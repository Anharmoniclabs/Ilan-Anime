from pathlib import Path
import json, shutil, subprocess, math, hashlib, sys
sys.path.insert(0,str(Path.cwd()))
from PIL import Image, ImageDraw, ImageFilter
ROOT=Path.cwd(); OUT=ROOT/'production/runs/episode1-native-inserts/tasks/room-filters-coin-blackout'
W,H=1280,720
idx=json.load(open(ROOT/'production/runs/episode1-anime90s-scenes/shot-index.json'))
# Recover selected rows without assuming the index wrapper.
def rows(o):
 if isinstance(o,dict):
  if o.get('shot') in ['S03-03','S04-02','S05-13','S06-03'] and 'path' in o:yield o
  else:
   for v in o.values():yield from rows(v)
 elif isinstance(o,list):
  for v in o:yield from rows(v)
selected={r['shot']:r for r in rows(idx)}
def write(p,d):p.write_text(json.dumps(d,indent=2))
def svg(d,name,body,w=W,h=H):
 p=d/(name+'.svg');p.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">{body}</svg>')
 subprocess.run(['rsvg-convert',str(p),'-o',str(d/(name+'.png'))],check=True)
 return name+'.png'
def layer(name,source,keys=None,rate=1):
 return {'name':name,'source':source,'rate':rate,'keys':keys or [{'frame':0,'x':0,'y':0}]}
def spec(sh,n,ls):return {'id':sh,'size':[W,H],'fps':24,'frames':n,'status':'exploratory','layers':ls,'post':{'grain':0,'weave':0,'chroma':0,'vignette':0,'halation':0}}
provenance=[]
for sh in selected:
 d=OUT/sh;d.mkdir(exist_ok=True);(d/'sources').mkdir(exist_ok=True)
 p=ROOT/selected[sh]['path'];shutil.copy2(p,d/'sources/selected-original.png')
 provenance.append({'shot':sh,'source':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'status':'exploratory source; not author-approved'})
# Room: same painted plate, fixed uniform resize and numeric horizontal pan.
d=OUT/'S03-03'; im=Image.open(d/'sources/selected-original.png').convert('RGB');im.resize((1408,792),Image.Resampling.LANCZOS).save(d/'room-wide.png')
cam=[{'frame':f,'x':-128*(f/287),'y':-72} for f in range(288)]
ls=[layer('room inventory painted plate','room-wide.png',cam)]
steam=[]
for i in range(8):
 # Three independent ink/wash wisps. Three-frame exposures; source coordinates 1408x792.
 body=''
 for j in range(3):
  x=1160+j*17; y=496-i*3-j*3; a=max(0,(1-i/9)*.26)
  body+=f'<path d="M{x},{y+30} C{x-9},{y+18} {x+10},{y+11} {x+2},{y} C{x-4},{y-7} {x-4},{y-10} {x+2},{y-14}" fill="none" stroke="#cbd6da" stroke-opacity="{a}" stroke-width="{3+i*.35}" stroke-linecap="round"/>'
 steam.append(svg(d,f'steam-{chr(97+i)}',body,1408,792))
# Pulses, then empty rests, all on 3s.
svg(d,'steam-clear','',1408,792)
seq=steam+['steam-clear.png']*8
ls.append({'name':'radiator drawn steam on threes','sequence':seq,'loop':True,'rate':3,'smooth':True,'keys':cam})
write(d/'shot.json',spec('S03-03',288,ls));write(d/'camera.json',{'source_size':[1672,941],'registered_size':[1408,792],'viewport':[1280,720],'keys':cam,'no_warp':True,'fan':'No fan visible in supplied plate; none invented','order':'Desk/dish/laundry left, radiator and nightstand right, follows actual painting over proposed phase order.'})
# Three editable gauze panes. Use source room and endpoint artwork, no old malformed sigils.
d=OUT/'S04-02';Image.open(OUT/'S03-03/sources/selected-original.png').convert('RGB').resize((W,H),Image.Resampling.LANCZOS).save(d/'room.png')
im=Image.open(d/'sources/selected-original.png').convert('RGBA').resize((W,H),Image.Resampling.LANCZOS)
# The bounded endpoint crops contain pipe and projector; they exclude old sigils and panes.
left=Image.new('RGBA',(W,H));left.paste(im.crop((0,440,214,655)),(0,440));left.save(d/'pipe.png')
right=Image.new('RGBA',(W,H));right.paste(im.crop((1058,430,1280,652)),(1058,430));right.save(d/'projector.png')
ls=[layer('room','room.png'),layer('pipe endpoint','pipe.png'),layer('projector endpoint','projector.png')]
for i,(x,label) in enumerate([(320,'SMOOTHING'),(570,'GATING'),(820,'NOISE FLOOR')]):
 body=f'<g id="gauze-{i}"><path d="M{x},242 L{x+166},252 L{x+166},578 L{x},568 Z" fill="#8b9dad" fill-opacity=".13" stroke="#d3ae77" stroke-width="1.6"/>'
 for a in range(9,163,9):body+=f'<path d="M{x+a},253 L{x+a-4},563" stroke="#b3bdc9" stroke-opacity=".09" stroke-width=".6"/>'
 for b in range(265,565,9):body+=f'<path d="M{x+5},{b} L{x+160},{b+9}" stroke="#b3bdc9" stroke-opacity=".07" stroke-width=".6"/>'
 body+='</g>'
 ls.append(layer(label+' gauze',svg(d,f'pane-{i+1}-gauze',body)))
 body=f'<text x="{x+83}" y="286" text-anchor="middle" font-family="DejaVu Sans" font-size="17" fill="#ecd7b0">{label}</text><g fill="none" stroke="#edcca0" stroke-width="3" stroke-linecap="round">'
 if i==0:
  body+=f'<path d="M{x+50},322 H{x+116}"/>'
  for a in range(50,117,11):body+=f'<path d="M{x+a},322 V355"/>'
 elif i==1:body+=f'<path d="M{x+62},359 V314 H{x+105} V359 M{x+62},314 L{x+91},324 V365 L{x+62},359"/><circle cx="{x+84}" cy="342" r="1"/>'
 else:body+=f'<path d="M{x+51},337 H{x+116}"/>'
 body+='</g>';ls.append(layer(label+' label and icon',svg(d,f'pane-{i+1}-label',body)))
