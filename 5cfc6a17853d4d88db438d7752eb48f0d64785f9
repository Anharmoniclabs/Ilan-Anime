from pathlib import Path
import json,subprocess,hashlib
import numpy as np
from PIL import Image,ImageDraw
R=Path('/home/alabs/Projects/Ilan-Anime');D=R/'production/runs/episode1-picture-motion/tasks/editorial-motion';O=Path(__file__).parent/'editorial-review';O.mkdir(exist_ok=True)
checks=[]
for shot,n in [('S00-01',96),('S00-02',120),('S02-01',288),('S01-15',96),('S15-09',192)]:
 p=D/shot/'native-v1/preview.mp4'; meta=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(p)]));v=next(s for s in meta['streams'] if s['codec_type']=='video');w,h=v['width'],v['height']; proc=subprocess.Popen(['ffmpeg','-v','error','-i',str(p),'-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
 frames=[];means=[];diff=[];hashes=[];last=None; samples=set([0,3,12,24,48,60,71,72,90,n-1]) if shot!='S02-01' else set([0,24,48,72,96,120,144,168,192,216,240,287]);thumbs=[];i=0
 while True:
  b=proc.stdout.read(w*h*3)
  if not b:break
  assert len(b)==w*h*3
  a=np.frombuffer(b,dtype=np.uint8).reshape(h,w,3);means.append(float(a.mean()));hashes.append(hashlib.sha256(b).hexdigest());diff.append(0 if last is None else float(np.abs(a.astype(float)-last).mean()));last=a.astype(float)
  if i in samples:
   im=Image.fromarray(a);im.save(O/f'{shot}-{i:03}.png');im.thumbnail((480,270));thumbs.append((i,im))
  i+=1
 proc.wait(); assert proc.returncode==0
 sheet=Image.new('RGB',(960,300*((len(thumbs)+1)//2)),(20,20,20));dr=ImageDraw.Draw(sheet)
 for j,(f,im) in enumerate(thumbs):x=(j%2)*480;y=(j//2)*300;dr.text((x+5,y+5),f'{shot} frame {f}',fill='white');sheet.paste(im,(x,y+25))
 sheet.save(O/f'{shot}-sheet.jpg')
 checks.append({'shot':shot,'path':str(p.relative_to(R)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'native_project':str((D/shot/'native-v1/shot.ecproj').relative_to(R)),'native_sha256':hashlib.sha256((D/shot/'native-v1/shot.ecproj').read_bytes()).hexdigest(),'decoded_frames':i,'expected_frames':n,'dimensions':[w,h],'fps':v['r_frame_rate'],'audio_stream_count':sum(s['codec_type']=='audio' for s in meta['streams']),'unique_decoded_frames':len(set(hashes)),'mean_min':min(means),'mean_max':max(means),'max_adjacent_mean_abs_difference':max(diff),'all_decoded_black':max(means)==0,'sheet':str((O/f'{shot}-sheet.jpg').relative_to(R)),'frame_mean':means,'frame_difference':diff})
(O/'decode-checks.json').write_text(json.dumps(checks,indent=2)+'\n');print([(x['shot'],x['decoded_frames'],x['unique_decoded_frames'],x['mean_min'],x['mean_max']) for x in checks])
