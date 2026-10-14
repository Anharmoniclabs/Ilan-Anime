#!/usr/bin/env python3
"""Anime Motion: local shot direction, real I2V jobs, frame review and assembly."""
import argparse
import base64
import hashlib
import json
import mimetypes
import os
from pathlib import Path
import shutil
import subprocess
import threading
import time
import uuid
import zipfile
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, unquote
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
ROOT = HERE / 'workspace'
LOCK = threading.RLock()
ROUTE = 'https://queue.fal.run/fal-ai/wan/v2.2-a14b/image-to-video'
FIELDS = ('title', 'start', 'action', 'end', 'secondary', 'camera', 'continuity', 'seconds')
CHECKS = ('body_motion', 'identity', 'anatomy', 'continuity')

def save(path, data):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(data, indent=2))
    temp.replace(path)

def load():
    ROOT.mkdir(parents=True, exist_ok=True)
    path = ROOT / 'project.json'
    if not path.exists():
        save(path, dict(title='Untitled film', style='2D anime animation, clean ink lines, cel shading, strong key poses, intentional timing, consistent palette.',
                        characters='', world='', shots=[]))
    return json.loads(path.read_text())

def persist(p):
    save(ROOT / 'project.json', p)

def file_path(name):
    path = (ROOT / name).resolve()
    if not path.is_relative_to(ROOT.resolve()):
        raise ValueError('Invalid workspace path')
    return path

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def run(args, timeout=180):
    result = subprocess.run(args, capture_output=True, timeout=timeout)
    if result.returncode:
        raise ValueError(result.stderr.decode(errors='replace')[-1800:])
    return result.stdout

def probe(path):
    data = json.loads(run(['ffprobe', '-v', 'error', '-count_frames', '-show_streams', '-show_format', '-of', 'json', str(path)]))
    v = next((s for s in data['streams'] if s['codec_type'] == 'video'), None)
    if not v:
        raise ValueError('No video stream')
    seconds = float(data.get('format', {}).get('duration', v.get('duration', 0)))
    if not 0 < seconds <= 30:
        raise ValueError('Use a shot between 0 and 30 seconds')
    return dict(width=v['width'], height=v['height'], frames=int(v.get('nb_read_frames', 0)), fps=v['avg_frame_rate'], seconds=seconds)

def prompt(p, s):
    for field in ('start', 'action', 'end'):
        if not str(s.get(field, '')).strip():
            raise ValueError('Describe the starting pose, body action, and ending pose before rendering.')
    if not p['characters'].strip() or not p['world'].strip():
        raise ValueError('Fill in the shared character details and world/lighting first.')
    index = p['shots'].index(s)
    previous = p['shots'][index - 1]['end'] if index else 'Opening shot'
    return '\n'.join([
        p['style'], 'Character identity: ' + p['characters'], 'World and lighting: ' + p['world'],
        'Animate the supplied reference as one continuous shot. Preserve its design and proportions.',
        f"Opening 20% — anticipation: {s['start']}", f"Middle 60% — visible articulated body action: {s['action']}",
        f"Closing 20% — follow-through and end pose: {s['end']}",
        'Secondary motion: ' + s['secondary'], 'Camera: ' + s['camera'],
        'Previous shot ends: ' + previous, 'Continuity and screen direction: ' + s['continuity'],
        'Draw changing body poses with believable weight transfer, arcs and overlapping action. '
        'Keep the subject actively performing the action throughout. No internal cuts, slideshow, '
        'frozen character with camera-only motion, rubber limbs, face morphing, or style changes.'
    ])

def api(url, payload=None):
    u = urlparse(url)
    if u.scheme != 'https' or u.netloc != 'queue.fal.run':
        raise ValueError('Unexpected queue URL')
    key = os.environ.get('FAL_KEY')
    if not key:
        raise ValueError('Set FAL_KEY in the terminal before starting the studio. Image uploads and clip imports work without it.')
    req = Request(url, data=json.dumps(payload).encode() if payload is not None else None,
                  headers={'Authorization': 'Key ' + key, 'Content-Type': 'application/json'})
    with urlopen(req, timeout=55) as response:
        return json.load(response)

def take_dir(s):
    name = 'takes/' + s['id'] + '-' + uuid.uuid4().hex[:10]
    folder = file_path(name)
    folder.mkdir(parents=True)
    return name, folder

