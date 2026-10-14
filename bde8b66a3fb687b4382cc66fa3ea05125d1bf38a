#!/usr/bin/env python3
"""Registered cel regions on immutable scene plates. FFmpeg, no Python imaging deps."""
import argparse
import json
import math
from pathlib import Path
import shutil
import tempfile

from camera_motion import command, probe, sha256, track, sample


def rect(value, canvas):
    if not isinstance(value, list) or len(value) != 4 or any(type(v) is not int for v in value):
        raise ValueError('Region must be four integer source pixels: x,y,width,height.')
    x,y,w,h = value
    if x < 0 or y < 0 or w <= 0 or h <= 0 or x+w > canvas[0] or y+h > canvas[1]:
        raise ValueError('Region extends outside its scene plate.')
    return value


def intersects(a,b):
    x,y,w,h = a; u,v,s,t = b
    return x < u+s and u < x+w and y < v+t and v < y+h


def check_regions(regions, canvas):
    seen = []
    for r in regions:
        box = rect(r['rect'], canvas)
        if any(intersects(box, other) for other in seen):
            raise ValueError('Movement regions overlap; separate them before compositing.')
        if any(k in r for k in ('scale_x','scale_y','rotation','translate','zoom')):
            raise ValueError('Per-region transforms are locked; animate drawings inside the region.')
        seen.append(box)


def check_camera(keys, protected, frames):
    """Check the actual output samples, after camera edge clamping."""
    for f in range(frames):
        c = sample(keys, f/max(1,frames-1)); half = .5/c['zoom']
        for x,y,w,h in protected:
            if x < c['x']-half-1e-8 or x+w > c['x']+half+1e-8 or y < c['y']-half-1e-8 or y+h > c['y']+half+1e-8:
                raise ValueError(f'Camera clips a protected subject at frame {f}.')


def cell(sheet, columns, rows, index, target, dest):
    """Uniform contain: never squeeze art into an unrelated target aspect ratio."""
    info = probe(sheet); sw,sh=info['width']//columns,info['height']//rows
    w,h = target
    if abs((sw/sh)/(w/h)-1) > .015:
        raise ValueError('Cel and locked region aspect ratios differ by more than 1.5%.')
    if not 0 <= index < columns*rows:
        raise ValueError('Cel index out of range.')
    filt=(f'crop={sw}:{sh}:{index%columns*sw}:{index//columns*sh},'
          f'scale={w}:{h}:force_original_aspect_ratio=decrease:flags=lanczos,'
          f'pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,setsar=1')
    command(['ffmpeg','-v','error','-filter_threads','1','-i',str(sheet),'-vf',filt,'-frames:v','1',str(dest)])


