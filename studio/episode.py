"""Persistent, sequential episode draft production. Never fabricates final approval.

Remote calls use the existing anonymous-only video bridge. Missing images,
long-shot choreography, failed calls and completed motion candidates stop the
queue at explicit handoffs; no retries, still-image filler or paid fallback.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import json
from pathlib import Path
import shutil
import os
import subprocess

from studio import video
from studio.paths import EPISODE, PROJECT, ROOT, load_json, sha256, write_json


class EpisodeError(RuntimeError):
    pass


def now():
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def lock(directory):
    with (directory / 'coordinator.lock').open('a') as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise EpisodeError('Another episode coordinator is active') from exc
        yield


def initialize(directory):
    directory = Path(directory).resolve()
    if (directory / 'episode.json').exists():
        return summary(directory)
    directory.mkdir(parents=True, exist_ok=False)
    episode = load_json(EPISODE)
    rows = []
    for shot in episode['shots']:
        references = [PROJECT / p for p in shot.get('keyframes', [])]
        # A saved opening candidate already exists outside episode.keyframes.
        if shot['id'] == 'S01-01':
            references.insert(0, PROJECT / 'assets/keyframes/S01-01-candidate-v1.png')
        source = next((p for p in references if p.is_file()), None)
        row = {'shot': shot['id'], 'frames': shot['frames'], 'start_frame': shot['start_frame'],
               'state': 'pending', 'script': shot['script'], 'source': str(source) if source else None,
               'source_sha256': sha256(source) if source else None}
        editorial = {
            'S00-01': ROOT / 'production/episode-first-pass/opening/S00-01.mp4',
            'S00-02': ROOT / 'production/episode-first-pass/opening/S00-02.mp4',
            'S15-09': ROOT / 'production/episode-first-pass/ending/S15-09-review.mp4',
        }.get(shot['id'])
        if editorial and editorial.is_file():
            row.update(editorial=str(editorial), editorial_sha256=sha256(editorial))
        rows.append(row)
    data = {'version': 1, 'created_at': now(), 'state': 'ready', 'shots': rows,
            'episode_source_sha256': sha256(EPISODE), 'fps': 24,
            'expected_frames': sum(r['frames'] for r in rows), 'budget_ceiling_usd': 5,
            'paid_calls_enabled': False, 'reference_basis': 'current episode artwork, provisional draft basis',
            'truth': 'Draft production queue. No canonical assets or final author approvals are created.'}
    write_json(directory / 'episode.json', data)
    return summary(directory)


def summary(directory):
    data = load_json(Path(directory) / 'episode.json')
    counts = {}
    for row in data['shots']:
        counts[row['state']] = counts.get(row['state'], 0) + 1
    return {'state': data['state'], 'shots': len(data['shots']), 'counts': counts,
            'ready_frames': sum(r['frames'] for r in data['shots'] if r['state'] == 'draft_ready'),
            'expected_frames': data['expected_frames'], 'blocked_shot': data.get('blocked_shot'),
            'reason': data.get('reason'), 'paid_calls_enabled': False}


def _save(directory, data):
    data['updated_at'] = now()
    write_json(directory / 'episode.json', data)


def _stop(directory, data, row, state, reason):
    row['state'] = state
    data.update(state=state, blocked_shot=row['shot'], reason=reason)
    _save(directory, data)
    return summary(directory)


def _export(job, target):
    from studio.render import export_shot
    spec = load_json(job / 'imported/shot.json')
    # Preserve locally authored titles such as BEFORE as exact typography.
    baseline = load_json(PROJECT / 'data/shots' / f"{spec['id']}.json")
    for layer in baseline.get('layers', []):
        if layer.get('generator', {}).get('type') == 'text':
            spec['layers'].append(layer)
    write_json(job / 'draft-shot.json', spec)
    export_shot(spec, target, draft=True)


def run(directory, *, submit=video.submit, importer=video.import_clip, exporter=_export):
    """Work until a concrete image/motion-review handoff, not a blind full batch."""
    directory = Path(directory).resolve()
    with lock(directory):
        data = load_json(directory / 'episode.json')
        if data['state'] not in {'ready'}:
            raise EpisodeError(f"Queue is {data['state']}: {data.get('reason')}. Inspect outputs before resuming.")
        if sha256(EPISODE) != data['episode_source_sha256']:
            raise EpisodeError('Episode timing/script changed since queue creation')
        for row in data['shots']:
            if row['state'] == 'draft_ready':
                if sha256(row['output']) != row['output_sha256']:
                    raise EpisodeError(f"Completed output changed: {row['shot']}")
                continue
            if row['state'] != 'pending':
                return _stop(directory, data, row, 'paused', 'Interrupted in-flight step: inspect its existing files; never resubmit blindly.')
            if row.get('editorial'):
                from studio.engine.io import probe_frames
                if sha256(row['editorial']) != row['editorial_sha256'] or probe_frames(Path(row['editorial'])) != row['frames']:
                    return _stop(directory, data, row, 'paused', 'Editorial source changed or has wrong frame count')
                target = directory / 'shots' / f"{row['shot']}.mp4"
                target.parent.mkdir(exist_ok=True)
                if target.exists():
                    return _stop(directory, data, row, 'paused', 'Unrecorded editorial output exists; inspect before replacing')
                shutil.copyfile(row['editorial'], target)
                row.update(state='draft_ready', output=str(target), output_sha256=sha256(target), audio='existing editorial audio only')
                _save(directory, data)
                continue
            if not row['source']:
                # Hand off one shot at the point it needs art. Never batch missing images.
                from studio.demand import prepare, coordinator
                with coordinator(ROOT):
                    packet = prepare(ROOT, row['shot'])
                write_json(directory / 'image-request.json', packet)
                return _stop(directory, data, row, 'needs_image', 'One reference-attached image turn is required; see image-request.json. Host image tool is not an unattended HTTP API.')
            if sha256(row['source']) != row['source_sha256']:
                return _stop(directory, data, row, 'paused', 'Reference image changed since queue creation')
            if row['frames'] > video.MAX_FRAMES:
                return _stop(directory, data, row, 'needs_segment_plan', 'Shot exceeds 14 seconds; author motion/continuity boundaries instead of mechanically cutting action.')
            job = directory / 'jobs' / row['shot']
            target = directory / 'shots' / f"{row['shot']}.mp4"
            target.parent.mkdir(exist_ok=True)
            row.update(state='working', job=str(job))
            _save(directory, data)
            try:
                if job.exists() or target.exists():
                    raise EpisodeError('Pre-existing unrecorded output; inspect instead of overwriting or resubmitting')
                job.parent.mkdir(exist_ok=True)
                prompt_path = directory / f"{row['shot']}.prompt.txt"
                prompt = row['script'] + '\nKeep the supplied source designs, hair, costume, ages, props and palette. '
                prompt += 'Animate the complete stated duration, with deliberate acting and physical contacts. '
                prompt += 'Do not add or amplify supernatural glow; no fire around the children. '
                prompt += 'Keep paddle blade size fixed and its recovery inside the framing; restrained coherent motion. '
                prompt += 'No typography or watermarks; titles and exact scripted speech are handled separately.'
                prompt_path.write_text(prompt)
                video.prepare(row['shot'], row['source'], job, frames=row['frames'], prompt_file=prompt_path)
                submit(job)  # exactly one submission; bridge persists intent before sending
                importer(job)
                exporter(job, target)
                row.update(output=str(target), output_sha256=sha256(target), audio='final audio still required')
                return _stop(directory, data, row, 'awaiting_motion_review',
                             'A full-duration visual candidate is ready. Independent motion review must precede further generation; final author approval remains separate.')
            except BaseException as exc:
                _stop(directory, data, row, 'paused', f'{type(exc).__name__}: {str(exc)[:600]}')
                raise
        return assemble(directory, data)


def assemble(directory, data=None):
    """Refuse a fake complete episode: require every full-length draft shot."""
    directory = Path(directory).resolve()
    data = data or load_json(directory / 'episode.json')
    missing = [r['shot'] for r in data['shots'] if r['state'] != 'draft_ready']
    if missing:
        raise EpisodeError(f"Cannot assemble: {len(missing)} unfinished shots, beginning {missing[:3]}")
    from studio.engine.io import probe_frames
    from studio.render import assemble as concatenate
    for row in data['shots']:
        if sha256(row['output']) != row['output_sha256'] or probe_frames(Path(row['output'])) != row['frames']:
            raise EpisodeError(f"Output changed or wrong duration: {row['shot']}")
    result = concatenate([Path(r['output']) for r in data['shots']], directory / 'episode-picture-draft',
                         expected_frames=data['expected_frames'])
    data.update(state='picture_draft_complete', output=result,
                reason='Picture draft only. Sound, dialogue, independent quality and author review still required.')
    _save(directory, data)
    return summary(directory)


def _review(directory, row):
    """One real independent Codex reviewer, with image attachments and a saved result."""
    dest = directory / 'reviews' / row['shot']
    dest.mkdir(parents=True, exist_ok=False)
    schema = {'type':'object', 'additionalProperties':False,
              'required':['decision','evidence','repair_notes'],
              'properties':{'decision':{'type':'string','enum':['approve','reject','blocked']},
                            'evidence':{'type':'array','items':{'type':'string'}},
                            'repair_notes':{'type':'array','items':{'type':'string'}}}}
    write_json(dest/'schema.json',schema)
    prompt = ('You are the independent anime-quality-review reviewer for a generated episode DRAFT. '
              'Inspect the attached source and actual decoded video frames. Read AGENTS.md and '
              '.agents/skills/anime-quality-review/SKILL.md. Write only in '+str(dest)+'. '
              'No generation, changes to assets, paid calls, retries or author approvals. '
              'Current episode artwork is the provisional reference basis for this draft; '
              'historical character sheets must not silently replace it. '
              'Check faces, costumes, cast, grips, rigid prop geometry, water contacts, style, '
              'frame continuity and the scripted action. Inspect additional consecutive frames '
              'from '+row['job']+'/imported/frames wherever needed. '
              'State whether you inspected samples or continuous playback. Approve only a usable '
              'draft without observed material defects; reject with frame-specific repairs or return blocked. '
              'This decision is technical review only, not author approval or canonicalization. '
              'Shot: '+row['shot']+'\nScript:\n'+row['script'])
    frames = sorted((Path(row['job'])/'imported/frames').glob('*.png'))
    if len(frames) != row['frames']:
        raise EpisodeError('Missing decoded review frames')
    images = [Path(row['job'])/'first.png']
    images += [frames[i*(len(frames)-1)//5] for i in range(6)]
    cmd = ['codex','exec','--json','--sandbox','workspace-write','--output-schema',str(dest/'schema.json'),
           '-o',str(dest/'result.json')]
    for image in images:
        cmd += ['--image',str(image)]
    cmd += ['--',prompt]
    env = os.environ.copy()
    env['PATH'] = str(ROOT/'.venv/bin') + os.pathsep + env.get('PATH','')
    with (dest/'events.jsonl').open('w') as events, (dest/'stderr.log').open('w') as errors:
        result = subprocess.run(cmd,cwd=ROOT,env=env,stdin=subprocess.DEVNULL,stdout=events,
                                stderr=errors,text=True,timeout=900)
    if result.returncode:
        raise EpisodeError('Independent reviewer failed; inspect its saved logs, no automatic retry')
    thread = next((e.get('thread_id') for e in
                   (json.loads(line) for line in (dest/'events.jsonl').read_text().splitlines())
                   if e.get('type')=='thread.started'),None)
    if not thread:
        raise EpisodeError('Reviewer returned no real session ID')
    return {**load_json(dest/'result.json'),'reviewer_thread_id':thread,
            'output_sha256':row['output_sha256']}


def review(directory, *, reviewer=_review):
    directory = Path(directory).resolve()
    with lock(directory):
        data = load_json(directory/'episode.json')
        if data['state'] != 'awaiting_motion_review':
            raise EpisodeError('No completed motion candidate awaits review')
        row = next(r for r in data['shots'] if r['shot']==data['blocked_shot'])
        if sha256(row['output']) != row['output_sha256']:
            raise EpisodeError('Candidate changed before review')
        try:
            result = reviewer(directory,row)
            if (result.get('output_sha256')!=row['output_sha256'] or not result.get('reviewer_thread_id')
                    or not result.get('evidence') or result.get('decision') not in {'approve','reject','blocked'}):
                raise EpisodeError('Invalid independent review result')
            row['review'] = result
            if result['decision']!='approve':
                return _stop(directory,data,row,'needs_repair',
                             'Independent reviewer did not approve this draft: '+str(result.get('repair_notes',[])))
            row['state']='draft_ready'
            data.update(state='ready',blocked_shot=None,reason=None)
            _save(directory,data)
            return summary(directory)
        except BaseException as exc:
            _stop(directory,data,row,'paused',f'Review interrupted: {type(exc).__name__}: {str(exc)[:400]}')
            raise


def recover_clip(directory, clip):
    """Use a manually recovered result, never send another generation request."""
    directory=Path(directory).resolve()
    with lock(directory):
        data=load_json(directory/'episode.json')
        if data['state']!='paused':
            raise EpisodeError('Recovery applies only to a paused queue')
        row=next(r for r in data['shots'] if r['shot']==data['blocked_shot'])
        job=Path(row['job'])
        video.import_clip(job,clip)
        target=directory/'shots'/f"{row['shot']}.mp4"
        if target.exists():
            raise EpisodeError('Review file already exists; inspect instead of replacing')
        _export(job,target)
        row.update(output=str(target),output_sha256=sha256(target))
        return _stop(directory,data,row,'awaiting_motion_review','Recovered existing video; no generation call sent.')


def auto(directory):
    """Advance across approved draft shots; stop on every unresolved handoff."""
    while True:
        state=summary(directory)['state']
        if state=='ready':
            run(directory)
        elif state=='awaiting_motion_review':
            review(directory)
        else:
            return summary(directory)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['init', 'run', 'auto', 'review', 'recover-clip', 'status', 'assemble'])
    parser.add_argument('--out', default=str(ROOT / 'production/episode-automation-v1'))
    parser.add_argument('--clip', help='existing downloaded video for recover-clip; never a remote retry')
    args = parser.parse_args(argv)
    try:
        if args.action=='recover-clip':
            if not args.clip:
                parser.error('recover-clip requires --clip')
            result=recover_clip(args.out,args.clip)
        else:
            result = {'init': initialize, 'run': run, 'auto':auto, 'review':review,
                      'status': summary, 'assemble': assemble}[args.action](args.out)
        print(json.dumps(result, indent=2))
    except Exception as exc:
        raise SystemExit(f'episode stopped: {exc}') from exc


if __name__ == '__main__':
    main()
