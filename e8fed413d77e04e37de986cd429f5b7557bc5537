from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
import numpy as np,json,shutil,hashlib
P=Path(__file__).resolve().parent
O=P.parent/'three-losses'; N=Path('production/runs/episode1-full-picture/amaia-breakdowns').resolve()
for d in ['cels','layers','sources','masks','review','decoded']: (P/d).mkdir(exist_ok=True)
def sj(n,v):(P/n).write_text(json.dumps(v,indent=2)+'\n')
timeline=json.loads((O/'action-timeline-review.json').read_text());sj('action-timeline.json',timeline)
for e in timeline['exposures']:
 for f in [e['source'],e['source'].replace('.png','-native.png')]:
  if (O/f).exists():shutil.copy2(O/f,P/f)
base=Image.open(O/'sources/rest.png').convert('RGBA');size=base.size
shutil.copy2(O/'sources/rest.png',P/'sources/rest.png')
# Only the near cross-hull is an occluder. Far diagonal rail stays behind bodies.
poly=[(0,780),(130,798),(230,836),(335,872),(700,871),(1000,867),(1300,864),(1500,862),(1617,863),(1615,887),(1672,904),(1672,941),(0,941)]
m=Image.new('L',size);ImageDraw.Draw(m).polygon(poly,fill=255);m.save(P/'masks/near-hull.png')
# Living body silhouette exclusion is left of x896; new figures begin to its right.
records=[];imgs=[]
for name,out,s,src_anchor,dst_anchor in [('woman','woman',.39,(550,800),(940,820)),('man','young-man',.39,(620,800),(1190,820)),('elder','elder',.39,(580,800),(1360,820))]:
 f=N/f'ghost-{name}-rgba.png';shutil.copy2(f,P/'sources'/f.name)
 im=Image.open(f).convert('RGBA');a=np.asarray(im.getchannel('A')); alpha=im.getchannel('A').filter(ImageFilter.MinFilter(3));im.putalpha(alpha)
 # A one-source-pixel choke removes the thin coloured fringe without redrawing contours.
 q=im.resize(tuple(round(v*s) for v in size),Image.Resampling.LANCZOS)
 xy=tuple(round(dst_anchor[i]-src_anchor[i]*s) for i in range(2))
 canvas=Image.new('RGBA',size);canvas.alpha_composite(q,xy);canvas.save(P/'layers'/f'{out}-registered-full.png')
 ca=np.asarray(canvas).copy();ca[:,:,3][np.asarray(m)>0]=0;canvas=Image.fromarray(ca)
 canvas.save(P/'layers'/f'{out}-occluded-native.png');canvas.resize((1280,720),Image.Resampling.LANCZOS).save(P/'layers'/f'apparition-{out}-cel.png')
 records.append({'figure':name,'source':str(f),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'mode':'RGBA','alpha_extrema':[int(a.min()),int(a.max())],'opaque_pixels':int((a==255).sum()),'scale_static':s,'translation_static':xy,'hip_source':src_anchor,'seat_contact_native':dst_anchor,'animation':'opacity only; no body transform','choke_source_pixels':1,'source_lower_crop_hidden_by_front_hull':True})
 imgs.append(canvas)
preview=base.copy()
for q in imgs:
 q=q.copy();q.putalpha(q.getchannel('A').point(lambda v:round(v*.25)));preview=Image.alpha_composite(preview,q)
preview.save(P/'review/layout.png')
ann=preview.convert('RGB');dr=ImageDraw.Draw(ann)
for r in records:
 x,y=r['seat_contact_native'];dr.ellipse((x-7,y-7,x+7,y+7),outline='yellow',width=2);dr.text((x-35,y+10),r['figure']+' hip/seat',fill='yellow')
dr.line(poly[:12],fill='cyan',width=3);ann.save(P/'review/contact-registration.png')
sj('registration.json',{'canvas':size,'records':records,'occlusion':'near cross-hull only; far rail behind complete figures; hip anchors on interior seat plane above near cross-hull','native_front_edge':poly})
recipe=json.loads((O/'native-review-recipe.json').read_text().replace(str(O),str(P)))
sj('native-recipe.json',recipe)
shutil.copy2(O/'head-landmarks.json',P/'head-landmarks.json')
sj('source-hashes.json',[{'path':str(f),'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in [O/'native-review-recipe.json',O/'action-timeline-review.json',O/'sources/rest.png']]+[{'path':r['source'],'sha256':r['sha256']} for r in records])
