"""Bounded source-registration diagnostic. Not a production shot or approval."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import hashlib,json
ROOT=Path(__file__).resolve().parents[5]
P=Path(__file__).resolve().parent
OLD=ROOT/'production/runs/episode1-amaia-finish/tasks/three-losses-r2'
SRC=ROOT/'production/runs/episode1-full-picture/amaia-breakdowns'
base=Image.open(OLD/'sources/rest.png').convert('RGBA')
mask=Image.open(OLD/'masks/near-hull.png').convert('L')
records=[]
opaque=base.copy(); ghost=base.copy()
for name,src_anchor,dst in [('woman',(550,800),(940,820)),('man',(620,800),(1190,820)),('elder',(580,800),(1360,820))]:
 f=SRC/f'ghost-{name}-rgba.png'; im=Image.open(f).convert('RGBA')
 scale=.75
 xy=tuple(round(dst[i]-src_anchor[i]*scale) for i in range(2))
 layer=Image.new('RGBA',base.size)
 layer.alpha_composite(im.resize(tuple(round(v*scale) for v in im.size),Image.Resampling.LANCZOS),xy)
 layer.paste((0,0,0,0),(0,0),mask)
 opaque=Image.alpha_composite(opaque,layer)
 layer.putalpha(layer.getchannel('A').point(lambda a:round(a*.25)))
 ghost=Image.alpha_composite(ghost,layer)
 records.append({'source':str(f.relative_to(ROOT)),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'scale':scale,'translation':xy,'unchanged_rejected_anchor':dst,'contact_status':'NOT ESTABLISHED: anchor is not a visible supporting bench'})
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',20)
for name,im,label in [('adult-scale-probe-opaque',opaque,'DIAGNOSTIC ONLY - larger adult scale, original unsupported anchors'),('adult-scale-probe-quarter-alpha',ghost,'DIAGNOSTIC ONLY - prescribed .25 alpha, seating remains unresolved')]:
 ImageDraw.Draw(im).rectangle((0,0,1672,36),fill='black')
 ImageDraw.Draw(im).text((12,6),label,font=font,fill='white')
 im.convert('RGB').save(P/f'{name}.jpg',quality=92)
# Existing visible wood only: this annotation does not create new seats.
annot=base.copy();dr=ImageDraw.Draw(annot)
dr.line([(850,720),(1015,710)],fill='yellow',width=5)
dr.line([(994,808),(1120,863)],fill='cyan',width=5)
dr.text((1025,690),'Short bench edge',font=font,fill='yellow')
dr.text((1140,820),'Low diagonal plank',font=font,fill='cyan')
for r in records:
 x,y=r['unchanged_rejected_anchor'];dr.ellipse((x-8,y-8,x+8,y+8),outline='red',width=3)
dr.rectangle((0,0,1672,36),fill='black');dr.text((12,6),'SOURCE DIAGNOSTIC - red circles are rejected anchors; no seat inferred',font=font,fill='white')
annot.convert('RGB').save(P/'seat-support-source-diagnostic.jpg',quality=94)
(P/'registration-probe.json').write_text(json.dumps({'status':'diagnostic-not-production','canvas':base.size,'records':records,'missing_visual':'Perspective-correct empty three-seat canoe interior plate with visible seat tops/contact edges matched to adult-scale figures; alternatively a restaged memory insert with complete adult seat contact drawings. Existing living figures and hull must be preserved.'},indent=2)+'\n')