def upload(data, image=False):
    raw = base64.b64decode(data['data'], validate=True)
    if len(raw) > (8_000_000 if image else 90_000_000):
        raise ValueError('File too large (images 8 MB; video 90 MB).')
    if image:
        ext = '.png' if raw.startswith(b'\x89PNG\r\n\x1a\n') else '.jpg' if raw.startswith(b'\xff\xd8\xff') else None
        if not ext:
            raise ValueError('Use PNG or JPEG images.')
    else:
        ext = '.mp4'
    name = 'assets/' + uuid.uuid4().hex + ext
    path = file_path(name)
    path.parent.mkdir(exist_ok=True)
    path.write_bytes(raw)
    return name

def analyze(t):
    folder = file_path(t['folder'])
    video = folder / 'video.mp4'
    info = probe(video)
    run(['ffmpeg', '-v', 'error', '-xerror', '-i', str(video), '-f', 'null', '-'])
    frames = folder / 'frames'
    frames.mkdir(exist_ok=True)
    run(['ffmpeg', '-v', 'error', '-y', '-i', str(video), '-map', '0:v:0', '-fps_mode', 'passthrough', str(frames / '%06d.png')])
    # Motion differences are a triage signal, never a claim of character animation.
    raw = run(['ffmpeg', '-v', 'error', '-i', str(video), '-vf', 'fps=8,scale=64:36,format=gray', '-f', 'rawvideo', '-'])
    size = 64 * 36
    samples = [raw[i:i+size] for i in range(0, len(raw)-size+1, size)]
    diffs = [sum(abs(a-b) for a,b in zip(x,y))/size for x,y in zip(samples,samples[1:])]
    still = sum(d < 0.6 for d in diffs) / max(1, len(diffs))
    stride = max(1, info['frames'] // 12)
    run(['ffmpeg', '-v', 'error', '-y', '-i', str(video), '-vf',
         f"select='not(mod(n,{stride}))',scale=320:-1,tile=4x3", '-frames:v', '1', str(folder / 'contact.jpg')])
    count = len(list(frames.glob('*.png')))
    t.update(status='review', media=info, frame_count=count, sha256=digest(video),
             still_fraction=round(still, 3), motion_warning=still > .8,
             analysis_note='Pixel changes can be camera motion, flicker or morphing. Review body action and continuity yourself.')
    save(folder / 'take.json', t)

def submit(p, s):
    if s.get('takes') and s['takes'][-1]['status'] in ('submitting', 'unknown', 'IN_QUEUE', 'IN_PROGRESS'):
        raise ValueError('This shot already has a pending or uncertain submission. Check it before buying another take.')
    if not os.environ.get('FAL_KEY'):
        raise ValueError('FAL_KEY is not configured. Set it in your terminal and restart the studio.')
    direction = prompt(p, s)
    raw = file_path(s['image']).read_bytes()
    seconds = float(s['seconds'])
    frames = min(161, max(17, 4 * round((seconds * 16 - 1) / 4) + 1))
    payload = dict(prompt=direction, image_url='data:image/' + ('png' if raw.startswith(b'\x89PNG') else 'jpeg') + ';base64,' + base64.b64encode(raw).decode(),
                   num_frames=frames, frames_per_second=16, resolution='720p', aspect_ratio='auto',
                   num_inference_steps=27, enable_prompt_expansion=False, interpolator_model='none', num_interpolated_frames=0,
                   negative_prompt='slideshow, static pose, camera motion only, morphing, distorted anatomy, flicker, text, watermark')
    name, folder = take_dir(s)
    t = dict(folder=name, status='submitting', prompt=direction, image_sha256=digest(file_path(s['image'])),
             frames_requested=frames, model=ROUTE, created=time.time(), approved=False)
    s.setdefault('takes', []).append(t)
    s['active'] = len(s['takes'])-1
    save(folder / 'take.json', t)
    persist(p)  # Receipt is durable before a possibly paid request.
    try:
        result = api(ROUTE, payload)
        t.update(status='IN_QUEUE', request_id=result['request_id'], status_url=result['status_url'], response_url=result['response_url'])
    except Exception:
        t['status'] = 'unknown'
        raise ValueError('Submission outcome uncertain. Receipt retained; do not resubmit. Check your fal queue for the request.') from None
    finally:
        save(folder / 'take.json', t)
        persist(p)

def poll(t):
    if t['status'] in ('review', 'approved'):
        return
    if not t.get('status_url'):
        raise ValueError('No queue ID is available. Inspect the saved receipt and provider dashboard.')
    result = api(t['status_url'])
    t['status'] = result['status']
    if result.get('error'):
        t['status'] = 'failed'
        raise ValueError('Generation failed: ' + str(result['error']))
    if t['status'] == 'COMPLETED':
        result = api(t['response_url'])
        if result.get('error'):
            t['status'] = 'failed'
            raise ValueError(str(result['error']))
        url = result['video']['url']
        u = urlparse(url)
        if u.scheme != 'https' or not (u.hostname == 'fal.media' or (u.hostname or '').endswith('.fal.media')):
            raise ValueError('Unexpected media host')
        folder = file_path(t['folder'])
        with urlopen(url, timeout=60) as response:
            data = response.read(100_000_001)
        if len(data) > 100_000_000:
            raise ValueError('Generated clip exceeds 100 MB')
        (folder / 'video.mp4').write_bytes(data)
        analyze(t)

def export(p):
    if not p['shots']:
        raise ValueError('Add shots first.')
    takes = []
    for s in p['shots']:
        t = s.get('takes', [])[s.get('active', 0)] if s.get('takes') else None
        if not t or not t.get('approved') or t.get('sha256') != digest(file_path(t['folder']) / 'video.mp4'):
            raise ValueError('Review and approve the current take of every shot first: ' + s['title'])
        takes.append(t)
    folder = file_path('exports/' + uuid.uuid4().hex[:12])
    folder.mkdir(parents=True)
    # Match the first shot's orientation. Normalize without cropping or stretching.
    first = takes[0]['media']
    w, h = (1280, 720) if first['width'] >= first['height'] else (720, 1280)
    for i,t in enumerate(takes):
        run(['ffmpeg', '-v', 'error', '-y', '-i', str(file_path(t['folder']) / 'video.mp4'), '-an', '-vf',
             f'scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=24',
             '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', str(folder / f'{i:03}.mp4')])
    (folder / 'concat.txt').write_text(''.join(f"file '{i:03}.mp4'\n" for i in range(len(takes))))
    run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '1', '-i', str(folder / 'concat.txt'), '-c', 'copy', '-movflags', '+faststart', str(folder / 'film.mp4')])
    save(folder / 'edit.json', {'project':p, 'note':'Silent picture edit; 24 fps container repeats source frames where necessary, no synthesized interpolation.'})
    p['export'] = str((folder / 'film.mp4').relative_to(ROOT))

