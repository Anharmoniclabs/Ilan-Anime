from pathlib import Path
from PIL import Image,ImageDraw
import subprocess,json,hashlib,collections
out=Path(__file__).resolve().parent
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-of','json',str(out/'preview.mp4')]))
streams=probe['streams'];v=streams[0]
assert len(streams)==1 and v['codec_type']=='video'
assert (v['width'],v['height'],v['r_frame_rate'],int(v['nb_read_frames']))==(1280,720,'24/1',384)
assert float(v['duration'])==16
(out/'probe.json').write_text(json.dumps(probe,indent=2))
dec=out/'decoded';dec.mkdir(exist_ok=True)
subprocess.run(['ffmpeg','-v','error','-i',str(out/'preview.mp4'),'-fps_mode','passthrough','-start_number','0',str(dec/'%06d.png')],check=True)
assert len(list(dec.glob('*.png')))==384
native=json.loads((out/'native-r1/shot.ecproj').read_text());comp=next(x['kind'] for x in native['items'].values() if x['kind']['type']=='Comp');layers=comp['layers'];types=collections.Counter(l['source']['type'] for l in layers)
assert len(layers)==158 and types['Text']>20 and types.get('Footage',0)==0
assert comp['width']==1280 and comp['height']==720 and comp['frame_rate']=={'num':24,'den':1}
obj=json.loads((out/'objects.json').read_text())['objects']
assert all(o['start']%3==0 and o['end']%3==0 for o in obj)
assert len([o for o in obj if o['category']=='tab'])==11
assert len([o for o in obj if o['category']=='building'])==4
changes=[];prev=None
for f in range(0,384,3):
 b=(out/'frames'/f'{f:06d}.png').read_bytes();h=hashlib.sha256(b).hexdigest()
 assert all((out/'frames'/f'{f+n:06d}.png').read_bytes()==b for n in [1,2])
 if h!=prev:changes.append(f)
 prev=h
samples=changes+[383]
review=out/'review-frames';review.mkdir(exist_ok=True)
for page in range((len(samples)+11)//12):
 sheet=Image.new('RGB',(1152,960),'#162430');d=ImageDraw.Draw(sheet)
 for i,f in enumerate(samples[page*12:(page+1)*12]):
  im=Image.open(dec/f'{f:06d}.png').resize((384,216));x=(i%3)*384;y=(i//3)*240
  sheet.paste(im,(x,y));d.text((x+8,y+220),f'local f{f:03d} / episode f{21792+f}',fill='white')
 sheet.save(review/f'decoded-states-{page+1:02d}.jpg',quality=95)
sheet=Image.new('RGB',(1000,600),'#162430');d=ImageDraw.Draw(sheet)
for i,f in enumerate(range(96,141,3)):
 im=Image.open(dec/f'{f:06d}.png').crop((420,308,590,411)).resize((200,121));x=(i%5)*200;y=(i//5)*200
 sheet.paste(im,(x,y));d.text((x+8,y+158),f'f{f:03d} through f{f+2:03d}',fill='white')
sheet.save(review/'lunch-drawings.jpg',quality=96)
# Timeline exports reviewed separately; no static read hold represents acting.
report={'shot':'S14-03','start_frame':21792,'frames':384,'fps':24,'duration_seconds':16,'size':[1280,720],'audio_streams':0,'full_decode_frames':384,'native_layer_count':len(layers),'native_source_types':dict(types),'tabs':11,'buildings':4,'pin_tracks':4,'transformation_drawings':15,'cadence':3,'all_authored_boundaries_on_threes':True,'distinct_exposure_states':len(changes),'decoded_state_frames':samples,'sha256':{p:hashlib.sha256((out/p).read_bytes()).hexdigest() for p in ['native-r1/shot.ecproj','preview.mp4','edit.filmcraft']},'status':'exploratory; independent creative review pending'}
(out/'verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
