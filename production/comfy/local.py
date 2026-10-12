"""Local ComfyUI adapter. No cloud client, credentials, retries or paid nodes.

Run with python -m production.comfy.local. One coordinator owns the registry.
Generated images remain exploratory; this adapter never approves artwork.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import uuid
from production.asset_registry import AssetRegistry, AssetRegistryError

ALLOWED = {
    'CheckpointLoaderSimple', 'LoraLoader', 'CLIPTextEncode', 'LoadImage',
    'VAEEncode', 'VAEDecode', 'KSampler', 'SaveImage', 'EmptyLatentImage',
    'ControlNetLoader', 'ControlNetApplyAdvanced',
}

class ComfyError(ValueError):
    pass

class ConnectionPaused(ComfyError):
    pass


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False).encode()


def safe_path(root, relative):
    if not isinstance(relative, str) or not relative or '\\' in relative:
        raise ComfyError('Expected a repository-relative path')
    p = Path(relative)
    if p.is_absolute() or any(x.startswith('.') for x in p.parts):
        raise ComfyError('Absolute, hidden and traversal paths are not allowed')
    raw = root / p
    resolved = raw.resolve()
    if not resolved.is_relative_to(root) or resolved != raw:
        raise ComfyError('Path escapes repository or contains a symlink')
    return raw


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix='.comfy-')
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(json.dumps(data, indent=2, ensure_ascii=False).encode() + b'\n')
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ComfyError('Redirect refused; use the local ComfyUI endpoint directly')


class Client:
    def __init__(self, url='http://127.0.0.1:8188'):
        u = urllib.parse.urlsplit(url)
        if (u.scheme != 'http' or u.hostname not in {'127.0.0.1', '::1'}
                or u.username or u.password or u.path not in {'', '/'}
                or u.query or u.fragment):
            raise ComfyError('Only numeric loopback HTTP is allowed; tunnel your own GPU to localhost')
        self.url = url.rstrip('/')
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())

    def request(self, route, data=None, content_type='application/json', binary=False):
        req = urllib.request.Request(self.url + route, data=data,
                                     headers={'Content-Type': content_type})
        try:
            with self.opener.open(req, timeout=30) as response:
                raw = response.read()
        except urllib.error.HTTPError as exc:
            raise ComfyError(f'ComfyUI HTTP {exc.code}: {exc.read(4096).decode(errors="replace")}') from exc
        except (OSError, urllib.error.URLError) as exc:
            raise ConnectionPaused('Connection interrupted; paused, no retry. Inspect job then obtain approval to resume.') from exc
        if binary:
            return raw
        try:
            return json.loads(raw)
        except (ValueError, UnicodeError) as exc:
            raise ComfyError('ComfyUI returned invalid JSON; inspect job before any resubmission') from exc

    def upload(self, raw, name):
        boundary = 'ilan' + uuid.uuid4().hex
        body = (f'--{boundary}\r\nContent-Disposition: form-data; name="image"; filename="{name}"\r\n'
                'Content-Type: image/png\r\n\r\n').encode() + raw
        body += (f'\r\n--{boundary}\r\nContent-Disposition: form-data; name="type"\r\n\r\ninput'
                 f'\r\n--{boundary}--\r\n').encode()
        result = self.request('/upload/image', body, 'multipart/form-data; boundary=' + boundary)
        sub = result.get('subfolder', '')
        return (sub + '/' if sub else '') + result['name']


def graph(spec, image_name, control_name=None):
    def n(kind, **inputs):
        return {'class_type': kind, 'inputs': inputs}
    g = {'1': n('CheckpointLoaderSimple', ckpt_name=spec['checkpoint'])}
    model, clip = ['1', 0], ['1', 1]
    if spec.get('lora'):
        g['2'] = n('LoraLoader', model=model, clip=clip, lora_name=spec['lora'],
                   strength_model=spec.get('lora_strength', 0.7), strength_clip=spec.get('lora_strength', 0.7))
        model, clip = ['2', 0], ['2', 1]
    g['3'] = n('CLIPTextEncode', text=spec['positive'], clip=clip)
    g['4'] = n('CLIPTextEncode', text=spec['negative'], clip=clip)
    g['5'] = n('LoadImage', image=image_name)
    g['6'] = n('VAEEncode', pixels=['5', 0], vae=['1', 2])
    positive, negative = ['3', 0], ['4', 0]
    if spec.get('controlnet'):
        g['10'] = n('ControlNetLoader', control_net_name=spec['controlnet'])
        g['11'] = n('LoadImage', image=control_name)
        g['12'] = n('ControlNetApplyAdvanced', positive=positive, negative=negative,
                    control_net=['10', 0], image=['11', 0], strength=spec.get('control_strength', 0.8),
                    start_percent=0.0, end_percent=1.0, vae=['1', 2])
        positive, negative = ['12', 0], ['12', 1]
    g['7'] = n('KSampler', model=model, positive=positive, negative=negative,
               latent_image=['6', 0], seed=spec['seed'], steps=spec.get('steps', 24),
               cfg=spec.get('cfg', 5.0), sampler_name='euler', scheduler='normal',
               denoise=spec.get('denoise', 0.3))
    g['8'] = n('VAEDecode', samples=['7', 0], vae=['1', 2])
    g['9'] = n('SaveImage', images=['8', 0], filename_prefix='ilan/' + spec['job_id'])
    return g


def preflight(workflow, info):
    for node in workflow.values():
        kind = node['class_type']
        if kind not in ALLOWED:
            raise ComfyError(f'Node not allowed in local-only profile: {kind}')
        if kind not in info:
            raise ComfyError(f'Missing local node: {kind}')
        definition = info[kind]
        if definition.get('api_node') or str(definition.get('python_module', '')).startswith('comfy_api_nodes'):
            raise ComfyError(f'Paid/API node refused: {kind}')
        required = definition.get('input', {}).get('required', {})
        for key, options in required.items():
            if key not in node['inputs']:
                raise ComfyError(f'Missing required input: {kind}.{key}')
            value = node['inputs'][key]
            if isinstance(options[0], list) and not isinstance(value, list) and value not in options[0]:
                raise ComfyError(f'Unavailable model or option: {kind}.{key}={value}')


def prepare(repo, spec, job_path):
    if job_path.exists():
        raise ComfyError('Job already exists; use a new job ID for a new drawing')
    if not re.fullmatch(r'[a-z0-9][a-z0-9._-]{0,59}', spec.get('job_id', '')):
        raise ComfyError('Invalid job_id')
    contract = repo / 'production/art_direction.json'
    art = json.loads(contract.read_text())
    if spec.get('art_mode') not in art['modes']:
        raise ComfyError('Declare a mode from production/art_direction.json')
    if type(spec.get('seed')) is not int or not 0 <= spec['seed'] < 2**64:
        raise ComfyError('seed must be an unsigned 64-bit integer')
    if not 0 < spec.get('denoise', 0.3) <= 1:
        raise ComfyError('denoise must be greater than zero and at most one')
    for field in ('positive', 'negative', 'checkpoint', 'license'):
        if not isinstance(spec.get(field), str) or not spec[field].strip():
            raise ComfyError(f'Missing {field}')
    # Use registry validation for continuity shape before any compute.
    from production.asset_registry import _continuity
    _continuity(spec.get('continuity'))
    if not spec.get('shots'):
        raise ComfyError('At least one existing shot ID is required')
    for shot in spec['shots']:
        if not re.fullmatch(r'S\d{2}-\d{2}', shot):
            raise ComfyError('Invalid shot ID')
        if not (repo / f'projects/cemi_episode_01/data/shots/{shot}.json').is_file():
            raise ComfyError(f'Unknown shot: {shot}')
    registry = AssetRegistry(repo)
    state = registry.verify(check_files=True)
    sources = []
    inputs = {}
    if bool(spec.get('controlnet')) != bool(spec.get('control_image')):
        raise ComfyError('ControlNet requires both model and preprocessed control_image')
    for field in ('reference', 'control_image'):
        if field not in spec:
            if field == 'reference':
                raise ComfyError('An image reference is required')
            continue
        source = spec[field]
        ref = (source['asset_id'], source['version'])
        record = state['assets'].get(ref)
        if not record or state['states'][ref] != 'canonical':
            raise ComfyError(f'{field} must reference a canonical author-approved registry version')
        path = safe_path(repo, record['path'])
        if path.suffix.lower() != '.png' or not path.read_bytes().startswith(b'\x89PNG\r\n\x1a\n'):
            raise ComfyError('Reference/control images must be PNG files')
        inputs[field] = {'path': record['path'], 'sha256': record['sha256']}
        sources.append(source)
    job = {'schema_version': 1, 'state': 'prepared', 'spec': spec, 'inputs': inputs,
           'source_assets': sources, 'art_contract_sha256': digest(contract.read_bytes()),
           'canonical_art_sha256': digest((repo / art['canonical_document']).read_bytes()),
           'spec_sha256': digest(encoded(spec)), 'prompt_id': None, 'outputs': []}
    save(job_path, job)
    return job


def validate_job(repo, job):
    if digest(encoded(job['spec'])) != job['spec_sha256']:
        raise ComfyError('Job specification changed after preparation')
    art_path = repo / 'production/art_direction.json'
    art = json.loads(art_path.read_text())
    if (digest(art_path.read_bytes()) != job['art_contract_sha256'] or
            digest((repo / art['canonical_document']).read_bytes()) != job['canonical_art_sha256']):
        raise ComfyError('Art contract changed; prepare a fresh job')
    state = AssetRegistry(repo).verify(check_files=True)
    for field, item in job['inputs'].items():
        source = job['spec'][field]
        ref = (source['asset_id'], source['version'])
        record = state['assets'].get(ref)
        if (not record or state['states'].get(ref) != 'canonical' or
                record['path'] != item['path'] or record['sha256'] != item['sha256']):
            raise ComfyError('Upstream reference changed or is no longer canonical')


def submit(repo, job_path, client):
    job = json.loads(job_path.read_text())
    if job['state'] != 'prepared':
        raise ComfyError('Only a prepared job may submit; never automatically resubmit an uncertain request')
    validate_job(repo, job)
    job['endpoint'] = client.url
    try:
        info = client.request('/object_info')
        # Check models and allowed nodes before uploading anything.
        draft = graph(job['spec'], 'reference.png', 'control.png')
        for node in draft.values():
            if node['class_type'] == 'LoadImage':
                continue
            preflight({'node': node}, info)
        names = {}
        job['state'] = 'uploading'
        save(job_path, job)
        for field, item in job['inputs'].items():
            raw = safe_path(repo, item['path']).read_bytes()
            if digest(raw) != item['sha256']:
                raise ComfyError('Input bytes changed')
            names[field] = client.upload(raw, item['sha256'] + '.png')
        workflow = graph(job['spec'], names['reference'], names.get('control_image'))
        preflight(workflow, client.request('/object_info'))
        job['workflow'] = workflow
        job['workflow_sha256'] = digest(encoded(workflow))
        job['state'] = 'submitting'
        save(job_path, job)  # Durable intent BEFORE the non-idempotent POST.
        response = client.request('/prompt', encoded({'prompt': workflow,
            'client_id': job['spec']['job_id'], 'extra_data': {'ilan_job_id': job['spec']['job_id'],
            'ilan_workflow_sha256': job['workflow_sha256']}}))
        if response.get('error') or response.get('node_errors') or not response.get('prompt_id'):
            raise ComfyError('ComfyUI rejected workflow: ' + json.dumps(response))
        job['prompt_id'] = response['prompt_id']
        job['state'] = 'queued'
    except (ComfyError, KeyError, TypeError) as exc:
        job['paused_from'] = job['state']
        job['state'] = 'paused'
        job['reason'] = str(exc)
        save(job_path, job)
        raise
    save(job_path, job)
    return job


def reconcile(job, client):
    """Read-only reconciliation after explicit resume; never POST /prompt here."""
    if job.get('prompt_id'):
        return
    queue = client.request('/queue')
    history = client.request('/history')
    records = list(queue.get('queue_running', [])) + list(queue.get('queue_pending', []))
    records += [entry['prompt'] for entry in history.values() if 'prompt' in entry]
    matches = {p[1] for p in records if len(p) > 3 and isinstance(p[3], dict)
               and p[3].get('ilan_job_id') == job['spec']['job_id']
               and p[3].get('ilan_workflow_sha256') == job.get('workflow_sha256')}
    if len(matches) != 1:
        raise ComfyError('Cannot identify exactly one prior prompt. Inspect ComfyUI queue/history; no automatic resubmission.')
    job['prompt_id'] = matches.pop()


def collect(repo, job, client):
    history = client.request('/history/' + urllib.parse.quote(job['prompt_id'], safe=''))
    entry = history.get(job['prompt_id'])
    if not entry:
        # Missing history is not success and may mean eviction/restart.
        queue = client.request('/queue')
        ids = {p[1] for p in queue.get('queue_running', []) + queue.get('queue_pending', [])}
        if job['prompt_id'] not in ids:
            raise ComfyError('Prompt absent from queue and history; inspect server before resuming')
        return
    status = entry.get('status', {})
    if status.get('status_str') == 'error':
        job['state'] = 'failed'
        job['reason'] = json.dumps(status.get('messages', []))
        return
    if not status.get('completed'):
        return
    descriptors = [i for out in entry.get('outputs', {}).values() for i in out.get('images', [])
                   if i.get('type') == 'output']
    if not descriptors:
        raise ComfyError('Completed prompt has no saved output images')
    registry = AssetRegistry(repo)
    for index, item in enumerate(descriptors):
        if not str(item.get('filename', '')).lower().endswith('.png'):
            raise ComfyError('Local image profile expects PNG outputs')
        query = urllib.parse.urlencode({k: item.get(k, '') for k in ('filename', 'subfolder', 'type')})
        raw = client.request('/view?' + query, binary=True)
        if not raw.startswith(b'\x89PNG\r\n\x1a\n'):
            raise ComfyError('Server returned non-PNG bytes')
        asset_id = f"{job['spec']['job_id']}.{index:03d}"
        relative = f'production/comfy-runs/{job["spec"]["job_id"]}/outputs/{index:03d}.png'
        target = safe_path(repo, relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and digest(target.read_bytes()) != digest(raw):
            raise ComfyError('Output changed; refusing to overwrite an existing drawing')
        if not target.exists():
            with target.open('xb') as f:
                f.write(raw)
        existing = [a for a in registry.summary()['assets'] if a['asset_id'] == asset_id]
        if existing:
            record = existing[-1]
            if record['sha256'] != digest(raw) or record['path'] != relative:
                raise ComfyError('Registry output conflict')
        else:
            record = registry.register(asset_id=asset_id, path=relative,
                kind='generated-drawing', mode='work-in-progress', shots=job['spec']['shots'],
                provenance={'origin': 'local-comfyui', 'creator': 'comfy-local',
                    'license': job['spec']['license'], 'source_assets': job['source_assets'],
                    'notes': f"Prompt {job['prompt_id']}; workflow SHA256 {job['workflow_sha256']}; seed {job['spec']['seed']}; art mode {job['spec']['art_mode']}. Technical and author review required."},
                continuity=job['spec']['continuity'])
        output = {'asset_id': asset_id, 'version': record['version'], 'path': relative, 'sha256': digest(raw)}
        if output not in job['outputs']:
            job['outputs'].append(output)
    job['state'] = 'awaiting-review'


def poll(repo, job_path, client, approval=None):
    job = json.loads(job_path.read_text())
    if job.get('endpoint') != client.url:
        raise ComfyError('Endpoint differs from original job; provider switching is disabled')
    if job['state'] == 'awaiting-review':
        return job
    if job['state'] in {'paused', 'submitting', 'uploading'}:
        expected = 'APPROVE RESUME ' + job['spec']['job_id']
        if approval != expected:
            raise ComfyError('Paused/uncertain job requires user approval: ' + expected)
        job.setdefault('resume_records', []).append(approval)
    elif job['state'] != 'queued':
        raise ComfyError('Job is not queued or resumable')
    try:
        reconcile(job, client)
        job['state'] = 'queued'
        collect(repo, job, client)
    except (ComfyError, OSError, KeyError, TypeError, AssetRegistryError) as exc:
        job['state'] = 'paused'
        job['reason'] = str(exc)
        save(job_path, job)
        raise
    save(job_path, job)
    return job


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo', default='.')
    p.add_argument('--url', default='http://127.0.0.1:8188')
    s = p.add_subparsers(dest='command', required=True)
    s.add_parser('doctor')
    a = s.add_parser('prepare'); a.add_argument('spec')
    for cmd in ('submit', 'poll', 'resume'):
        a = s.add_parser(cmd); a.add_argument('job_id')
        if cmd == 'resume': a.add_argument('--approval', required=True)
    args = p.parse_args()
    repo = Path(args.repo).resolve()
    try:
        if args.command == 'doctor':
            client = Client(args.url)
            result = {'endpoint': client.url, 'system': client.request('/system_stats'),
                      'checkpoint_models': client.request('/models/checkpoints'),
                      'billing': 'local-only; no Comfy credits', 'generation_tested': False}
        else:
            spec = json.loads(Path(args.spec).read_text()) if args.command == 'prepare' else None
            job_id = spec['job_id'] if spec else args.job_id
            if not re.fullmatch(r'[a-z0-9][a-z0-9._-]{0,59}', job_id):
                raise ComfyError('Invalid job ID')
            path = safe_path(repo, f'production/comfy-runs/{job_id}/job.json')
            # Exclusive per-job lock; stale locks require manual inspection after a crash.
            path.parent.mkdir(parents=True, exist_ok=True)
            lock = path.parent / 'operation.lock'
            try:
                fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            except FileExistsError as exc:
                raise ComfyError('Job is locked; inspect active process before removing stale operation.lock') from exc
            os.close(fd)
            try:
                if args.command == 'prepare': result = prepare(repo, spec, path)
                elif args.command == 'submit': result = submit(repo, path, Client(args.url))
                else: result = poll(repo, path, Client(args.url), getattr(args, 'approval', None))
            finally:
                lock.unlink()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except (ComfyError, AssetRegistryError, OSError, KeyError, TypeError) as exc:
        p.exit(2, str(exc) + '\n')

if __name__ == '__main__':
    main()