def action(name, data):
    with LOCK:
        p = load()
        if name == 'save':
            before = json.dumps({k:p[k] for k in ('style','characters','world')}, sort_keys=True)
            previous_order = [s['id'] for s in p['shots']]
            changed = set()
            for key in ('title','style','characters','world'):
                p[key] = str(data[key])[:10000]
            order = data.get('shots', [])
            if sorted(s['id'] for s in order) != sorted(s['id'] for s in p['shots']):
                raise ValueError('Shot list changed. Reload before saving.')
            lookup = {s['id']:s for s in p['shots']}
            for row in order:
                if any(str(row.get(k,'')) != str(lookup[row['id']].get(k,'')) for k in FIELDS if k != 'title'):
                    changed.add(row['id'])
                for field in FIELDS:
                    lookup[row['id']][field] = str(row.get(field, ''))[:6000]
                seconds = float(lookup[row['id']]['seconds'])
                if not 2 <= seconds <= 10:
                    raise ValueError('Shot duration must be 2–10 seconds.')
            p['shots'] = [lookup[row['id']] for row in order]
            after = json.dumps({k:p[k] for k in ('style','characters','world')}, sort_keys=True)
            if before != after or previous_order != [s['id'] for s in p['shots']]:
                changed = {s['id'] for s in p['shots']}
            # Changes to a shot's ending also affect the next shot's continuity.
            affected = set(changed)
            for i,s in enumerate(p['shots'][:-1]):
                if s['id'] in changed:
                    affected.add(p['shots'][i+1]['id'])
            for s in p['shots']:
                if s['id'] in affected:
                    for t in s['takes']:
                        t['approved'] = False
                        t.pop('review', None)
                        if t['status'] == 'approved':
                            t['status'] = 'review'
                        save(file_path(t['folder']) / 'take.json', t)
        elif name == 'upload':
            image = upload(data, image=True)
            p['shots'].append(dict(id=uuid.uuid4().hex[:12], image=image, title=Path(data['name']).stem,
                start='', action='', end='', secondary='Hair and fabric follow the body action.', camera='Locked camera; readable full-body action.',
                continuity='Maintain screen direction, outfit, proportions and lighting.', seconds='5', takes=[], active=0))
        elif name == 'export':
            export(p)
        else:
            s = next((s for s in p['shots'] if s['id'] == data.get('id')), None)
            if not s:
                raise ValueError('Shot not found')
            if name == 'prompt':
                return {'prompt':prompt(p,s)}
            if name == 'render':
                submit(p,s)
            elif name == 'import':
                asset = upload(data)
                folder, path = take_dir(s)
                shutil.move(str(file_path(asset)), path / 'video.mp4')
                t = dict(folder=folder, status='imported', approved=False, created=time.time(), model='Imported clip')
                analyze(t)
                s['takes'].append(t)
                s['active'] = len(s['takes'])-1
            elif name == 'select':
                index = int(data['index'])
                if not 0 <= index < len(s['takes']):
                    raise ValueError('Invalid take')
                s['active'] = index
            elif name == 'framezip':
                t = s['takes'][s['active']]
                if not t.get('frame_count'):
                    raise ValueError('Collect or import a rendered take first.')
                folder = file_path(t['folder'])
                target = folder / 'frames.zip'
                if not target.exists():
                    temporary = folder / 'frames.zip.tmp'
                    with zipfile.ZipFile(temporary, 'w', zipfile.ZIP_STORED) as archive:
                        for frame in sorted((folder / 'frames').glob('*.png')):
                            archive.write(frame, 'frames/' + frame.name)
                        archive.write(folder / 'take.json', 'take.json')
                    temporary.replace(target)
                return {'url':str(target.relative_to(ROOT))}
            elif name in ('poll','approve'):
                t = s['takes'][s['active']]
                if name == 'poll':
                    try:
                        poll(t)
                    finally:
                        save(file_path(t['folder']) / 'take.json', t)
                        persist(p)
                else:
                    if t['status'] not in ('review','approved') or not all(data.get(k) is True for k in CHECKS):
                        raise ValueError('Review the rendered take and check all four quality criteria.')
                    if digest(file_path(t['folder']) / 'video.mp4') != t['sha256']:
                        raise ValueError('Clip changed since analysis; import it as a new take.')
                    t.update(approved=True, status='approved', review={k:True for k in CHECKS}, notes=str(data.get('notes','')))
                    save(file_path(t['folder']) / 'take.json', t)
            else:
                raise ValueError('Unknown action')
        persist(p)
        return p

