#!/usr/bin/env python3
"""Frame-based local episode builder. Python stdlib + FFmpeg; no service keys.

Artwork is supplied by imagegen or an illustrator. Missing shots fail closed:
the exporter never fills an unfinished episode with repeated preview footage.
"""
import argparse
import html
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent
FPS = 24


def run(args):
    p = subprocess.run([str(a) for a in args], capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError(p.stderr[-4000:])
    return p.stdout


def ff(*args):
    return run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-nostdin', '-y',
                '-threads', '1', '-filter_threads', '1', '-filter_complex_threads', '1', *args])


def probe(path):
    return json.loads(run(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0',
                          '-show_entries', 'stream=width,height,pix_fmt,nb_read_frames,avg_frame_rate',
                          '-of', 'json', path]))['streams'][0]


def split_fx(text):
    """Semicolons inside arguments do not delimit effects."""
    result, token, depth = [], '', 0
    for char in text:
        if char == ';' and depth == 0:
            result.append(token.strip()); token = ''; continue
        token += char
        depth += (char == '(') - (char == ')')
        if depth < 0:
            raise ValueError('Unbalanced FX arguments')
    if depth:
        raise ValueError('Unbalanced FX arguments')
    if token.strip(): result.append(token.strip())
    return [dict(name=t.split('(', 1)[0].strip(),
                 args=t.split('(', 1)[1][:-1] if '(' in t else '') for t in result]


def intake():
    data = json.loads((ROOT/'data/shots.source.json').read_text())
    current = None
    for line in (ROOT/'data/script.md').read_text().splitlines():
        match = re.match(r'\*\*(S\d+-\d+)\*\*', line)
        if match: current = match[1]
        if current and line.startswith('- **FX:** `'):
            fx = split_fx(line.split('`')[1])
            for shot in data['shots']:
                if shot['id'] == current: shot['fx'] = fx
            current = None
    end = 0
    ids = set()
    for shot in data['shots']:
        if shot['id'] in ids or shot['start_frame'] != end or shot['frames'] <= 0:
            raise ValueError('Invalid timeline at '+shot['id'])
        ids.add(shot['id']); end += shot['frames']
    if end != data['total_frames'] or data['fps'] != FPS:
        raise ValueError('Episode duration or frame rate mismatch')
    (ROOT/'data/shots.json').write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n')
    return data


def motion(a, b, frames, ease=False):
    p = f'min(t*24/{max(1,frames-1)},1)'
    if ease: p = f'(({p})*({p})*(3-2*({p})))'
    return f'({a}+({b-a})*({p}))'


def drawing_at(exposures, frame, loop=False):
    total = sum(hold for _, hold in exposures)
    if total <= 0: raise ValueError('Empty exposure track')
    if loop: frame %= total
    for cel, hold in exposures:
        if frame < hold: return cel
        frame -= hold
    return exposures[-1][0]


def validate_plan(shot, plan):
    if plan['kind'] not in ('sigil', 'card', 'composite'):
        raise ValueError('Unknown renderer')
    if plan['kind'] != 'composite': return
    if not (ROOT/plan['background']).is_file(): raise ValueError('Missing background')
    camera = plan.get('camera', {'x':[0,0], 'y':[0,0]})
    for axis in ('x','y'):
        if len(camera[axis]) != 2 or any(not math.isfinite(v) or v < 0 for v in camera[axis]):
            raise ValueError('Camera must stay inside its overscan')
    for layer in plan.get('layers', []):
        if not math.isfinite(layer['width']) or layer['width'] <= 0:
            raise ValueError('Invalid layer scale')
        for axis in ('x', 'y'):
            if len(layer[axis]) != 2 or any(not math.isfinite(v) for v in layer[axis]):
                raise ValueError('Invalid layer motion')
        if layer.get('keep_in_frame') and (min(layer['x']) < 0 or max(layer['x'])+layer['width'] > 1):
            raise ValueError('Protected character layer leaves the frame')
        if 'sheet' in layer or 'files' in layer:
            paths = layer.get('files', [layer.get('sheet')])
            if any(not (ROOT/path).is_file() for path in paths): raise ValueError('Missing animation cel')
            if not layer.get('loop') and sum(n for _,n in layer['exposures']) != shot['frames']:
                raise ValueError('Exposure track does not match shot length')
        elif not (ROOT/layer['image']).is_file(): raise ValueError('Missing cel layer')


