import json,subprocess,os
from pathlib import Path
from PIL import Image,ImageDraw
R=Path.cwd();O=R/'production/runs/episode1-full-picture/reviews/episode-wiring';t=json.loads((R/'production/runs/episode1-full-picture/tasks/episode-wiring/timeline.json').read_text())
for r in t['shots']:
 if not r['draft']:continue
 d=O/'render-qa'/r['shot'];d.mkdir(parents=True,exist_ok=True)
 subprocess.run(['ffmpeg','-v','error','-i',str(R/r['draft']['path']),'-vf','scale=320:180',str(d/'frame-%04d.png')],check=True)
 frames=sorted(d.glob('frame-*.png'));assert len(frames)==r['frames']
 spec={'id':r['shot'],'size':[320,180],'frames':r['frames'],'fps':24,'layers':[{'name':'decoded-inspection','source':str(frames[0]),'rate':1,'exposures':[{'start':i,'end':i+1,'source':str(p)} for i,p in enumerate(frames)]}],'camera':[],'post':{}}
 (d/'shot.json').write_text(json.dumps(spec))
 p=subprocess.run([str(R/'.venv/bin/python'),'-m','studio','qa',str(d/'shot.json'),'--render',str(R/r['draft']['path']),'--out',str(d/'qa'),'--scale','1'],capture_output=True,text=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'});(d/'qa-command.txt').write_text(p.stdout+p.stderr)
 selected=sorted(set([0,len(frames)//4,len(frames)//2,3*len(frames)//4,len(frames)-1]))
 sheet=Image.new('RGB',(320*len(selected),204));draw=ImageDraw.Draw(sheet)
 for j,i in enumerate(selected):
  sheet.paste(Image.open(frames[i]),(j*320,24));draw.text((j*320+5,5),f'{r["shot"]} f{i} {i/24:.3f}s',fill='white')
 sheet.save(d/'samples.jpg')
 print(r['shot'],p.returncode,flush=True)