class Handler(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def trusted(self):
        allowed = {f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'}
        if self.headers.get('Host') not in allowed:
            raise ValueError('Use the localhost studio address.')
        origin = self.headers.get('Origin')
        if origin and origin not in {'http://' + h for h in allowed}:
            raise ValueError('Cross-origin requests are not allowed.')

    def reply(self, body, code=200, mime='application/json'):
        if not isinstance(body, bytes):
            body = json.dumps(body).encode()
        self.send_response(code)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        try:
            self.trusted()
            route = unquote(urlparse(self.path).path)
            if route == '/api/project':
                with LOCK:
                    return self.reply({'project':load(), 'configured':bool(os.environ.get('FAL_KEY'))})
            if route == '/':
                return self.reply((HERE / 'index.html').read_bytes(), mime='text/html; charset=utf-8')
            if route.startswith('/media/'):
                path = file_path(route[len('/media/'):])
                if path.suffix.lower() not in ('.png','.jpg','.mp4','.zip'):
                    raise ValueError('Unsupported media')
                return self.reply(path.read_bytes(), mime=mimetypes.guess_type(path.name)[0] or 'application/octet-stream')
            self.reply({'error':'Not found'},404)
        except Exception as exc:
            self.reply({'error':str(exc)},400)

    def do_POST(self):
        try:
            self.trusted()
            if self.headers.get('Content-Type') != 'application/json':
                raise ValueError('JSON required')
            length = int(self.headers.get('Content-Length',0))
            if not 0 < length < 125_000_000:
                raise ValueError('Invalid request size')
            self.reply(action(self.path.removeprefix('/api/'), json.loads(self.rfile.read(length))))
        except Exception as exc:
            self.reply({'error':str(exc)},400)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--workspace', type=Path, default=ROOT)
    args = parser.parse_args()
    ROOT = args.workspace.resolve()
    for binary in ('ffmpeg','ffprobe'):
        if not shutil.which(binary):
            parser.error(f'{binary} must be installed')
    load()
    try:
        server = ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
    except PermissionError:
        parser.exit(1, 'This environment blocks local server sockets. Run Start.sh from your desktop terminal.\n')
    print(f'Anime Motion → http://127.0.0.1:{args.port}', flush=True)
    server.serve_forever()
