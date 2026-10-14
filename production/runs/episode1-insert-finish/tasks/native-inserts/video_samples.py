from pathlib import Path
import subprocess,json,hashlib
from PIL import Image,ImageDraw
O=Path(__file__).resolve().parent; P=Path('production/runs/episode1-native-inserts/tasks/room-filters-coin-blackout')
checks=[]
for shot,name,frames in [('S03-03','review.mp4',288),('S04-02','review-matte.mp4',144),('S05-13','review-matte.mp4',96),('S06-03','review.mp4',144),('S05-13-repaired','review.mp4',96)]:
 clip=O/'S05-13'/name if shot.endswith('repaired') else P/shot/name
 if not clip.exists(): continue
 picks=[0,1,3,9,12,14,15,16,17,18,19,95] if 'S05' in shot else ([0,24,48,72,96,120,143] if frames==144 else [0,72,144,216,287])
 probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(clip)])); v=probe['streams'][0]
 assert len(probe['streams'])==1 and int(v['nb_frames'])==frames and v['r_frame_rate']=='24/1' and (v['width'],v['height'])==(1280,720)
 proc=subprocess.Popen(['ffmpeg','-v','error','-i',str(clip),'-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
 sheet=Image.new('RGB',(960,((len(picks)+1)//2)*294),(24,24,24)); draw=ImageDraw.Draw(sheet); i=0
 while True:
  raw=proc.stdout.read(1280*720*3)
  if not raw: break
  assert len(raw)==1280*720*3
  if i in picks:
   im=Image.frombytes('RGB',(1280,720),raw); k=picks.index(i); sheet.paste(im.resize((480,270)),((k%2)*480,(k//2)*294+24)); draw.text(((k%2)*480+6,(k//2)*294+6),f'{shot} decoded f{i}',fill='white')
   if 'repaired' in shot and i in [0,12,16,18,19]: im.crop((470,370,780,560)).resize((930,570)).save(O/f'coin-detail-{i}.png')
  i+=1
 assert proc.wait()==0 and i==frames
 sheet.save(O/f'{shot}-decoded.jpg',quality=94)
 checks.append({'shot':shot,'clip':str(clip),'sha256':hashlib.sha256(clip.read_bytes()).hexdigest(),'decoded_frames':i,'fps':24,'size':[1280,720],'audio_streams':0,'sampled_frames':picks})
(O/'video-checks.json').write_text(json.dumps(checks,indent=2))
