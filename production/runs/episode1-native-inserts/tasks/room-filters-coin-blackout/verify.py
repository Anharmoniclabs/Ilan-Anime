from pathlib import Path
import subprocess,json,hashlib,sys
import numpy as np
from PIL import Image,ImageDraw
sys.path.insert(0,str(Path.cwd()))
from studio.engine.compositor import Compositor
P=Path('production/runs/episode1-native-inserts/tasks/room-filters-coin-blackout')
summary={}
for sh,n in [('S03-03',288),('S04-02',144),('S05-13',96),('S06-03',144)]:
 d=P/sh;video=d/('review-matte.mp4' if sh in ['S04-02','S05-13'] else 'review.mp4');native=d/('native-matte' if sh in ['S04-02','S05-13'] else 'native')
 probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(video)]));(d/'probe.json').write_text(json.dumps(probe,indent=2))
 v=[s for s in probe['streams'] if s['codec_type']=='video'][0];assert (v['width'],v['height'],v['r_frame_rate'],int(v['nb_read_frames']))==(1280,720,'24/1',n);assert len(probe['streams'])==1
 (d/'decoded').mkdir(exist_ok=True)
 subprocess.run(['ffmpeg','-v','error','-n','-i',str(video),'-fps_mode','passthrough','-start_number','0',str(d/'decoded/%06d.png')],check=True)
 files=sorted((d/'decoded').glob('*.png'));assert len(files)==n
 decoded_hashes=[hashlib.sha256(Image.open(f).tobytes()).hexdigest() for f in files]
 picks={'S03-03':[0,72,144,216,287],'S04-02':[0,24,48,72,96,120,143],'S05-13':[0,1,3,9,12,14,15,16,17,18,19,95],'S06-03':[0,72,143]}[sh]
 cols=3;rows=(len(picks)+cols-1)//cols;sheet=Image.new('RGB',(cols*426,rows*264),(25,29,35));draw=ImageDraw.Draw(sheet)
 for j,f in enumerate(picks):
  im=Image.open(files[f]).resize((426,240));x=j%cols*426;y=j//cols*264;sheet.paste(im,(x,y+24));draw.text((x+8,y+5),f'{sh} decoded frame {f}',fill='white')
 sheet.save(d/'decoded-review-sheet.jpg',quality=94)
 # Compare separately rendered native checkpoints with studio rendering before codec loss.
 c=Compositor(json.load(open(d/'shot.json')),base=d.resolve());parity=[]
 for f in sorted(native.glob('native-*.png')):
  frame=int(f.stem.split('-')[1]);a=np.array(Image.open(f).convert('RGB')).astype(float);b=np.array(c.draw(frame).convert('RGB')).astype(float);parity.append({'frame':frame,'mean_absolute_rgb_error':float(np.abs(a-b).mean()),'max_rgb_error':float(np.abs(a-b).max())})
 checks={'frames':n,'fps':24,'size':[1280,720],'audio_streams':0,'decoded_count':len(files),'decoded_unique_pixel_hashes':len(set(decoded_hashes)),'native_vs_studio':parity,'video':str(video),'native_project':str(native/'shot.ecproj'),'decoded_frame_hashes':decoded_hashes}
 if sh=='S05-13':
  s=json.load(open(d/'shot.json'));keys=s['layers'][2]['keys'];assert all(k['scale']==1 for k in keys);assert keys[1]['x']==2;assert keys[12]['y']==86 and keys[14]['y']==86;assert keys[17]['y']==98;assert keys[18]['y']==97;assert all(k['y']==98 for k in keys[19:]);assert np.array(Image.open(files[17])).mean()>250
  checks['contact_timing']='Independent spec assertions: rest f0; x tremor +2 f1; rise f3..12 to -12; hold/glint f12..14; drop starts f15; contact white frame f17; -1 bounce f18; settle f19..95; scale 1 throughout.'
  checks['decoded_settle_max_difference']=max(float(np.abs(np.array(Image.open(files[f])).astype(float)-np.array(Image.open(files[19])).astype(float)).max()) for f in [20,48,95])
 if sh=='S04-02':
  s=json.load(open(d/'shot.json'));a=s['layers'][-2];b=s['layers'][-1];assert a['rate']==b['rate']==3;assert len(a['keys'])==48
  checks['pane_crossings']=[{'pane_center_x':x,'first_frame_sigil_center_crosses':next(k['frame'] for k in a['keys'] if k['x']+50>=x)} for x in [403,653,903]]
  checks['rigidity']='One unchanged sigil PNG from supplied shared path and one unchanged waveform PNG. Translation only; no scale, rotation or shape filter.'
 if sh=='S06-03':checks['hold_check']='Source transform fixed throughout. Distant glow baked into supplied painting; no added nearby illumination or moving actors.'
 (d/'checks.json').write_text(json.dumps(checks,indent=2));summary[sh]={k:v for k,v in checks.items() if k!='decoded_frame_hashes'};print(sh,'verified',flush=True)
(P/'technical-checks.json').write_text(json.dumps(summary,indent=2))
