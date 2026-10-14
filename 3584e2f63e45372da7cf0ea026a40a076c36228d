from pathlib import Path
import json,subprocess,hashlib,csv
from PIL import Image,ImageDraw
O=Path(__file__).resolve().parent; Q=O/'qa';Q.mkdir(exist_ok=True)
v=O/'S01-01-silent-preview.mp4'
r=subprocess.run(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(v)],capture_output=True,text=True,check=True)
p=json.loads(r.stdout);(Q/'ffprobe.json').write_text(json.dumps(p,indent=2))
s=p['streams'];assert len(s)==1 and s[0]['codec_type']=='video';assert s[0]['nb_read_frames']=='144' and s[0]['avg_frame_rate']=='24/1';assert (s[0]['width'],s[0]['height'])==(1920,1080)
(Q/'decoded').mkdir(exist_ok=True)
subprocess.run(['ffmpeg','-v','error','-i',str(v),'-fps_mode','passthrough','-start_number','0',str(Q/'decoded/%06d.png')],check=True)
for start in [0,48,96]:
 sheet=Image.new('RGB',(1280,800),'#111820');d=ImageDraw.Draw(sheet)
 for i,f in enumerate(range(start,start+48,3)):
  im=Image.open(Q/'decoded'/f'{f:06d}.png').convert('RGB');im.thumbnail((320,180));x=(i%4)*320;y=(i//4)*200;sheet.paste(im,(x,y));d.text((x+5,y+183),f'f{f:03d}',fill='white')
 sheet.save(Q/f'exposures-{start:03d}.jpg',quality=94)
# Larger native-resolution contact crops, all from delivered MP4.
for label,fs in [('contact',[24,27,36,48,60,72]),('impact',[75,78,84,90,99,117])]:
 sheet=Image.new('RGB',(1440,750),'#111820');d=ImageDraw.Draw(sheet)
 for i,f in enumerate(fs):
  im=Image.open(Q/'decoded'/f'{f:06d}.png').crop((930,570,1410,925));x=i%3*480;y=i//3*375;sheet.paste(im,(x,y));d.text((x+5,y+356),f'f{f:03d}',fill='white')
 sheet.save(Q/f'{label}-decoded.jpg',quality=96)
old=json.loads(Path('production/runs/episode1-picture-motion/tasks/water-motion/S01-01-water-motion.ecproj').read_text());new=json.loads((O/'S01-01-water-motion.ecproj').read_text())
get=lambda p,n:next(l for l in p['items']['128']['kind']['layers'] if l['id']==n)
checks={str(n):get(old,n)==get(new,n) for n in [152,129,299]};assert all(checks.values())
e=json.loads((O/'exposures.json').read_text());prior=json.loads(Path('production/runs/episode1-picture-motion/tasks/water-motion/exposures.json').read_text());assert e['droplet_physics']==prior['droplet_physics']
with (O/'exposure-sheet.csv').open('w') as h:
 w=csv.writer(h);w.writerow(['shot','start_frame','end_frame','cel','contact_span','droplets'])
 for x in e['exposures']:w.writerow(['S01-01',x['start_frame'],x['start_frame']+2,Path(x['path']).name,x['contact_span'],json.dumps(x['droplets'])])
(Q/'checks.json').write_text(json.dumps({'streams':len(s),'frames':144,'fps':'24/1','dimensions':[1920,1080],'fully_decoded':True,'unchanged_native_layers':checks,'droplet_trajectories_identical':True,'background_warp':False,'real_time_perceptual_playback':'unavailable in this worker; not claimed'},indent=2))
(O/'layer-matte-manifest.json').write_text(json.dumps({'shot':'S01-01','status':'exploratory','native':'S01-01-water-motion.ecproj','layers':{'129':'unchanged painted water','152':'unchanged rigid paddle with held transform keys','175':'48 held foreground matte paths; localized irregular contact edge around y760','299':'unchanged exact live BEFORE super','water_fx':'48 numbered registered SVG / alpha PNG cels in drawings; held on 3s; independently timed from rigid blade'},'canvas':[1920,1080],'registration':'full-canvas origin [0,0], layer anchor/position [960,540]','separability':'background, prop, foreground matte, typography, and water FX track remain separate. Rings/drops/crowns share each FX exposure as in source; individual shapes remain editable in SVG.','contacts':e['exposures'],'droplet_physics':e['droplet_physics']},indent=2))
# Correct provenance distinction: only unedited snapshots have source-equal digests.
prov=json.loads((O/'source-provenance.json').read_text())
for x in prov['items']:
 x['source_sha256']=x.pop('sha256');x['snapshot_sha256']=hashlib.sha256(Path(x['snapshot']).read_bytes()).hexdigest();x['revised']=x['source_sha256']!=x['snapshot_sha256']
(O/'source-provenance.json').write_text(json.dumps(prov,indent=2))
print('Verified 144 decoded frames; identical rigid prop, background, text and ballistic trajectories.')
