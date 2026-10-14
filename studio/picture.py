"""Specialist, drawing-led picture drafts. Never grants canonical approval.

The episode catalog is small; per-shot ledgers are created only when started.
Host handoffs expose actual references and skills, without pretending the CLI
can call a chat-only image generator. Existing final-release gates are separate.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path

from production.runtime import Ledger, identifier
from studio.paths import ROOT, load_json, sha256, write_json

TIMELINE = 'production/runs/episode1-full-picture/tasks/episode-wiring/timeline.json'
EPISODE = 'projects/cemi_episode_01/data/episode.json'
SCRIPT = 'projects/cemi_episode_01/data/EPISODE_SCRIPT.md'
ART = 'production/runs/episode1-anime90s-scenes/shot-index.json'
TEMPLATE = 'production/pipeline_templates/complete_shot.json'
CATALOG = 'production/picture-drafts/catalog.json'
AUDIO = {'sound-plan', 'voice', 'dialogue-edit', 'sfx', 'music', 'mix'}
RENAMES = {'final-manifest': 'draft-manifest', 'qa': 'draft-review'}


class PictureError(ValueError):
    pass


def path(root, relative):
    root = Path(root).resolve()
    p = Path(relative)
    if p.is_absolute() or '..' in p.parts:
        raise PictureError('Use repository-relative paths')
    dest = root / p
    if dest.resolve() != dest or not dest.is_relative_to(root):
        raise PictureError('Symlinked or escaping paths are not allowed')
    return dest


def profile(template):
    """Reuse specialist contracts; omit audio only in this explicit draft path."""
    stages = []
    for original in template['stages']:
        if original['id'] in AUDIO:
            continue
        s = deepcopy(original)
        s['id'] = RENAMES.get(s['id'], s['id'])
        s['depends_on'] = [RENAMES.get(d, d) for d in s['depends_on'] if d not in AUDIO]
        # This profile cannot release a final episode. Technical approval here
        # concerns provisional picture only, including unchanged script timing.
        for key in ('requires_author_approval', 'author_approver', 'gate_after'):
            s.pop(key, None)
        if s['id'] == 'script-timing':
            s['artifact_kinds'][0] = 'draft timing record'
            s['acceptance'][0] = 'Use the current scripted frame count and latest author-directed rate; do not invent a new timing approval'
        if s['id'] == 'asset-register':
            s['acceptance'][1] = 'Provisional draft references are labeled; rejected outputs are diagnostic evidence only, never accepted animation inputs'
        if s['id'] == 'character-design':
            s['evidence_kinds'][0] = 'current-reference comparison'
            s['acceptance'][0] = 'Match current character references and report their exact approval state and any unresolved likeness'
        if s['id'] == 'edit':
            s['evidence_kinds'] = ['duration and order check', 'silent picture stream check']
            s['acceptance'][1] = 'Picture is silent; deferred sound and incomplete lip sync are explicitly recorded'
        if s['id'] == 'draft-manifest':
            s['acceptance'] = ['Every draft source and output has an exact hash and original review state; no canonical promotion']
        if s['id'] == 'draft-review':
            s['acceptance'] = [a.replace('color, sound and', 'color and') for a in s['acceptance']]
            s['acceptance'].append('Report picture-only coverage and deferred sound; technical draft approval is not release approval')
        stages.append(s)
    return stages


def verify_catalog(root, catalog):
    for source, digest in catalog['source_hashes'].items():
        if sha256(path(root, source)) != digest:
            raise PictureError(f'Source changed; inspect and explicitly refresh catalog: {source}')
    for row in catalog['shots']:
        if sha256(path(root, row['artwork']['path'])) != row['artwork']['sha256']:
            raise PictureError(f"Artwork changed: {row['shot']}")


def verify_packet(root, packet):
    """Check this shot's actual sources, independent of other shots' progress."""
    row = packet['shot']
    episode = {s['id']: s for s in load_json(path(root, EPISODE))['shots']}
    current = episode.get(row['shot'])
    if current is None or any(current[k] != row[k] for k in ('frames', 'start_frame', 'script')):
        raise PictureError(f"Shot script or timing changed: {row['shot']}")
    art = {s['shot']: s for s in load_json(path(root, ART))['shots']}
    if art.get(row['shot']) != row['artwork']:
        raise PictureError(f"Artwork record changed: {row['shot']}")
    if sha256(path(root, row['artwork']['path'])) != row['artwork']['sha256']:
        raise PictureError(f"Artwork changed: {row['shot']}")
    timeline = {s['shot']: s for s in load_json(path(root, TIMELINE))['shots']}
    if timeline[row['shot']]['action_contract'] != row['action_contract']:
        raise PictureError(f"Shot action contract changed: {row['shot']}")
    for source, digest in {**packet.get('reference_hashes', {}), **packet['repair_reports']}.items():
        if sha256(path(root, source)) != digest:
            raise PictureError(f'Reference changed: {source}')


def plan(root=ROOT, *, refresh=False):
    destination = path(root, CATALOG)
    if destination.exists() and not refresh:
        data = load_json(destination)
        verify_catalog(root, data)
        return data
    episode = load_json(path(root, EPISODE))['shots']
    timeline = load_json(path(root, TIMELINE))
    art = {s['shot']: s for s in load_json(path(root, ART))['shots']}
    rows = {s['shot']: s for s in timeline['shots']}
    if len(episode) != 128 or len(rows) != 128 or len(art) != 128:
        raise PictureError('Expected all 128 episode shots and artwork records')
    records, cursor = [], 0
    for s in episode:
        row = rows[s['id']]
        if s['start_frame'] != cursor or row['frames'] != s['frames'] or row['start_frame'] != cursor:
            raise PictureError(f"Timing mismatch: {s['id']}")
        cursor += s['frames']
        if s['end_frame'] != cursor or row['end_frame_exclusive'] != cursor:
            raise PictureError('Noncontiguous frame bounds')
        records.append({'shot': s['id'], 'frames': s['frames'], 'start_frame': s['start_frame'],
                        'script': s['script'], 'artwork': art[s['id']],
                        'action_contract': row['action_contract'],
                        'existing_motion_status': row['status'], 'existing_draft': row['draft']})
    if cursor != 27120 or timeline['fps'] != 24:
        raise PictureError('Episode must retain 27120 frames at 24 fps')
    data = {'schema': 'cemi.picture-drafts.v1', 'mode': 'picture-draft',
            'sound': 'deferred', 'canonical_delivery_allowed': False,
            'source_hashes': {p: sha256(path(root, p)) for p in (EPISODE, SCRIPT, ART, TIMELINE, TEMPLATE, 'production/roles.json')},
            'stages': profile(load_json(path(root, TEMPLATE))), 'shots': records}
    verify_catalog(root, data)
    write_json(destination, data)
    return data


def start(shot, *, root=ROOT, revision=1, repairs=()):
    catalog = plan(root)
    matches = [s for s in catalog['shots'] if s['shot'] == shot]
    if len(matches) != 1 or type(revision) is not int or revision < 1:
        raise PictureError('Use a known shot and positive explicit revision')
    row = matches[0]
    run = identifier(f'picture-draft-{shot.lower()}-v{revision}')
    ledger = Ledger(root, run)
    packet_path = f'production/runs/{run}/picture-packet.json'
    repair_hashes = {p: sha256(path(root, p)) for p in repairs}
    packet = {'mode': 'picture-draft', 'shot': row, 'fps': 24, 'aspect': '16:9',
              'sound': 'deferred', 'canonical_delivery_allowed': False,
              'repair_reports': repair_hashes, 'catalog_sha256': sha256(path(root, CATALOG)),
              'source_hashes': catalog['source_hashes'],
              'image_execution': 'Host image tool through one explicit image-demand subtask when necessary; never an unattended CLI promise',
              'references_are': 'Provisional draft references; no technical or author approval inferred'}
    if not path(root, packet_path).exists():
        packet['reference_hashes'] = {p: sha256(path(root, p)) for p in ('production/art_direction.json', 'production/roles.json', TEMPLATE)}
    if path(root, packet_path).exists():
        old = load_json(path(root, packet_path))
        verify_packet(root, old)
        if old['repair_reports'] != repair_hashes:
            raise PictureError('Existing shot packet differs; inspect it and use an explicit new revision')
        packet = old
        ledger.validate()
        if ledger.data['paused']:
            return ledger
    elif ledger.path.exists():
        raise PictureError('Run exists without a matching picture packet; inspect before starting')
    stages = catalog['stages']
    roles_raw = load_json(path(root, 'production/roles.json'))
    roles = roles_raw.get('roles', roles_raw)
    if isinstance(roles, list):
        roles = {r['id']: r for r in roles}
    for stage in stages:
        role = roles[stage['role']]
        if role['reviewer'] != stage['reviewer'] or not path(root, role['skill']).is_file():
            raise PictureError(f"Missing skill or reviewer mismatch: {stage['id']}")
    # The current script overrides a superseded action sentence in old contracts.
    departments = row['action_contract']['departments']
    action = {'character': [departments['character']['action']],
              'prop': [departments['props']['action']],
              'environment': [departments['environment_fx']['action']],
              'effects': [departments['environment_fx']['script_fx']],
              'camera': [departments['camera']['script_mode']]}
    write_json(path(root, packet_path), packet)
    ledger.initialize()
    for stage in stages:
        sid = stage['id']
        upstream = [f'production/runs/{run}/tasks/{d}' for d in stage['depends_on']]
        objective = (f"PICTURE DRAFT ONLY. Complete {sid} for {shot}, exactly {row['frames']} frames at 24fps,16:9. "
                     f"Read {packet_path}: current script, actual reference image, action phases, contact locks and prior failures. "
                     "Keep exact timing and latest author corrections; propose any story changes separately. "
                     "Use the assigned specialist skill and its designated reviewer. Produce every contracted artifact/evidence kind. "
                     "Draft references are provisional; preserve their review status. Separate missing input drawings from completed work. "
                     "No pose atlas counts as registered motion. No warped paintings, repeated stills or camera-only substitutes. "
                     "Request individual controlled key/breakdown drawings when broad pose sheets fail. "
                     "Use Craft for editable assets/composition/timeline and Blender for rigid prop/perspective work where appropriate. "
                     "Do not generate an entire shot in a layout or design stage. No paid tools, canonical promotion or Git uploads. "
                     "Sound is deferred; final episode approval is outside this draft workflow. "
                     "Explicit image needs must be handed to a host image-demand turn with actual references; report missing capability honestly.")
        task = {'id': sid, 'role': stage['role'], 'shots': [shot], 'objective': objective,
                'inputs': [packet_path, EPISODE, SCRIPT, row['artwork']['path'], 'production/art_direction.json'] + list(repairs) + upstream,
                'output_dir': f'production/runs/{run}/tasks/{sid}', 'depends_on': stage['depends_on'],
                'acceptance_criteria': stage['acceptance'], 'require_host_bindings': True,
                'requires_author_approval': False, 'full_scene_action': action,
                'budget': {'max_cost_usd': 0},
                'completion_contract': {'required_artifact_kinds': stage['artifact_kinds'],
                                        'required_evidence_kinds': stage['evidence_kinds'],
                                        'independent_review_required': True,
                                        'technical_gate': bool(stage.get('technical_gate')), 'author_gate': None}}
        if stage.get('art_direction_mode'):
            task['art_direction_mode'] = stage['art_direction_mode']
        if sid in ledger.data['tasks']:
            existing = ledger._task(sid)
            if any(existing.get(k) != v for k, v in task.items()):
                raise PictureError(f'Existing task contract changed: {sid}')
        else:
            ledger.add(task)
    return ledger


def status(root=ROOT):
    catalog = plan(root)
    runs = []
    for p in sorted(path(root, 'production/runs').glob('picture-draft-*/picture-packet.json')):
        ledger = Ledger(root, p.parent.name)
        runs.append({'run': ledger.run, 'paused': ledger.data['paused'],
                     'ready': [{'task': t, 'role': ledger._task(t)['role']} for t in ledger.ready()],
                     'states': {k: t['state'] for k, t in ledger.data['tasks'].items()}})
    return {'mode': 'picture-draft', 'shots': len(catalog['shots']), 'stages_per_shot': len(catalog['stages']),
            'canonical_delivery_allowed': False, 'runs': runs,
            'existing_motion_counts': {s: sum(r['existing_motion_status'] == s for r in catalog['shots'])
                                       for s in sorted({r['existing_motion_status'] for r in catalog['shots']})}}


def handoff(run, task_id, *, root=ROOT, recover=False):
    """Reserve one real host worker; never launch or retry image generation."""
    from studio.runner import CodexRunner
    packet = load_json(path(root, f'production/runs/{identifier(run)}/picture-packet.json'))
    verify_packet(root, packet)
    ledger = Ledger(root, run)
    ledger._active()
    task = ledger._task(task_id)
    destination = path(root, f'production/runs/{run}/handoff-jobs/{task_id}.json')
    if task['state'] == 'running':
        if not recover or not destination.exists():
            raise PictureError('Task already reserved; inspect host/output state and use --recover only for an unlaunched handoff')
        job = load_json(destination)
        bindings = ledger._load_handoffs()['bindings']
        if task_id in bindings or any(path(root, task['output_dir']).iterdir()):
            raise PictureError('Task has a host binding or output; collect existing work, never launch a duplicate')
        if job['state'] != 'prepared':
            raise PictureError('Handoff was already delivered; do not launch it again')
        job['state'] = 'awaiting-real-host-worker'
        write_json(destination, job)
        return job
    if task_id not in ledger.ready():
        raise PictureError('Task is not ready')
    runner = CodexRunner(run, root=root)
    role = ledger.roles[task['role']]
    envelope = dict(task)
    envelope['inputs'] = [ledger._current_input(p) for p in task['inputs']]
    text = ('Read AGENTS.md, production/WORKER_CONTRACT.md and ' + role['skill'] + '.\n'
            'Bounded assignment:\n' + json.dumps(envelope, indent=2) + '\n'
            'Return host_agent_id and completion: {artifacts: [{path,kind}], evidence: [{kind,detail}]} '
            'covering every required completion_contract kind. List these paths in artifacts too. '
            'Write only inside output_dir; no self-approval, ledger edits or delegation.')
    job = {'run': run, 'task': task_id, 'role': task['role'], 'skill': role['skill'],
           'reviewer_role': role['reviewer'], 'reviewer_skill': ledger.roles[role['reviewer']]['skill'],
           'reference_images': [packet['shot']['artwork']['path']],
           'prompt': runner.worker_prompt(task, text), 'state': 'prepared',
           'instructions': 'Spawn a separate real worker; bind its returned ID with host_handoff.py. Worker must view reference_images. Submit result through runtime.py; spawn and bind a distinct reviewer. Do not fabricate IDs or approvals.'}
    # Durable preparation precedes reservation. Recovery never repeats a launch.
    write_json(destination, job)
    ledger.dispatch(task_id, 'host-' + task_id)
    job['state'] = 'awaiting-real-host-worker'
    write_json(destination, job)
    return job


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    q = sub.add_parser('plan'); q.add_argument('--refresh', action='store_true')
    q = sub.add_parser('start'); q.add_argument('shot'); q.add_argument('--revision', type=int, default=1)
    q.add_argument('--repair', action='append', default=[])
    sub.add_parser('status')
    q = sub.add_parser('handoff'); q.add_argument('--run', required=True); q.add_argument('--task', required=True)
    q.add_argument('--recover', action='store_true')
    a = p.parse_args(argv)
    try:
        if a.command == 'plan':
            d = plan(refresh=a.refresh); result = {'catalog': CATALOG, 'shots': len(d['shots']), 'stages_per_shot': len(d['stages']), 'mode': d['mode']}
        elif a.command == 'start':
            ledger = start(a.shot, revision=a.revision, repairs=a.repair)
            result = {'run': ledger.run, 'tasks': len(ledger.data['tasks']), 'ready': ledger.ready(), 'paused': ledger.data['paused']}
        elif a.command == 'status':
            result = status()
        else:
            result = handoff(a.run, a.task, recover=a.recover)
        print(json.dumps(result, indent=2))
    except (ValueError, OSError, KeyError) as exc:
        raise SystemExit(f'picture: {exc}')


if __name__ == '__main__':
    main()
