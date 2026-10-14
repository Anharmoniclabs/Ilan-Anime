#!/usr/bin/env python3
"""A local multiplane pass: a transparent fleet travels across a painted river."""
import argparse
import csv
import json
import math
from pathlib import Path
import shutil
import tempfile

from camera_motion import command, probe, sha256


def positions(spec, frame):
    total=round(spec['duration']*spec['fps'])
    p=frame/max(1,total-1)
    camera=spec['camera_pan']*p
    world=spec['boat_start_x']+spec['boat_travel']*p
    return dict(frame=frame,seconds=frame/spec['fps'],camera_x=camera,
                boat_world_x=world,boat_screen_x=world-camera,
                boat_screen_y=spec['boat_y']+spec['bob_pixels']*math.sin(2*math.pi*(frame/spec['fps'])/3.6))


def validate(spec):
    for key in ('duration','fps','camera_pan','boat_start_x','boat_travel','boat_y','bob_pixels','fleet_width'):
        value=spec[key]
        if type(value) not in (int,float) or not math.isfinite(value):
            raise ValueError(f'{key} must be a finite number.')
    if spec['fps']!=24 or not 0 < spec['duration'] <= 30:
        raise ValueError('Use a 24fps shot lasting at most 30 seconds.')
    if not 0 <= spec['camera_pan'] <= 116 or not 200 <= spec['fleet_width'] <= 1200:
        raise ValueError('Camera exceeds painted overscan or fleet scale is invalid.')
    if not 0 <= spec['bob_pixels'] <= 5:
        raise ValueError('Heave must stay within five pixels.')
    for frame in range(round(spec['duration']*24)):
        p=positions(spec,frame)
        if p['boat_screen_x'] < 0 or p['boat_screen_x']+spec['fleet_width'] > 1280:
            raise ValueError('Fleet would leave the frame.')


def render(spec_path, output):
    spec_path,output=Path(spec_path).resolve(),Path(output).resolve()
    spec=json.loads(spec_path.read_text());validate(spec)
    base=spec_path.parent; bg=(base/spec['background']).resolve();fleet=(base/spec['fleet']).resolve()
    if output.exists():raise ValueError('Use a new output directory.')
    info=probe(fleet); width=spec['fleet_width']; height=round(width*info['height']/info['width'])
    # Image alpha is mandatory; an opaque rectangular image cannot become a boat layer.
    pixel=json.loads(command(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=pix_fmt','-of','json',str(fleet)]))['streams'][0]['pix_fmt']
    if pixel not in ('rgba','bgra','argb','abgr','yuva420p','gbrap'):
        raise ValueError('Fleet must have an alpha channel.')
    fps=spec['fps'];count=round(spec['duration']*fps);duration=count/fps
    if spec['boat_y']+spec['bob_pixels']+height > 900:
        raise ValueError('Fleet canvas placement is too low.')
    output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='vintage-build-',dir=output.parent) as tmp:
        result=Path(tmp)/'result';result.mkdir()
        painted=result/'painted-background.png'
        command(['ffmpeg','-v','error','-threads','1','-filter_threads','1','-i',str(bg),'-vf',
                 'scale=1408:792:force_original_aspect_ratio=increase:flags=lanczos,crop=1408:792,setsar=1',
                 '-frames:v','1',str(painted)])
        print('Rendering a looping river-surface layer',flush=True)
        ripple=result/'water-loop.mkv'
        shift='2.4*sin(Y/17+PI*T)+0.8*sin(Y/8-2*PI*T)'
        # Only open water below the bank; a static upper edge joins the painted plate.
        coord=f'clip(X+({shift})*clip(Y/24,0,1),0,W-1)'
        water=f"crop=1408:240:0:552,format=yuv444p,geq=lum='lum({coord},Y)':cb='cb({coord},Y)':cr='cr({coord},Y)'"
        command(['ffmpeg','-v','error','-threads','1','-filter_threads','1','-loop','1','-framerate',str(fps),
                 '-i',str(painted),'-vf',water,'-frames:v',str(fps*2),'-c:v','ffv1','-threads','1',str(ripple)])
        # Work at 2x resolution so translations can advance by half an output pixel.
        p=f'min(t/{(count-1)/fps},1)'
        camera=f'24+{2*spec["camera_pan"]}*({p})'
        x=f'{2*spec["boat_start_x"]}+{2*(spec["boat_travel"]-spec["camera_pan"])}*({p})'
        y=f'{2*spec["boat_y"]}+{2*spec["bob_pixels"]}*sin(2*PI*t/3.6)'
        graph=(f'[0:v][1:v]overlay=0:552:format=auto[river];'
               f"[river]scale=2816:1584:flags=lanczos,crop=2560:1440:x='{camera}':y=80[world];"
               f'[2:v]scale={2*width}:-1:flags=lanczos,format=rgba[cel];'
               f"[world][cel]overlay=x='{x}':y='{y}':eval=frame:format=auto,"
               'scale=1280:720:flags=lanczos,setsar=1,format=yuv420p,'
               'noise=c0s=2:c0f=t+u:c0_seed=1994[film]')
        (result/'motion.filter.txt').write_text(graph)
        print('Rendering boat travel and tracking camera',flush=True)
        command(['ffmpeg','-v','error','-filter_complex_threads','1','-threads','1','-loop','1','-framerate',str(fps),'-i',str(painted),
                 '-threads','1','-stream_loop','-1','-i',str(ripple),'-threads','1','-loop','1','-framerate',str(fps),'-i',str(fleet),
                 '-filter_complex',graph,'-map','[film]','-frames:v',str(count),'-an','-c:v','libx264','-threads','2',
                 '-preset','veryfast','-crf','17','-movflags','+faststart',str(result/'animation.mp4')],timeout=900)
        measured=json.loads(command(['ffprobe','-v','error','-count_frames','-select_streams','v:0',
                         '-show_entries','stream=width,height,nb_read_frames,avg_frame_rate,duration','-of','json',str(result/'animation.mp4')]))['streams'][0]
        if int(measured['nb_read_frames'])!=count or measured['avg_frame_rate']!='24/1':raise ValueError('Incomplete render.')
        rows=[positions(spec,n) for n in range(count)]
        with (result/'motion.csv').open('w') as f:
            writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
        report=dict(style='Quiet 1990s cel-anime travel shot',measured=measured,
                    camera_pan_pixels=spec['camera_pan'],boat_world_travel_pixels=spec['boat_travel'],
                    boat_screen_travel_pixels=rows[-1]['boat_screen_x']-rows[0]['boat_screen_x'],
                    background_sha256=sha256(bg),fleet_sha256=sha256(fleet),
                    method='Held transparent fleet cel, continuous world travel, independent background pan, gentle heave, looping water surface, light luma grain. No earlier action-cycle frames.',
                    limitation='Passenger poses are held. All three boats share one travel layer; this pass does not add character performance or independent boat pitching.')
        (result/'manifest.json').write_text(json.dumps(report,indent=2))
        shutil.copyfile(spec_path,result/'source-spec.json')
        command(['ffmpeg','-v','error','-i',str(result/'animation.mp4'),'-frames:v','1',str(result/'poster.png')])
        result.rename(output)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('spec',type=Path);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();print(json.dumps(render(a.spec,a.out),indent=2))
