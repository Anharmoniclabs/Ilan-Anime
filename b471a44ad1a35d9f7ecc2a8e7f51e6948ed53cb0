from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np,json
p=Path('production/runs/episode1-native-inserts/tasks/room-filters-coin-blackout')
def image(d,f):return np.array(Image.open(d/'decoded'/f'{f:06d}.png').convert('RGB')).astype(float)
d=p/'S05-13';base=image(d,0);crop=(560,414,680,470);x,y,r,b=crop;template=base[y:b,x:r];measure=[]
for f in [1,3,9,12,14,15,16,18,19,95]:
 a=image(d,f);scores=[]
 for dy in range(-14,3):
  for dx in range(-3,4):scores.append((float(np.mean(abs(template-a[y+dy:b+dy,x+dx:r+dx]))),dx,dy))
 score,dx,dy=min(scores);measure.append({'frame':f,'measured_dx':dx,'measured_dy':dy,'mean_absolute_error':score})
expected={1:(2,0),3:(0,0),12:(0,-12),14:(0,-12),15:(0,-12),16:(0,-9),18:(0,-1),19:(0,0),95:(0,0)}
assert all((m['measured_dx'],m['measured_dy'])==expected[m['frame']] for m in measure if m['frame'] in expected)
sheet=Image.new('RGB',(1200,600),(20,25,31));dr=ImageDraw.Draw(sheet)
for i,f in enumerate([0,1,12,16,18,19]):
 im=Image.open(d/'decoded'/f'{f:06d}.png').crop((465,370,785,570)).resize((400,250));x=i%3*400;y=i//3*300;sheet.paste(im,(x,y+30));dr.text((x+10,y+10),f'decoded contact crop f{f}',fill='white')
sheet.save(d/'decoded-contact-detail.jpg',quality=96)
# Exact source hold check isolates codec noise from actual authored movement.
from studio.engine.compositor import Compositor
s=json.load(open(d/'shot.json'));c=Compositor(s,base=d.resolve());hold=np.array(c.draw(19));assert all(np.array_equal(hold,np.array(c.draw(f))) for f in [20,48,95])
d=p/'S06-03';c=Compositor(json.load(open(d/'shot.json')),base=d.resolve());assert np.array_equal(np.array(c.draw(0)),np.array(c.draw(143)))
result={'coin_decoded_template_tracking':measure,'coin_source_settle_frames':[19,20,48,95],'coin_source_settle_pixel_identical':True,'blackout_source_first_last_pixel_identical':True,'codec_note':'Lossy inter-frame encoding creates small decoded pixel differences on intentional holds; no authored flicker. Source/native checks distinguish these.'}
(p/'pixel-checks.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
