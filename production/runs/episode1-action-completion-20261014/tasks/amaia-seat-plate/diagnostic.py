from pathlib import Path
from PIL import Image, ImageDraw
import json, hashlib, numpy as np
P=Path(__file__).resolve().parent
R=P.parents[4]
old=R/'production/runs/episode1-amaia-finish/tasks/three-losses-r2'
src=R/'production/runs/episode1-full-picture/amaia-breakdowns'
base=Image.open(P/'candidate.png').convert('RGBA')
mask=Image.open(old/'masks/near-hull.png').convert('L')
records=[]; combined=base.copy(); annotated=base.copy()
# One bounded source-only registration diagnostic. No artistic repair or invented contact approval.
for name,s,a,d in [('woman',.65,(550,800),(900,690)),('man',.70,(620,800),(1015,755)),('elder',.75,(580,800),(1135,810))]:
 f=src/f'ghost-{name}-rgba.png';im=Image.open(f).convert('RGBA')
 xy=tuple(round(d[i]-a[i]*s) for i in range(2));layer=Image.new('RGBA',base.size)
 layer.alpha_composite(im.resize(tuple(round(v*s) for v in im.size),Image.Resampling.LANCZOS),xy)
 layer.paste((0,0,0,0),(0,0),mask)
 single=Image.alpha_composite(base,layer)
 ImageDraw.Draw(single).text((10,10),'DIAGNOSTIC ONLY - '+name+' placement; contact not approved',fill='white')
 single.convert('RGB').save(P/f'placement-{name}.jpg',quality=90)
 combined=Image.alpha_composite(combined,layer)
 dr=ImageDraw.Draw(annotated);x,y=d;dr.ellipse((x-8,y-8,x+8,y+8),outline='yellow',width=3);dr.text((x+10,y-20),name,fill='yellow')
 records.append({'name':name,'source':str(f.relative_to(R)),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'scale':s,'source_anchor':a,'target_anchor':d,'translation':xy,'status':'diagnostic only, support and fit require review'})
combined.convert('RGB').save(P/'placement-combined.jpg',quality=92)
annotated.convert('RGB').save(P/'seat-anchors.jpg',quality=92)
a=np.asarray(Image.open(old/'sources/rest.png').convert('RGB'),dtype=np.int16);b=np.asarray(base.convert('RGB'),dtype=np.int16)
checks={}
for name,(x0,y0,x1,y1) in {'living_region':(150,50,800,700),'foreground_hull':(300,880,1550,930),'upper_background':(800,0,1672,550)}.items():
 v=np.abs(a[y0:y1,x0:x1]-b[y0:y1,x0:x1]); checks[name]={'mean_abs_channel_delta':float(v.mean()),'max_channel_delta':int(v.max()),'exact_pixel_fraction':float((v.max(axis=2)==0).mean())}
(P/'placement-diagnostic.json').write_text(json.dumps({'canvas':base.size,'records':records,'source_region_pixel_comparisons':checks,'method':'static uniform registration of existing full RGBA sources and inherited hull mask; no warp; one proposed staggered layout only'},indent=2)+'\n')