def sequence(layer, count, work):
    if 'files' in layer:
        work.mkdir()
        width, height = layer['canvas']
        for i, path in enumerate(layer['files']):
            source = ROOT/path
            if 'a' not in probe(source)['pix_fmt']: raise ValueError('Cel must have alpha')
            ff('-i', source, '-vf', f'format=rgba,scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=black@0', '-frames:v', '1', work/f'cel-{i}.png')
        for frame in range(count):
            cel = drawing_at(layer['exposures'], frame, layer.get('loop', False))
            if not 0 <= cel < len(layer['files']): raise ValueError('Invalid cel index')
            (work/f'{frame:06d}.png').symlink_to(f'cel-{cel}.png')
        return work/'%06d.png'
    path = ROOT/layer['sheet']
    info = probe(path)
    if 'a' not in info['pix_fmt']:
        raise ValueError('Cel sheet must have transparency: '+str(path))
    cols, rows = layer['grid']
    exposures = layer['exposures']
    if any(not isinstance(i, int) or not 0 <= i < cols*rows or
           not isinstance(n, int) or n < 1 for i, n in exposures):
        raise ValueError('Invalid cel exposure')
    work.mkdir()
    for cel in sorted({i for i, _ in exposures}):
        x0 = (cel % cols)*info['width']//cols; x1 = (cel % cols+1)*info['width']//cols
        y0 = (cel // cols)*info['height']//rows; y1 = (cel // cols+1)*info['height']//rows
        ff('-i', path, '-vf', f'format=rgba,crop={x1-x0}:{y1-y0}:{x0}:{y0}:exact=1,scale=600:600',
           '-frames:v', '1', work/f'cel-{cel}.png')
    for frame in range(count):
        cel = drawing_at(exposures, frame, layer.get('loop', False))
        (work/f'{frame:06d}.png').symlink_to(f'cel-{cel}.png')
    return work/'%06d.png'


def title_frames(shot, plan, work, width, height):
    """Native vector title design, deterministically rasterized by librsvg."""
    work.mkdir()
    points = []
    for i in range(121):
        t = i/120; angle = t*math.pi*4-1.1; radius = 3+76*t
        points.append((480+radius*math.cos(angle), 288+radius*math.sin(angle)))
    points.extend([(480, 173), (600, 375), (360, 375), (480, 173)])
    for frame in range(shot['frames']):
        content = ''
        if plan['kind'] == 'sigil':
            p = min(1, frame/71)
            n = max(2, round(len(points)*p))
            poly = ' '.join(f'{x:.2f},{y:.2f}' for x, y in points[:n])
            content = f'<polyline points="{poly}" fill="none" stroke="#C9A24A" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"/>'
        else:
            opacity = min(1, frame/23)
            content = f'<g opacity="{opacity:.5f}" font-family="Noto Serif" text-anchor="middle" fill="#EDE6D6">'
            for text, y, size in plan['lines']:
                content += f'<text x="480" y="{y}" font-size="{size}" letter-spacing="2">{html.escape(text)}</text>'
            content += '</g>'
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 960 720"><rect width="960" height="720" fill="#14202B"/>{content}</svg>'
        (work/f'{frame:06d}.svg').write_text(svg)
    return work/'%06d.svg'


def render_shot(shot, plan, target, width, height):
    validate_plan(shot, plan)
    frames = shot['frames']
    with tempfile.TemporaryDirectory(prefix='shot-', dir=target.parent) as temp:
        work = Path(temp)
        args, graph = [], []
        if plan['kind'] in ('sigil', 'card'):
            src = title_frames(shot, plan, work/'titles', width, height)
            args = ['-framerate', str(FPS), '-i', str(src)]
            graph.append('[0:v]format=yuv420p[out]')
        else:
            # Work at 2x to preserve half-pixel camera motion at output resolution.
            bg = ROOT/plan['background']
            camera = plan.get('camera', {'x':[0,0], 'y':[0,0]})
            sw = 2*width+2*max(camera['x'])+4
            sh = 2*height+2*max(camera['y'])+4
            sw += sw % 2; sh += sh % 2
            args += ['-loop', '1', '-framerate', '24', '-i', str(bg)]
            cx = motion(2*camera['x'][0], 2*camera['x'][1], frames, True)
            cy = motion(2*camera['y'][0], 2*camera['y'][1], frames, True)
            graph.append(f'[0:v]scale={sw}:{sh}:force_original_aspect_ratio=increase:flags=lanczos,crop={sw}:{sh},setsar=1[plate]')
            last = 'plate'
            if plan.get('water'):
                top = round(sh*plan['water']['top'])
                wh = sh-top
                graph.append(f'[plate]split[bank][water]')
                # Restrained displacement confined to water with a feathered join.
                coord = 'clip(X+2*sin(Y/19+2*PI*T/3)*min(Y/32,1),0,W-1)'
                graph.append(f"[water]crop={sw}:{wh}:0:{top},fps=8,scale={sw//6}:{max(2,wh//6)},format=yuv444p,geq=lum='lum({coord},Y)':cb='cb({coord},Y)':cr='cr({coord},Y)',scale={sw}:{wh}[ripples]")
                graph.append(f'[bank][ripples]overlay=0:{top}[river]')
                last = 'river'
            graph.append(f"[{last}]crop={2*width}:{2*height}:x='{cx}':y='{cy}'[world]")
            last = 'world'
            for index, layer in enumerate(plan.get('layers', []), 1):
                if 'sheet' in layer or 'files' in layer:
                    src = sequence(layer, frames, work/f'cels-{index}')
                    args += ['-framerate', '24', '-i', str(src)]
                else:
                    src = ROOT/layer['image']
                    if 'a' not in probe(src)['pix_fmt']: raise ValueError('Layer must have alpha')
                    args += ['-loop', '1', '-framerate', '24', '-i', str(src)]
                lw = round(2*width*layer['width'])
                x = motion(2*width*layer['x'][0], 2*width*layer['x'][1], frames)
                y = motion(2*height*layer['y'][0], 2*height*layer['y'][1], frames)
                if layer.get('bob'): y += f'+{2*layer["bob"]}*sin(2*PI*t/3.6)'
                graph.append(f'[{index}:v]scale={lw}:-1:flags=lanczos,format=rgba[cel{index}]')
                graph.append(f"[{last}][cel{index}]overlay=x='{x}':y='{y}':eval=frame:format=auto[composite{index}]")
                last = f'composite{index}'
            graph.append(f'[{last}]scale={width}:{height}:flags=lanczos,setsar=1,format=yuv420p[scaled]')
            last = 'scaled'
            if plan.get('super'):
                textfile = work/'super.txt'; textfile.write_text(plan['super'])
                graph.append(f"[{last}]drawtext=fontfile=/usr/share/fonts/noto/NotoSerif-Regular.ttf:textfile='{textfile}':fontsize={round(height*.027)}:fontcolor=0xEDE6D6:x=w*0.08:y=h*0.88:alpha='min(t,1)'[lettered]")
                last = 'lettered'
            graph.append(f'[{last}]null[out]')
        filtertext = ';'.join(graph)
        (work/'filter.txt').write_text(filtertext)
        ff(*args, '-filter_complex', filtertext, '-map', '[out]', '-progress', work/'progress.log',
           '-frames:v', str(frames), '-r', '24', '-an', '-c:v', 'libx264', '-threads', '2',
           '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', work/'video.mp4')
        measured = probe(work/'video.mp4')
        if int(measured['nb_read_frames']) != frames or measured['avg_frame_rate'] != '24/1':
            raise ValueError('Incomplete render: '+shot['id'])
        shutil.copy2(work/'video.mp4', target)
        target.with_suffix('.json').write_text(json.dumps(dict(shot=shot['id'], measured=measured,
            source_start_frame=shot['start_frame'], limitations=plan.get('limitations', []),
            audio='pending', plan=plan), indent=2)+'\n')
        for label, frame in [('first', 0), ('middle', frames//2), ('last', frames-1)]:
            ff('-i', target, '-vf', f'select=eq(n\\,{frame})', '-frames:v', '1',
               target.parent/f'{shot["id"]}-{label}.jpg')


def review(data, plans, output):
    cards, completed = [], 0
    for shot in data['shots']:
        sid = shot['id']; path = output/f'{sid}.mp4'
        ready = path.is_file()
        if ready: completed += 1
        video = f'<video controls preload="none" poster="{sid}-middle.jpg" src="{sid}.mp4"></video>' if ready else ''
        detail = '; '.join(plans.get(sid, {}).get('limitations', []))
        cards.append(f'<article id="{sid}"><h2>{sid} · {shot["tc_in"]} · {shot["frames"]/24:g}s</h2><b>{"Motion draft · audio pending" if ready else "Awaiting production"}</b>{video}<p>{html.escape(shot["action"])}</p><small>{html.escape(shot["camera"])}</small><p>{html.escape(detail)}</p></article>')
    doc = '<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Heralds · Episode production</title><style>body{background:#101921;color:#ede6d6;font:17px/1.6 system-ui;max-width:1100px;margin:40px auto;padding:24px}h1,h2{font-family:serif}h2{font-size:22px}article{background:#182630;border:1px solid #34414a;border-radius:12px;padding:24px;margin:20px 0}video{display:block;width:100%;max-height:70vh;margin:20px 0;background:black}small,b{color:#c9a24a}a{color:#7fb7d6}</style>'
    doc += f'<h1>Heralds of the Cemí — “3:07”</h1><p>1990s cel anime · 4:3 · 24 fps · {completed}/128 shots have motion drafts. Full episode: 18:50. Unfinished shots are listed below.</p>'
    if (output/'opening-assembly.mp4').is_file():
        doc += '<p><a href="opening-assembly.mp4">Play the continuous opening draft</a></p><video controls preload="metadata" src="opening-assembly.mp4"></video>'
    doc += '<p>Hold a drawing for several frames; move the camera every frame. This page records drafts, not final episode completion.</p>'+''.join(cards)
    (output/'review.html').write_text(doc)
    (output/'status.json').write_text(json.dumps({'rendered_drafts':completed, 'total_shots':128,
        'full_episode_complete':False,'audio':'pending', 'shots':{s['id']: ('motion_draft' if (output/f'{s["id"]}.mp4').exists() else 'pending') for s in data['shots']}}, indent=2))


def assemble(data, ids, output, name):
    shots = {s['id']:s for s in data['shots']}
    previous = None
    for sid in ids:
        shot = shots[sid]
        if previous is not None and shot['start_frame'] != previous:
            raise ValueError('Assembly must contain contiguous source shots')
        previous = shot['start_frame']+shot['frames']
        if not (output/f'{sid}.mp4').exists(): raise ValueError('Missing shot: '+sid)
    concat = output/'concat.txt'
    concat.write_text(''.join(f"file '{sid}.mp4'\n" for sid in ids))
    ff('-f', 'concat', '-safe', '1', '-i', concat, '-c', 'copy', '-movflags', '+faststart', output/name)
    if int(probe(output/name)['nb_read_frames']) != sum(shots[s]['frames'] for s in ids):
        raise ValueError('Assembly frame count mismatch')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=['validate','render','review','assemble'])
    p.add_argument('--shots', nargs='+')
    p.add_argument('--width', type=int, default=1440)
    p.add_argument('--output', default='build/take-01')
    args = p.parse_args()
    if args.width < 320 or args.width % 8: p.error('Width must be a multiple of 8, at least 320')
    data = intake(); plans = json.loads((ROOT/'data/render-plans.json').read_text())
    output = (ROOT/args.output).resolve(); output.mkdir(parents=True, exist_ok=True)
    by_id = {s['id']:s for s in data['shots']}
    ids = args.shots or list(plans)
    if any(s not in by_id for s in ids): p.error('Unknown shot ID')
    if args.command == 'validate':
        print(f"Validated {len(data['shots'])} shots, {data['total_frames']} frames; FX arguments recovered from script.")
    elif args.command == 'render':
        missing = [sid for sid in ids if sid not in plans]
        if missing: raise ValueError('No production assets/plan for '+', '.join(missing))
        for sid in ids:
            target = output/f'{sid}.mp4'
            if target.exists():
                record = json.loads(target.with_suffix('.json').read_text())
                if (record['plan'] != plans[sid] or record['measured']['width'] != args.width
                        or record['measured']['height'] != args.width*3//4):
                    raise ValueError(f'{sid} has a different plan or resolution. Use a new output take.')
                print('Already rendered; use a new take to revise:', sid, flush=True); continue
            print('Rendering', sid, flush=True)
            render_shot(by_id[sid], plans[sid], target, args.width, args.width*3//4)
            review(data, plans, output)
    elif args.command == 'assemble':
        assemble(data, ids, output, 'opening-assembly.mp4')
    review(data, plans, output)
    print(output/'review.html')


if __name__ == '__main__': main()
