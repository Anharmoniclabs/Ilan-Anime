from pathlib import Path
from PIL import Image,ImageDraw
import subprocess,json,hashlib,numpy as np
from studio.craft import Session
from studio.paths import ROOT
P=Path(__file__).resolve().parent
v=P/'S01-03-three-losses-r2-silent.mp4'
subprocess.run(['ffmpeg','-v','error','-y','-framerate','24','-i',str(P/'native/%06d.png'),'-c:v','libx264','-crf','16','-pix_fmt','yuv420p','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-an',str(v)],check=True)
subprocess.run(['ffmpeg','-v','error','-i',str(v),str(P/'decoded/%06d.png')],check=True)
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(v)]));(P/'probe.json').write_text(json.dumps(probe,indent=2))
for page in range(8):
 s=Image.new('RGB',(1280,1176))
 for slot in range(24):
  f=page*24+slot;im=Image.open(P/'decoded'/f'{f+1:06}.png').resize((320,180));x=slot%4*320;y=slot//4*196;s.paste(im,(x,y));ImageDraw.Draw(s).text((x+4,y+181),f'frame {f}',fill='white')
 s.save(P/'review'/f'sequential-{page+1:02}.jpg',quality=93)
for name,start,end in [('woman',24,42),('man',57,75),('elder',90,108)]:
 s=Image.new('RGB',(1500,1080))
 for i,f in enumerate(range(start,end+1,3)):
  im=Image.open(P/'decoded'/f'{f+1:06}.png').crop((675,375,1280,690)).resize((750,315));x=i%2*750;y=i//2*270
  im=im.resize((750,250));s.paste(im,(x,y));ImageDraw.Draw(s).text((x+5,y+253),f'{name} fade frame {f}',fill='white')
 s.save(P/'review'/f'fade-{name}.jpg',quality=95)
with Session('effectcraft',ROOT,P/'reopen-evidence') as ec:
 ec.call('open_project',{'path':str(P/'native/shot.ecproj')})
 for f in [0,42,75,108,191]:ec.call('render_frame',{'time':f/24,'path':str(P/f'review/reopened-{f}.png'),'max_side':0,'inline':False})
def arr(p):return np.asarray(Image.open(p).convert('RGB')).astype(int)
checks={'reopen_max_pixel_difference':{str(f):int(np.abs(arr(P/'native'/f'{f:06}.png')-arr(P/f'review/reopened-{f}.png')).max()) for f in [0,42,75,108,191]},'source_integrity':[{'path':r['path'],'unchanged':hashlib.sha256(Path(r['path']).read_bytes()).hexdigest()==r['sha256']} for r in json.loads((P/'source-hashes.json').read_text())]}
O=P.parent/'three-losses'
checks['after_losses_matches_prior_verified_frames']=all(np.array_equal(arr(P/'native'/f'{f:06}.png'),arr(O/'native-review'/f'{f:06}.png')) for f in range(108,192))
checks['protected_living_and_front_hull_max_delta']={str(f):{'living':int(np.abs(arr(P/'native'/f'{f:06}.png')[:650,:680]-arr(O/'native-review'/f'{f:06}.png')[:650,:680]).max()),'front_hull':int(np.abs(arr(P/'native'/f'{f:06}.png')[680:]-arr(O/'native-review'/f'{f:06}.png')[680:]).max())} for f in [0,24,42,57,75,90,108]}
checks['frame_count']=int(probe['streams'][0]['nb_read_frames']);checks['fps']=probe['streams'][0]['r_frame_rate'];checks['audio_streams']=sum(s['codec_type']=='audio' for s in probe['streams'])
(P/'verification.json').write_text(json.dumps(checks,indent=2))
print(json.dumps(checks,indent=2))