def render(spec_path, output):
    spec_path,output=Path(spec_path).resolve(),Path(output).resolve()
    spec=json.loads(spec_path.read_text()); base=spec_path.parent
    fps=spec.get('fps',60)
    if type(fps) is not int or fps not in (24,30,60):
        raise ValueError('Use 24, 30 or 60 fps.')
    if output.exists():
        raise ValueError('Output exists; use a new take directory.')
    plate=(base/spec['plate']).resolve(); info=probe(plate)
    canvas=[info['width'],info['height']]
    duration=spec['duration']
    if not isinstance(duration,(int,float)) or not math.isfinite(duration) or not 0 < duration <= 60:
        raise ValueError('Duration must be positive and at most 60 seconds.')
    frames=round(duration*fps)
    if frames < 1:
        raise ValueError('Shot must have at least one frame.')
    regions=spec.get('regions',[]); check_regions(regions,canvas)
    output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='scene-build-',dir=output.parent) as tmp:
        build=Path(tmp)/'result'; build.mkdir()
        args=['ffmpeg','-v','error','-filter_complex_threads','1','-loop','1','-framerate',str(fps),'-i',str(plate)]
        graph=['[0:v]format=gbrp,setsar=1[plate]']; last='plate'; manifest=[]
        for i,r in enumerate(regions,1):
            x,y,w,h=r['rect']; name=r['name']; kind=r.get('kind','cels')
            feather=r.get('feather',12)
            if not isinstance(feather,(int,float)) or not 1<=feather<=min(w,h)/2:
                raise ValueError('Invalid feather width.')
            alpha=r.get('mask',f'255*clip(min(min(X,W-1-X),min(Y,H-1-Y))/{feather},0,1)')
            mask_filter=f"format=rgba,geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':a='{alpha}',format=rgba"
            if kind=='cels':
                cels=[(base/p).resolve() for p in r['cels']]
                if not cels:
                    raise ValueError('Empty cel list.')
                for c in cels:
                    p=probe(c)
                    if [p['width'],p['height']] != [w,h]:
                        raise ValueError('Cel size differs from locked region; register it first.')
                timeline=r['timeline']
                if len(timeline)!=frames or any(type(n) is not int or not 0<=n<len(cels) for n in timeline):
                    raise ValueError('Cel timeline must contain one valid index per output frame.')
                seq=build/f'region-{i}'; seq.mkdir()
                registered=build/f'masked-{i}'; registered.mkdir()
                cached=[]
                for idx,c in enumerate(cels):
                    dest=registered/f'{idx:03d}.png'
                    command(['ffmpeg','-v','error','-threads','1','-filter_threads','1','-i',str(c),
                             '-vf',mask_filter,'-frames:v','1','-threads','1',str(dest)])
                    cached.append(dest)
                # Hard links preserve exact source pixels without copying hundreds of drawings.
                for n,idx in enumerate(timeline):
                    try:
                        (seq/f'{n:05d}.png').hardlink_to(cached[idx])
                    except OSError:
                        shutil.copyfile(cached[idx],seq/f'{n:05d}.png')
                args += ['-threads','1','-framerate',str(fps),'-i',str(seq/'%05d.png')]
                graph.append(f'[{i}:v]format=rgba[masked{i}]')
                manifest.append(dict(name=name,rect=r['rect'],drawings=len(cels),hashes=[sha256(c) for c in cels]))
            elif kind=='water':
                # Low-amplitude ripple only within a reviewed, empty-water rectangle.
                shift='2*sin(Y/19+T*PI)+0.7*sin(Y/7-T*2*PI)'
                expr=f'clip(X+({shift}),0,W-1)'
                filt=f"crop={w}:{h}:{x}:{y},format=gbrp,geq=r='r({expr},Y)':g='g({expr},Y)':b='b({expr},Y)',{mask_filter}"
                water=build/f'water-{i}.mkv'
                print(f'Caching {name}',flush=True)
                command(['ffmpeg','-v','error','-threads','1','-filter_threads','1','-loop','1','-framerate',str(fps),
                         '-i',str(plate),'-vf',filt,'-frames:v',str(fps*2),'-c:v','ffv1','-threads','1','-pix_fmt','bgra',str(water)])
                args += ['-threads','1','-stream_loop','-1','-i',str(water)]
                graph.append(f'[{i}:v]format=rgba[masked{i}]')
                manifest.append(dict(name=name,rect=r['rect'],motion='Water-only subpixel ripple; maximum displacement 2.7 source pixels.'))
            else:
                raise ValueError('Unknown region kind.')
            # A region cannot alter pixels outside this fixed mask. Alpha is derived from a
            # static rectangle or the explicitly reviewed mathematical mask in the spec.
            graph.append(f'[{last}][masked{i}]overlay={x}:{y}:format=rgb:shortest=1[out{i}]')
            last=f'out{i}'
        # Native plate dimension can be odd: pad the canvas, never stretch the picture.
        graph.append(f'[{last}]pad=ceil(iw/2)*2:ceil(ih/2)*2:0:0,setsar=1,format=yuv420p[final]')
        (build/'composite.filter.txt').write_text(';'.join(graph))
        command(args+['-filter_complex',';'.join(graph),'-map','[final]','-frames:v',str(frames),'-an',
                      '-c:v','libx264','-threads','2','-preset','veryfast','-crf','15','-movflags','+faststart',str(build/'scene.mp4')],timeout=1800)
        measured=json.loads(command(['ffprobe','-v','error','-count_frames','-select_streams','v:0',
                                     '-show_entries','stream=nb_read_frames','-of','json',str(build/'scene.mp4')]))
        if int(measured['streams'][0]['nb_read_frames']) != frames:
            raise ValueError('Incomplete scene render: decoded frame count differs from timeline.')
        report=dict(plate=str(plate),plate_sha256=sha256(plate),canvas=canvas,frames=frames,fps=fps,duration=frames/fps,regions=manifest,
                    limits='Pixel containment and uniform registration are enforced. Drawing anatomy still requires visual review.')
        (build/'manifest.json').write_text(json.dumps(report,indent=2))
        (build/'source-spec.json').write_text(spec_path.read_text())
        build.replace(output)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('spec',type=Path); parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(render(args.spec,args.out),indent=2))
