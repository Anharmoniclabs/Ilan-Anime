from pathlib import Path
import json,subprocess,hashlib
from PIL import Image,ImageDraw
import numpy as np
p=Path(__file__).resolve().parent
v=p/'S01-03-partial-silent-v2.mp4'
subprocess.run(['ffmpeg','-v','error','-n','-framerate','24','-start_number','0','-i',str(p/'native-continuous-camera/%06d.png'),'-frames:v','192','-an','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709',str(v)],check=True)
(p/'decoded-v2').mkdir();(p/'review-v2').mkdir()
subprocess.run(['ffmpeg','-v','error','-i',str(v),'-start_number','0',str(p/'decoded-v2/%06d.png')],check=True)
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-of','json',str(v)]));(p/'probe-v2.json').write_text(json.dumps(probe,indent=2))
assert len(probe['streams'])==1
s=probe['streams'][0];assert (s['width'],s['height'],s['r_frame_rate'],s['nb_read_frames'])==(1280,720,'24/1','192')
for page in range(8):
 sheet=Image.new('RGB',(1280,1180))
 for i,f in enumerate(range(page*24,(page+1)*24)):
  im=Image.open(p/'decoded-v2'/f'{f:06d}.png');x=(i%4)*320;y=(i//4)*196;sheet.paste(im.resize((320,180)),(x,y));ImageDraw.Draw(sheet).text((x+4,y+180),f'{f:03d}',fill='white')
 sheet.save(p/'review-v2'/f'decoded-sequential-{page+1:02d}.jpg')
for page in range(4):
 sheet=Image.new('RGB',(1200,1200))
 for i,f in enumerate(range(page*48,(page+1)*48,3)):
  t=f/191;z=1.15+.7*t;px=720.5+308*t;py=408.3+192.2*t
  box=(px+(320*1280/1672-640)*z,py+(90*720/941-360)*z,px+(655*1280/1672-640)*z,py+(390*720/941-360)*z)
  im=Image.open(p/'decoded-v2'/f'{f:06d}.png').crop(box).resize((300,280));x=(i%4)*300;y=(i//4)*300;sheet.paste(im,(x,y));ImageDraw.Draw(sheet).text((x+4,y+280),f'{f:03d}',fill='white')
 sheet.save(p/'review-v2'/f'decoded-acting-{page+1:02d}.jpg')
# Reconcile studio camera to native linear position/scale at all 192 sample times.
m=json.load(open(p/'motion.json'));keys=[]
for f in range(192):
 t=f/191;z=1.15+.7*t;keys.append({'frame':f,'scale':z,'x':(80.5+308*t)/z,'y':(48.3+192.2*t)/z})
m['camera']=keys;(p/'motion.json').write_text(json.dumps(m,indent=2));(p/'camera.json').write_text(json.dumps({'native_key_time':'seconds relative to each exposure in-point','native_position_keys':[[0,720.5,408.3],[191,1028.5,600.5]],'native_scale_percent':[115,185],'studio_sampled_keys':keys},indent=2))
# Check source immutability against snapshot hashes.
checks=[]
for item in json.load(open(p/'source-provenance.json')):
 checks.append({'path':item['path'],'unchanged':hashlib.sha256(Path(item['path']).read_bytes()).hexdigest()==item['sha256']})
assert all(c['unchanged'] for c in checks)
(p/'source-integrity.json').write_text(json.dumps(checks,indent=2))
print('Verified 192 frames, 24 fps, 1280x720, no audio; raw source hashes unchanged.')
