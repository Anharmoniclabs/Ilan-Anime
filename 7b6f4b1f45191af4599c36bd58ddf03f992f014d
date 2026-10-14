from pathlib import Path
import json, shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
R=Path.cwd(); O=R/'production/runs/episode1-insert-finish/tasks/native-inserts'; D=O/'S05-13'; D.mkdir(exist_ok=True)
P=R/'production/runs/episode1-native-inserts/tasks/room-filters-coin-blackout/S05-13'
blank=Image.open(R/'production/runs/episode1-full-picture/coin-assets/coin-unengraved-rgba.png').convert('RGBA')
old=Image.open(P/'coin-matte-clean.png').convert('RGBA')
# Fixed affine registration of supplied artwork to prior opaque silhouette; not animated.
sx=356/271; sy=209/156
registered=blank.transform(old.size,Image.Transform.AFFINE,(sx,0,638-489*sx,0,sy,380-293*sy),Image.Resampling.BICUBIC)
registered.putalpha(old.getchannel('A')); registered.save(D/'coin-blank-registered.png')
sigilpath=R/'production/runs/episode1-picture-motion/tasks/editorial-motion-r1/shared-sigil.json'
sigil=json.loads(sigilpath.read_text()); pts=sigil['path']
# Planar oblique projection, fitted within the upper face, independent of thickness rim.
a,b,c,d,e,f=100,12,623,5,62,359
projected=[(a*x+b*y+c,d*x+e*y+f) for x,y in pts]
scale=4
mask=Image.new('L',(1280*scale,720*scale)); draw=ImageDraw.Draw(mask)
draw.line([(round(x*scale),round(y*scale)) for x,y in projected],fill=255,width=round(3.2*scale),joint='curve')
mask=mask.resize(old.size,Image.Resampling.LANCZOS)
# One groove with a subpixel lower-right lip; no second offset full bright mark.
m=np.asarray(mask,dtype=float)/255
shift=mask.transform(old.size,Image.Transform.AFFINE,(1,0,-.6,0,1,-.65),Image.Resampling.BICUBIC)
h=np.maximum(np.asarray(shift,dtype=float)/255-m,0)*.36
rgb=np.array(registered,dtype=float); rgb[:,:,:3]*=(1-m[:,:,None]*.72)
rgb[:,:,:3]=rgb[:,:,:3]*(1-h[:,:,None])+np.array([240,155,73])*h[:,:,None]
coin=Image.fromarray(np.uint8(np.clip(rgb,0,255))); coin.save(D/'coin-shared-engraved.png'); mask.save(D/'engraving-mask.png')
overlay=Image.new('RGBA',old.size,(29,14,9,0)); overlay.putalpha(mask.point(lambda v:round(v*.72))); overlay.save(D/'engraving-groove.png')
shutil.copy2(sigilpath,D/'shared-sigil.json'); shutil.copy2(sigilpath.with_suffix('.svg'),D/'shared-sigil.svg')
svg='<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720"><polyline points="'+' '.join(f'{x:.8f},{y:.8f}' for x,y in projected)+'" fill="none" stroke="#1d0e09" stroke-width="3.2" stroke-linejoin="round" stroke-linecap="round"/></svg>'
(D/'engraving-projected.svg').write_text(svg)
shot=json.loads((P/'shot.json').read_text()); mapping={}
for layer in shot['layers']:
 src=Path(layer['source']); target=D/( 'coin-shared-engraved.png' if 'coin-matte' in src.name else src.name)
 if target.name!='coin-shared-engraved.png': shutil.copy2(src,target)
 mapping[str(src)]=str(target); layer['source']=str(target)
(D/'shot.json').write_text(json.dumps(shot,indent=2))
recipe=(P/'native-matte-recipe.json').read_text()
for src,dst in mapping.items(): recipe=recipe.replace(src,dst)
recipe=recipe.replace('"item": "coin-matte-clean.png"','"item": "coin-shared-engraved.png"')
recipe=json.loads(recipe)
# Save every frame from the actual native composition, retaining all original keys.
recipe['steps']=[s for s in recipe['steps'] if s['tool']!='render_frame']
recipe['steps'] += [{'app':'effectcraft','tool':'render_frame','arguments':{'time':i/24,'path':'${OUT}/frame-%04d.png'%i,'max_side':0,'inline':False}} for i in range(96)]
(D/'native-recipe.json').write_text(json.dumps(recipe,indent=2))
reg={'source':str(blank.filename) if hasattr(blank,'filename') else 'coin-unengraved-rgba.png','source_opaque_bbox':[638,380,994,589],'target_opaque_bbox':[489,293,760,449],'inverse_affine':[sx,0,638-489*sx,0,sy,380-293*sy],'alpha':'exact prior coin-matte-clean alpha preserved','sigil_projection':[a,b,c,d,e,f],'groove_width_px':3.2,'groove_darkening':.72,'lip_offset_px':[.6,.65],'lip_strength':.36,'keys':shot['layers'][2]['keys'],'status':'exploratory; independent review pending'}
(D/'registration.json').write_text(json.dumps(reg,indent=2))
