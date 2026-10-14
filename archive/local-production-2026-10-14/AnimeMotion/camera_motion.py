#!/usr/bin/env python3
"""Local, non-destructive camera tracks over existing animation. No generation APIs."""
import argparse
import copy
import csv
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import tempfile

EASINGS = ('linear', 'smooth', 'smoother', 'ease-in', 'ease-out', 'hold')
SIZES = {'draft': [640, 360], 'preview': [1280, 720], 'hd': [1920, 1080], '4k': [3840, 2160]}


def command(args, timeout=900):
    result = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    if result.returncode:
        raise ValueError(result.stderr[-2500:])
    return result.stdout


def probe(path):
    data = json.loads(command(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(path)]))
    video = next((s for s in data['streams'] if s['codec_type'] == 'video'), None)
    if not video:
        raise ValueError(f'No video stream in {path}')
    return dict(width=video['width'], height=video['height'], duration=float(video.get('duration', data['format'].get('duration', 0))),
                audio=any(s['codec_type'] == 'audio' for s in data['streams']))


def number(value, low, high, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError(f'{name} must be a finite number in {low}..{high}.')
    return float(value)


def track(keys):
    if keys is None:
        keys = [{'at': 0}, {'at': 1}]
    if not isinstance(keys, list) or not 2 <= len(keys) <= 30:
        raise ValueError('Camera needs 2–30 keyframes.')
    result = []
    for key in keys:
        item = {k: number(key.get(k, default), low, high, k) for k, default, low, high in
                [('at', None, 0, 1), ('x', .5, 0, 1), ('y', .5, 0, 1), ('zoom', 1, 1, 8)]}
        item['ease'] = key.get('ease', 'smoother')
        if item['ease'] not in EASINGS:
            raise ValueError('Unknown easing: ' + str(item['ease']))
        result.append(item)
    if result[0]['at'] != 0 or result[-1]['at'] != 1 or any(a['at'] >= b['at'] for a, b in zip(result, result[1:])):
        raise ValueError('Camera keys must increase strictly from at=0 to at=1.')
    return result


def ease(t, kind):
    if kind == 'smooth':
        return t*t*(3-2*t)
    if kind == 'smoother':
        return t*t*t*(t*(6*t-15)+10)
    if kind == 'ease-in':
        return t*t
    if kind == 'ease-out':
        return 1-(1-t)**2
    return 0 if kind == 'hold' else t


def sample(keys, progress):
    progress = min(1, max(0, progress))
    if progress == 1:
        raw = {k: keys[-1][k] for k in ('x', 'y', 'zoom')}
    else:
        a, b = next((a, b) for a, b in zip(keys, keys[1:]) if a['at'] <= progress < b['at'])
        t = ease((progress-a['at'])/(b['at']-a['at']), a['ease'])
        raw = {k: a[k]+(b[k]-a[k])*t for k in ('x', 'y', 'zoom')}
    half = .5/raw['zoom']
    actual = {k: min(1-half, max(half, raw[k])) for k in ('x', 'y')}
    return dict(**actual, zoom=raw['zoom'], clamped=any(abs(actual[k]-raw[k]) > 1e-9 for k in ('x', 'y')))


def ease_expression(t, kind):
    if kind == 'smooth':
        return f'({t})*({t})*(3-2*({t}))'
    if kind == 'smoother':
        return f'pow({t},3)*(({t})*(6*({t})-15)+10)'
    if kind == 'ease-in':
        return f'pow({t},2)'
    if kind == 'ease-out':
        return f'(1-pow(1-({t}),2))'
    return '0' if kind == 'hold' else t


def expression(keys, field, frames):
    p = f'(on/{max(1, frames-1)})'
    expr = str(keys[-1][field])
    for a, b in reversed(list(zip(keys, keys[1:]))):
        t = f'(({p}-{a["at"]})/{b["at"]-a["at"]})'
        value = f'({a[field]}+({b[field]-a[field]})*({ease_expression(t,a["ease"])}))'
        expr = f'if(lt({p},{b["at"]}),{value},{expr})'
    return expr


def preset(name):
    presets = {
        'locked': [{'at': 0}, {'at': 1}],
        'push-in': [{'at': 0, 'zoom': 1}, {'at': 1, 'zoom': 1.18}],
        'pull-back': [{'at': 0, 'zoom': 1.18}, {'at': 1, 'zoom': 1}],
        'pan-right': [{'at': 0, 'zoom': 1.2, 'x': .44}, {'at': 1, 'zoom': 1.2, 'x': .56}],
        'pan-left': [{'at': 0, 'zoom': 1.2, 'x': .56}, {'at': 1, 'zoom': 1.2, 'x': .44}],
        'rise': [{'at': 0, 'zoom': 1.2, 'y': .56}, {'at': 1, 'zoom': 1.2, 'y': .44}],
    }
    if name not in presets:
        raise ValueError('Unknown preset: ' + name)
    return copy.deepcopy(presets[name])


def validate(spec, base):
    fps = spec.get('fps', 60)
    if type(fps) is not int or fps not in (24, 30, 60):
        raise ValueError('Output fps must be 24, 30 or 60.')
    size = spec.get('size', SIZES['preview'])
    if not isinstance(size, list) or len(size) != 2 or any(type(n) is not int or n < 32 or n > 4096 or n % 2 for n in size):
        raise ValueError('Size must contain two even dimensions, 32–4096.')
    if not isinstance(spec.get('shots'), list) or not 1 <= len(spec['shots']) <= 30:
        raise ValueError('Use 1–30 shots.')
    shots = []
    for i, original in enumerate(spec['shots']):
        shot = copy.deepcopy(original)
        source = (base/shot['source']).resolve()
        if not source.is_file():
            raise ValueError(f'Missing source: {source}')
        info = probe(source)
        start = number(shot.get('start', 0), 0, info['duration'], 'start')
        duration = number(shot.get('duration', info['duration']-start), 1/fps, 300, 'duration')
        if start+duration > info['duration']+.001:
            raise ValueError('Shot trim extends past the source video.')
        fit = shot.get('fit', 'match')
        if fit not in ('match', 'cover', 'contain'):
            raise ValueError('fit must be match, cover or contain.')
        if fit == 'match' and abs((info['width']/info['height'])/(size[0]/size[1])-1) > .01:
            raise ValueError('Aspect ratios differ. Set fit=contain for letterboxing or fit=cover for an intentional crop.')
        keys = track(shot.get('camera', preset(shot['preset']) if 'preset' in shot else None))
        frames = round(duration*fps)
        protected = shot.get('protected', [])
        if protected:
            if fit != 'match':
                raise ValueError('Protected subject framing requires fit=match.')
            for box in protected:
                if not isinstance(box, list) or len(box) != 4:
                    raise ValueError('Protected bounds must be normalized x,y,width,height.')
                x,y,w,h = [number(v,0,1,'protected bound') for v in box]
                if w <= 0 or h <= 0 or x+w > 1 or y+h > 1:
                    raise ValueError('Protected bounds extend outside the scene.')
            from locked_scene import check_camera
            check_camera(keys, protected, frames)
        transition = shot.get('transition', {'type': 'cut'})
        kind = transition.get('type', 'cut')
        if kind not in ('cut', 'dissolve', 'fade-black'):
            raise ValueError('Transition must be cut, dissolve or fade-black.')
        overlap = 0 if kind == 'cut' else round(number(transition.get('seconds', .2), 1/fps, 5, 'transition.seconds')*fps)
        if i == 0 and overlap:
            raise ValueError('The first shot cannot transition from a previous shot.')
        if overlap and (overlap >= frames or overlap >= shots[-1]['frames']-shots[-1]['overlap']):
            raise ValueError('Transition is too long or overlaps the preceding transition.')
        shots.append(dict(source=source, info=info, start=start, frames=frames, duration=frames/fps, camera=keys,
                          fit=fit, protected=protected, overlap=overlap, transition=kind, name=str(shot.get('name', f'Shot {i+1}'))))
    return fps, size, shots


def filter_for(shot, fps, size):
    w, h = size
    oversample = 2 if w*h <= 1920*1080 else 1
    ow, oh = w*oversample, h*oversample
    if shot['fit'] in ('contain', 'match'):
        canvas = f'scale={ow}:{oh}:force_original_aspect_ratio=decrease:flags=lanczos,pad={ow}:{oh}:(ow-iw)/2:(oh-ih)/2'
    else:
        canvas = f'scale={ow}:{oh}:force_original_aspect_ratio=increase:flags=lanczos,crop={ow}:{oh}'
    z = expression(shot['camera'], 'zoom', shot['frames'])
    x = expression(shot['camera'], 'x', shot['frames'])
    y = expression(shot['camera'], 'y', shot['frames'])
    return (f'trim=duration={shot["duration"]:.9f},setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration=1,'
            f'fps={fps},{canvas},setsar=1,'
            f"zoompan=z='{z}':x='clip(iw*({x})-iw/zoom/2,0,iw-iw/zoom)':"
            f"y='clip(ih*({y})-ih/zoom/2,0,ih-ih/zoom)':d=1:s={w}x{h}:fps={fps},format=yuv420p")


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        while block := f.read(1024*1024):
            h.update(block)
    return h.hexdigest()


def render(spec_path, output, quality=None):
    spec_path, output = Path(spec_path).resolve(), Path(output).resolve()
    spec = json.loads(spec_path.read_text())
    if quality:
        spec['size'] = SIZES[quality]
    fps, size, shots = validate(spec, spec_path.parent)
    if output.exists():
        raise ValueError('Output exists; use a new take directory.')
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='camera-build-', dir=output.parent) as tmp:
        build = Path(tmp)/'result'
        build.mkdir()
        parts = build/'shots'; parts.mkdir()
        camera_rows, report = [], []
        for i, shot in enumerate(shots):
            print(f'Rendering camera {i+1}/{len(shots)}: {shot["name"]}', flush=True)
            filt = filter_for(shot, fps, size)
            (parts/f'{i:03d}.filter.txt').write_text(filt)
            clip = parts/f'{i:03d}.mp4'
            command(['ffmpeg', '-v', 'error', '-filter_threads', '1', '-threads', '2', '-ss', str(shot['start']),
                     '-i', str(shot['source']), '-an', '-vf', filt, '-frames:v', str(shot['frames']),
                     '-c:v', 'libx264', '-threads', '2', '-preset', 'veryfast', '-crf', '16', '-pix_fmt', 'yuv420p', str(clip)])
            clamped = 0
            for frame in range(shot['frames']):
                cam = sample(shot['camera'], frame/max(1, shot['frames']-1))
                clamped += cam['clamped']
                camera_rows.append(dict(shot=i+1, frame=frame, seconds=frame/fps, **cam))
            report.append(dict(name=shot['name'], source=str(shot['source']), sha256=sha256(shot['source']),
                               source_size=[shot['info']['width'], shot['info']['height']], camera=shot['camera'],
                               frames=shot['frames'], start=shot['start'], overlap_frames=shot['overlap'],
                               transition=shot['transition'], clamped_frames=clamped,
                               protected=shot['protected'],
                               audio_omitted=shot['info']['audio']))
        total = sum(s['frames']-s['overlap'] for s in shots)
        if len(shots) == 1:
            shutil.copyfile(parts/'000.mp4', build/'camera.mp4')
        elif all(s['transition']=='cut' for s in shots):
            # Identically encoded parts can be joined without a second lossy encode.
            listing=parts/'concat.txt'
            listing.write_text(''.join(f"file '{i:03d}.mp4'\n" for i in range(len(shots))))
            command(['ffmpeg','-v','error','-f','concat','-safe','1','-i',str(listing),
                     '-c','copy','-movflags','+faststart',str(build/'camera.mp4')])
        else:
            args = ['ffmpeg', '-v', 'error', '-filter_complex_threads', '1']
            graph = []
            for i in range(len(shots)):
                args += ['-i', str(parts/f'{i:03d}.mp4')]
                graph.append(f'[{i}:v]settb=1/{fps},setpts=PTS-STARTPTS[v{i}]')
            last, count = 'v0', shots[0]['frames']
            for i, shot in enumerate(shots[1:], 1):
                if shot['overlap']:
                    trans = 'fade' if shot['transition'] == 'dissolve' else 'fadeblack'
                    graph.append(f'[{last}][v{i}]xfade=transition={trans}:duration={shot["overlap"]/fps:.9f}:offset={(count-shot["overlap"])/fps:.9f}[o{i}]')
                else:
                    graph.append(f'[{last}][v{i}]concat=n=2:v=1:a=0,settb=1/{fps}[o{i}]')
                last = f'o{i}'
                count += shot['frames']-shot['overlap']
            (build/'edit.filter.txt').write_text(';'.join(graph))
            command(args+['-filter_complex', ';'.join(graph), '-map', f'[{last}]', '-an', '-r', str(fps),
                          '-frames:v', str(total), '-c:v', 'libx264', '-threads', '2', '-preset', 'veryfast',
                          '-crf', '16', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(build/'camera.mp4')])
        measured = json.loads(command(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0',
                                      '-show_entries', 'stream=nb_read_frames,width,height,avg_frame_rate', '-of', 'json', str(build/'camera.mp4')]))['streams'][0]
        if int(measured['nb_read_frames']) != total or [measured['width'], measured['height']] != size:
            raise ValueError('Render dimensions/frame count differ from the camera timeline.')
        with (build/'camera-samples.csv').open('w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=list(camera_rows[0]))
            writer.writeheader(); writer.writerows(camera_rows)
        manifest = dict(fps=fps, size=size, frames=total, duration=total/fps, shots=report,
                        method='Camera transforms at output frame rate. Source cel timing retained; no new artwork or optical-flow in-betweens. Silent picture edit.', spec=spec)
        (build/'camera-manifest.json').write_text(json.dumps(manifest, indent=2))
        (build/'source-spec.json').write_text(spec_path.read_text())
        command(['ffmpeg', '-v', 'error', '-i', str(build/'camera.mp4'), '-frames:v', '1', str(build/'poster.png')])
        build.replace(output)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='operation', required=True)
    r = sub.add_parser('render')
    r.add_argument('spec', type=Path)
    r.add_argument('--out', required=True, type=Path)
    r.add_argument('--quality', choices=SIZES)
    p = sub.add_parser('preset')
    p.add_argument('name', choices=('locked','push-in','pull-back','pan-left','pan-right','rise'))
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--save', type=Path, required=True)
    p.add_argument('--duration', type=float)
    args = parser.parse_args()
    try:
        if args.operation == 'preset':
            item = {'source': str(args.source.resolve()), 'camera': preset(args.name)}
            if args.duration is not None:
                item['duration'] = args.duration
            result = dict(fps=60, size=SIZES['preview'], shots=[item])
            validate(result, args.save.resolve().parent)
            with args.save.open('x') as f:
                json.dump(result, f, indent=2)
            print(args.save.resolve())
        else:
            result = render(args.spec, args.out, args.quality)
            print(json.dumps({k:result[k] for k in ('size','fps','frames','duration')}))
            print(args.out.resolve()/'camera.mp4')
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        parser.exit(1, str(exc)+'\n')


if __name__ == '__main__':
    main()
