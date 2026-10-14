import json,subprocess,hashlib
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np
O=Path(__file__).resolve().parent
samples={'S00-01':[0,12,24,36,48,60,69,72,73,95],'S00-02':[0,3,12,21,24,25,119],'S02-01':[0,36,69,72,78,102,111,120,129,138,287],'S01-15':[0,48,95],'S15-09':[0,96,191]}
checks=[]
for row in json.loads((O/'shots.json').read_text()):
 sid=row['id'];d=O/sid;n=row['frames']
 probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-of','json',str(d/'preview.mp4')]))
 (d/'probe.json').write_text(json.dumps(probe,indent=2));v=probe['streams'][0]
 assert len(probe['streams'])==1 and v['codec_type']=='video'
 assert (v['width'],v['height'],v['r_frame_rate'],int(v['nb_read_frames']))==(1280,720,'24/1',n)
 assert np.array_equal(np.array(Image.open(d/'reopened-last.png')),np.array(Image.open(d/'frames'/f'{n-1:06d}.png')))
 p=subprocess.Popen(['ffmpeg','-v','error','-i',str(d/'preview.mp4'),'-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
 selected={};grain_std=[];black_max=0
 for f in range(n):
  data=p.stdout.read(1280*720*3);assert len(data)==1280*720*3
  a=np.frombuffer(data,np.uint8).reshape(720,1280,3)
  if f in samples[sid]:selected[f]=Image.fromarray(a)
  grain_std.append(float(a[:100,:100,0].std()))
  if sid in ['S01-15','S15-09']:black_max=max(black_max,int(a.max()))
 assert p.stdout.read()==b'' and p.wait()==0
 if sid in ['S01-15','S15-09']:assert black_max==0
 else:assert min(grain_std)>.1,(sid,min(grain_std))
 sheet=Image.new('RGB',(1280, (len(selected)+1)//2*386),'#252525');dr=ImageDraw.Draw(sheet)
 for i,(f,im) in enumerate(selected.items()):
  x=i%2*640;y=i//2*386;sheet.paste(im.resize((640,360)),(x,y+26));dr.text((x+8,y+6),f'{sid} decoded frame {f}',fill='white')
 sheet.save(d/'decoded-sheet.jpg',quality=95)
 # Native paths remain editable; text and solid are real engine layer types.
 comp=json.loads((d/'native-inspection.json').read_text());types=[l['type'] for l in comp['layers']]
 checks.append({'shot':sid,'frames':n,'fps':'24/1','size':[1280,720],'silent':True,'full_decode':True,'reopened_last_exact':True,'grain_std_range':[min(grain_std),max(grain_std)],'black_max':black_max if sid in ['S01-15','S15-09'] else None,'native_types':types,'decoded_visual_samples':samples[sid]})
(O/'verification.json').write_text(json.dumps(checks,indent=2))
print(json.dumps(checks,indent=2))
