#!/usr/bin/env python3
"""Prepare registered animation drawings and reproducible first-shot specs."""
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from locked_scene import cell
from camera_motion import command

root=Path(__file__).resolve().parent
gen=root/'generated'; cels=root/'registered-cels'; cels.mkdir(exist_ok=True)

def ff(input, filt, output):
    if not output.exists():
        command(['ffmpeg','-v','error','-filter_threads','1','-i',str(input),'-vf',filt,'-frames:v','1',str(output)])

def prepare():
    for file,cols,rows in [('dairon-keys',2,2),('dairon-betweens',4,2)]:
        for i in range(cols*rows):
            dest=cels/f'{file}-{i}.png'
            if not dest.exists(): cell(gen/(file+'.png'),cols,rows,i,[400,390],dest)
    cycle=[]
    for i in range(4):
        cycle += [f'registered-cels/dairon-keys-{i}.png',f'registered-cels/dairon-betweens-{i*2}.png',f'registered-cels/dairon-betweens-{i*2+1}.png']
    # Two-frame exposures at 24fps; the final camera/export runs at 60fps.
    first=dict(plate='assets/Cemi-River-Scene/03-Keyframes/K01-Three-Canoes.png',duration=8,fps=24,regions=[
        dict(name='Dairon paddle cycle',rect=[1250,360,400,390],cels=cycle,timeline=[(f//2)%12 for f in range(192)],
             mask='255*clip(min(min(X-(60-50*clip((Y-240)/90,0,1)),W-1-X),min(Y-5,H-1-Y))/14,0,1)'),
        dict(name='Foreground water',kind='water',rect=[0,770,1670,170],feather=24)])
    (root/'shot-01.json').write_text(json.dumps(first,indent=2))
    plate=root/'assets/Cemi-River-Scene/03-Keyframes/K02-Amaia-and-Son.png'
    ff(plate,'crop=130:46:525:152',cels/'eyes-original.png')
    for i in [0,1]:
        raw=cels/f'amaia-blink-{i}.png'
        if not raw.exists(): cell(gen/'amaia-blink.png',2,2,i,[500,360],raw)
        # One uniform scale and fixed translation align both eyes to the master painting.
        # Facial features outside these two masks are never replaced.
        ff(raw,'scale=460:332:flags=lanczos,crop=460:328:0:4,pad=500:360:6:0,crop=130:46:165:117',cels/f'eyes-{i}.png')
    timing=[0]*540
    for start in [112,367]:
        timing[start:start+5]=[1]*5
        timing[start+5:start+11]=[2]*6
        timing[start+11:start+16]=[1]*5
    second=dict(plate='assets/Cemi-River-Scene/03-Keyframes/K02-Amaia-and-Son.png',duration=9,fps=60,regions=[
        dict(name='Amaia eyelids',rect=[525,152,130,46],cels=['registered-cels/eyes-original.png','registered-cels/eyes-0.png','registered-cels/eyes-1.png'],timeline=timing,
             mask='255*clip(max(1-sqrt(pow((X-29)/22,2)+pow((Y-21)/14,2)),1-sqrt(pow((X-103)/32,2)+pow((Y-20)/16,2)))*5,0,1)'),
        dict(name='River beside canoe',kind='water',rect=[1120,555,550,230],feather=24)])
    (root/'shot-02.json').write_text(json.dumps(second,indent=2))
    # Preserve supplied composition. K02 already touches the top/bottom frame, so no zoom.
    edit=dict(fps=60,size=[1920,1080],shots=[
        dict(name='Three canoes, eleven survivors',source='shot-01-take-02/scene.mp4',duration=8,fit='match',
             camera=[dict(at=0,zoom=1),dict(at=1,zoom=1.008,x=.501,y=.501)],protected=[[.012,.345,.975,.43]]),
        dict(name='Her son slept against her ribs',source='shot-02-take-01/scene.mp4',duration=9,fit='match',
             camera=[dict(at=0,zoom=1),dict(at=1,zoom=1)],protected=[[0,0,1,1]])])
    (root/'opening-camera.json').write_text(json.dumps(edit,indent=2))

if __name__=='__main__': prepare()
