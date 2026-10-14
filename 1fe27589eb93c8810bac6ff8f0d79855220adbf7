#!/usr/bin/env python3
"""Assemble generated animation cels with an animator's exposure sheet.

This is the local compositor, not an image generation model. Artwork is supplied
by imagegen in the conversation, or by the user. No network, API key or GPU.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile


def run(args):
    result = subprocess.run(args, capture_output=True, text=True, timeout=240)
    if result.returncode:
        raise ValueError(result.stderr[-2000:])
    return result.stdout


def dimensions(path):
    data = json.loads(run(['ffprobe','-v','error','-select_streams','v:0',
                           '-show_entries','stream=width,height','-of','json',str(path)]))
    return data['streams'][0]['width'], data['streams'][0]['height']


def validate(spec, base):
    if spec.get('fps',24) not in (12,24,30):
        raise ValueError('Use a 12, 24 or 30 fps timeline.')
    if not spec.get('shots'):
        raise ValueError('At least one shot is required.')
    for shot in spec['shots']:
        rows,cols = shot.get('rows',4),shot.get('columns',4)
        if type(rows) is not int or type(cols) is not int or not 1 <= rows*cols <= 256:
            raise ValueError('Grid must contain 1–256 cells.')
        path = (base/shot['sheet']).resolve()
        if not path.is_file():
            raise ValueError(f'Missing sheet: {path}')
        exposure = shot.get('exposures',[])
        if not exposure:
            raise ValueError('Specify the drawing order and exposures explicitly.')
        for item in exposure:
            if len(item)!=2 or any(type(n) is not int for n in item):
                raise ValueError('Each exposure is [zero-based cell index, timeline frames].')
            cell,hold = item
            if not 0 <= cell < rows*cols or not 1 <= hold <= 48:
                raise ValueError('Invalid cell or exposure length (1–48 frames).')
    if sum(n for s in spec['shots'] for _,n in s['exposures']) > 24*300:
        raise ValueError('Split long projects into smaller sequences.')


def assemble(spec_path, output):
    spec_path=Path(spec_path).resolve()
    output=Path(output).resolve()
    spec=json.loads(spec_path.read_text())
    validate(spec,spec_path.parent)
    if output.exists():
        raise ValueError('Output already exists; use a new take directory.')
    output.parent.mkdir(parents=True,exist_ok=True)
    # Publish only once the sequence, PNGs and metadata are complete.
    with tempfile.TemporaryDirectory(prefix='cel-build-',dir=output.parent) as temp:
        temp=Path(temp)
        cels=temp/'cels';cels.mkdir()
        timeline=temp/'timeline';timeline.mkdir()
        references=temp/'references';references.mkdir()
        fps=spec.get('fps',24)
        width,height=spec.get('size',[640,360])
        if type(width) is not int or type(height) is not int or not (32<=width<=2048 and 32<=height<=2048 and width%2==height%2==0):
            raise ValueError('Output size must be even dimensions between 32 and 2048.')
        records=[];number=0;unique=0
        for si,shot in enumerate(spec['shots']):
            sheet=(spec_path.parent/shot['sheet']).resolve()
            sw,sh=dimensions(sheet)
            cols,rows=shot.get('columns',4),shot.get('rows',4)
            shutil.copy2(sheet,references/f'{si:03d}{sheet.suffix}')
            extracted={}
            for cell,hold in shot['exposures']:
                if cell not in extracted:
                    x0=(cell%cols)*sw//cols;x1=(cell%cols+1)*sw//cols
                    y0=(cell//cols)*sh//rows;y1=(cell//cols+1)*sh//rows
                    target=cels/f'shot-{si+1:02d}-cel-{cell+1:03d}.png'
                    run(['ffmpeg','-v','error','-y','-i',str(sheet),'-vf',
                         f'crop={x1-x0}:{y1-y0}:{x0}:{y0},scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2',
                         '-frames:v','1',str(target)])
                    extracted[cell]=target;unique+=1
                start=number
                for _ in range(hold):
                    number+=1
                    dest=timeline/f'{number:06d}.png'
                    # Separate files make the rendered sequence portable.
                    shutil.copyfile(extracted[cell],dest)
                records.append(dict(shot=si+1,cel=cell+1,start_frame=start,end_frame_exclusive=number,
                                    source_sha256=hashlib.sha256(sheet.read_bytes()).hexdigest()))
        run(['ffmpeg','-v','error','-framerate',str(fps),'-i',str(timeline/'%06d.png'),
             '-c:v','libx264','-crf','17','-pix_fmt','yuv420p','-movflags','+faststart',str(temp/'animation.mp4')])
        run(['ffmpeg','-v','error','-i',str(temp/'animation.mp4'),'-filter_complex',
             '[0:v]split[a][b];[a]palettegen=stats_mode=diff[p];[b][p]paletteuse=dither=sierra2_4a',
             '-loop','0',str(temp/'preview.gif')])
        # Original cels, rather than re-decoded compressed video, form the sheet.
        run(['ffmpeg','-v','error','-pattern_type','glob','-i',str(cels/'*.png'),'-vf',
             f'scale=240:-1,tile=4x{(unique+3)//4}', '-frames:v','1',str(temp/'contact-sheet.png')])
        report=dict(fps=fps,frames=number,drawings=unique,duration=number/fps,size=[width,height],
                    exposures=records,spec=spec,
                    method='Individually generated cel drawings. Exposure holds repeat a drawing; no optical flow, camera transforms or synthesized interpolation.')
        (temp/'exposure-sheet.json').write_text(json.dumps(report,indent=2))
        shutil.copytree(temp,output)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('spec',type=Path)
    parser.add_argument('--out',required=True,type=Path)
    args=parser.parse_args()
    try:
        result=assemble(args.spec,args.out)
        print(json.dumps({k:result[k] for k in ('fps','frames','drawings','duration','method')},indent=2))
        print(args.out.resolve()/'animation.mp4')
    except (ValueError,OSError,subprocess.SubprocessError) as exc:
        parser.exit(1,str(exc)+'\n')