sigil=json.load(open(ROOT/'production/runs/episode1-picture-motion/tasks/editorial-motion-r1/shared-sigil.json'))
pts=sigil['path'];xx=[p[0] for p in pts];yy=[p[1] for p in pts];span=max(max(xx)-min(xx),max(yy)-min(yy))
coords=[((p[0]-min(xx))/span*72+12,(p[1]-min(yy))/span*72+12) for p in pts]
body='<polyline points="'+' '.join(f'{x:.3f},{y:.3f}' for x,y in coords)+'" fill="none" stroke="#b7edf0" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>'
svg(d,'rigid-shared-sigil',body,100,100)
# One unchanged waveform packet, same source and dimensions at every frame.
wave=[(x,20+10*math.sin(x*.18)*(.65+.35*math.cos(x*.05))) for x in range(121)]
svg(d,'rigid-waveform','<polyline points="'+' '.join(f'{x},{y:.3f}' for x,y in wave)+'" fill="none" stroke="#b7edf0" stroke-width="2"/>',124,40)
keys=[{'frame':f,'x':180+880*((f//3)*3/141),'y':393} for f in range(0,144,3)]
ls.append(layer('shared connected sigil travels unchanged','rigid-shared-sigil.png',keys,3))
ls.append(layer('same waveform travels unchanged','rigid-waveform.png',[dict(k,y=503,x=k['x']-12) for k in keys],3))
write(d/'shot.json',spec('S04-02',144,ls));shutil.copy2(ROOT/'production/runs/episode1-picture-motion/tasks/editorial-motion-r1/shared-sigil.json',d/'sources/shared-sigil.json');shutil.copy2(ROOT/'production/runs/episode1-picture-motion/tasks/editorial-motion-r1/shared-sigil.svg',d/'sources/shared-sigil.svg')
# Coin: retain exact painting; alpha bounds and wood registration explicit.
d=OUT/'S05-13'
for name in ['clean-plate','coin-rgba']:shutil.copy2(ROOT/f'production/runs/episode1-full-picture/coin-assets/{name}.png',d/f'sources/{name}.png')
bg=Image.open(d/'sources/clean-plate.png').convert('RGB').resize((W,H),Image.Resampling.LANCZOS);bg.save(d/'clean-plate.png')
coin=Image.open(d/'sources/coin-rgba.png').convert('RGBA');original_bbox=coin.getchannel('A').getbbox();coin=coin.resize((W,H),Image.Resampling.LANCZOS);coin.save(d/'coin-rgba.png');bbox=coin.getchannel('A').getbbox()
yoff=98
shadow=Image.new('RGBA',(W,H));dr=ImageDraw.Draw(shadow);dr.ellipse((494,519,758,551),fill=(11,8,12,195));shadow=shadow.filter(ImageFilter.GaussianBlur(3));shadow.save(d/'contact-shadow.png')
ks=[]
for f in range(96):
 rise=0
 if 3<=f<=12:rise=12*(1-(1-(f-3)/9)**2)
 elif 12<f<=15:rise=12
 elif f==16:rise=9
 elif f==18:rise=1
 ks.append({'frame':f,'x':2 if f==1 else 0,'y':yoff-rise,'scale':1})
ls=[layer('wood clean plate','clean-plate.png'),layer('anchored contact shadow','contact-shadow.png'),layer('same rigid copper coin','coin-rgba.png',ks)]
# Narrow copper glint clipped to original alpha, at f12/13/14 only.
for f in [12,13,14]:
 gl=Image.new('RGBA',(W,H));dr=ImageDraw.Draw(gl);x=510+(f-12)*102;dr.line((x,290,x+38,455),fill=(255,211,142,115),width=4)
 import numpy as np
 a=np.array(gl);a[:,:,3]=(a[:,:,3].astype(float)*np.array(coin.getchannel('A'))/255).astype('uint8');Image.fromarray(a).save(d/f'glint-{chr(97+f-12)}.png')
 ls.append(dict(layer(f'copper glint {f}',f'glint-{chr(97+f-12)}.png',[{'frame':0,'y':86}]),**{'in':f,'out':f+1}))
svg(d,'white-contact-flash','<rect width="1280" height="720" fill="white"/>')
ls.append(dict(layer('one frame contact flash','white-contact-flash.png'),**{'in':17,'out':18}))
write(d/'shot.json',spec('S05-13',96,ls))
write(d/'registration.json',{'original_alpha_bbox':original_bbox,'resized_alpha_bbox':bbox,'rest_translation_y':98,'rest_bottom_y':bbox[3]-1+98,'wood_plane_contact_band':[519,552],'rise_pixels':12,'rigid_scale':1,'keys':ks,'motif_dependency':'Painted coin groove is a broad filled spiral/hooked triangle; shared-sigil.json is a single thin open path with different triangle proportion. Native line overlay alone cannot remove existing engraved groove convincingly. Need clean unengraved coin face or author-approved registered motif repaint; original coin retained.'})
# Intentional still block: retain only distant existing glow. No nearby lamp flicker.
d=OUT/'S06-03';Image.open(d/'sources/selected-original.png').convert('RGB').resize((W,H),Image.Resampling.LANCZOS).save(d/'blackout-plate.png')
write(d/'shot.json',spec('S06-03',144,[layer('intentional blackout hold with painted distant ambient glow','blackout-plate.png')]))
write(OUT/'provenance.json',provenance)
# Native EffectCraft recipe mirrors independent studio spec. Sampled transforms retain frame-exact paths.
for sh in selected:
 d=OUT/sh;s=json.load(open(d/'shot.json'));steps=[{'app':'effectcraft','tool':'open_project','arguments':{'new':True}},{'app':'effectcraft','tool':'execute_command','arguments':{'command':'comp.new','params':{'name':sh,'width':W,'height':H,'frameRate':24,'duration':s['frames']/24}}}]
 def cmd(c,p):steps.append({'app':'effectcraft','tool':'execute_command','arguments':{'command':c,'params':p}})
 from studio.engine.compositor import interpolate,LAYER_DEFAULTS
 for li,l in enumerate(s['layers']):
  spans=[]
  if 'sequence' in l:
   for start in range(0,s['frames'],l['rate']):spans.append((start,min(s['frames'],start+l['rate']),l['sequence'][(start//l['rate'])%len(l['sequence'])]))
  else:spans=[(l.get('in',0),l.get('out',s['frames']),l['source'])]
  for j,(start,end,src) in enumerate(spans):
   full=str(d/src);name=f'{li}-{j} {l["name"]}'
   cmd('file.import',{'paths':[full]});cmd('layer.addItem',{'item':Path(src).name,'time':start/24,'duration':(end-start)/24});cmd('layer.rename',{'name':name})
   iw,ih=Image.open(full).size
   # Positions at every frame eliminate interpolation/cadence ambiguity.
   for f in range(start,end):
    local=f-l.get('in',0);q=local if l.get('smooth') else local//l.get('rate',1)*l.get('rate',1)
    k=interpolate(l.get('keys',[]),q,LAYER_DEFAULTS)
    cmd('prop.addKey',{'layer':name,'path':'transform/position','time':f/24,'value':[iw/2+k['x'],ih/2+k['y']]})
 steps.append({'app':'effectcraft','tool':'save_project','arguments':{'path':'${OUT}/shot.ecproj'}})
 for f in sorted(set([0,s['frames']//2,s['frames']-1]+([12,16,17,18,19] if sh=='S05-13' else []))):steps.append({'app':'effectcraft','tool':'render_frame','arguments':{'time':f/24,'path':'${OUT}/native-'+str(f)+'.png','max_side':0,'inline':False}})
 write(d/'native-recipe.json',{'steps':steps,'outputs':['shot.ecproj']})
print('Built four layered draft specifications and saved recipes')
