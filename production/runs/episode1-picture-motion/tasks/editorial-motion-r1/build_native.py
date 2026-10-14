"""Bounded v2 editorial recipe; run from repository root with PYTHONPATH=."""
import json, shutil, subprocess, hashlib
from pathlib import Path
import numpy as np
from PIL import Image
from studio.craft import Session
from studio.engine.post import grain_plates, gate_weave
from studio.engine.fx import font
OUT=Path(__file__).resolve().parent
OLD=OUT.parent/'editorial-motion'
def save(p,v):p.write_text(json.dumps(v,indent=2))
for n in ['shared-sigil.json','shared-sigil.svg','shots.json']:shutil.copy2(OLD/n,OUT/n)
unit=json.loads((OUT/'shared-sigil.json').read_text())['path']
grain=OUT/'grain';grain.mkdir(exist_ok=True)
# Baked deterministic 24-plate bank, matching local studio grain construction.
for i,p in enumerate(grain_plates(1280,720,193407)):
 a=np.asarray(p,dtype=np.float32);im=np.zeros((720,1280,4),dtype=np.uint8)
 im[:,:,:3]=np.where(a[:,:,None]>0,255,0);im[:,:,3]=np.clip(abs(a)*16,0,255).astype(np.uint8)
 Image.fromarray(im).save(grain/f'grain-{i:04d}.png')
shots=json.loads((OUT/'shots.json').read_text())
recipe=[]
for row in shots:
 sid=row['id'];n=row['frames'];d=OUT/sid;d.mkdir(exist_ok=True);(d/'frames').mkdir(exist_ok=True)
 with Session('effectcraft',OUT,d/'receipts') as s:
  def call(c,**p):
   recipe.append({'shot':sid,'app':'effectcraft','tool':'execute_command','arguments':{'command':c,'params':p}})
   return s.call('execute_command',{'command':c,'params':p})
  def prop(l,p,v):return call('prop.set',layer=l,path=p,value=v)
  def key(l,p,f,v):return call('prop.addKey',layer=l,path=p,time=f/24,value=v)
  def expr(l,p,e):return call('prop.setExpression',layer=l,path=p,expression=e)
  def text(name,txt,size,tracking,y,color='#EDE6D6',start=0):
   l=call('layer.newText',name=name,text=txt,font='DejaVu Serif',size=size,tracking=tracking,fill=color,justify='center',position=[640,y],allCaps=False)['layer']
   # Explicit per-frame keys preserve v1 3-frame exposure cadence.
   for f in range(n):key(l,'transform/opacity',f,max(0,min(100,((f//3)*3-start)/24*100)))
   return l
  call('comp.new',name=sid+' revision 1',width=1280,height=720,frameRate=24,duration=n/24)
  black=sid in ['S01-15','S15-09']
  call('layer.newSolid',name='Background — black hold' if black else 'Background — navy #14202B',color='#000000' if black else '#14202B',width=1280,height=720)
  if sid in ['S00-01','S02-01']:
   center,radius=((640,330),200) if sid=='S00-01' else ((640,190),128)
   l=call('layer.newShape',kind='none',name='Sigil — shared connected path')['layer']
   call('shape.newPath',layer=l,vertices=[[center[0]+x*radius,center[1]+y*radius] for x,y in unit],space='comp',closed=False,fill=False,stroke='#C9A24A',strokeWidth=2)
   call('layer.addShapeItem',layer=l,kind='trim')
   for f in range(n):key(l,'contents/trim/end',f,min(100,(f//3)*3/72*100))
   if sid=='S00-01':
    # Independent editable effect controller, with exact subpixel curve keys.
    ctrl=call('layer.newNull',name='Effect — gate weave 0.3')['layer']
    call('layer.setParent',layers=[l],parent=ctrl)
    for f in range(n):
     dx,dy=gate_weave(sid,f,.3);key(ctrl,'transform/position',f,[640+dx,360+dy,0])
  if sid=='S00-02':
   text('Spanish — line 1','ELLOS CUENTAN.',40,180,282)
   text('Spanish — line 2','NOSOTROS RECORDAMOS.',40,180,348)
   text('English subtitle','They count. We remember. — ABUELA.',18,100,449,'#C9A24A')
  if sid=='S02-01':
   title=text('Main title','HERALDS OF THE CEMÍ',42,130,418,start=54)
   text('Episode subtitle','EPISODE 1 · 3:07',22,150,506,start=54)
   shine=call('layer.newText',name='Effect — single title shimmer',text='HERALDS OF THE CEMÍ',font='DejaVu Serif',size=42,tracking=130,fill='#F2D99B',justify='center',position=[640,418],allCaps=False)['layer']
   mask=call('layer.addMask',layer=shine,shape='rect',rect=[-422,-48,24,78])
   tree=s.call('get_layer',{'layer':shine,'flat':True});save(d/'shimmer-properties.json',tree)
   maskpath=next(p['path'] for p in tree['properties'] if p['type']=='path')
   for f in range(n):
    q=f//3*3;x=230+(q-102)/36*850-640
    key(shine,'transform/opacity',f,45/255*100 if 102<=q<138 else 0)
    key(shine,maskpath,f,{'t':'Path','v':{'vertices':[[x-12,-48],[x+12,-48],[x+12,30],[x-12,30]],'in_tangents':[[0,0]]*4,'out_tangents':[[0,0]]*4,'closed':True}})
  if not black:
   call('file.import',paths=[str(grain/'grain-0000.png')])
   project=s.call('get_project',{});item=next(i for i in project['items'] if i['type']=='Image Sequence')
   call('file.interpretFootage',items=[item['id']],frameRate=24,alpha='straight')
   # Explicit one-second instances: engine caps sequence out-point to source length.
   for sec in range(n//24):
    g=call('layer.addItem',item=item['id'],time=sec,duration=1)['layer']
    call('layer.rename',layer=g,name=f'Effect — film grain cycle {sec+1}')
    prop(g,'transform/opacity',50 if sid=='S00-01' else 35)
  s.call('save_project',{'path':str(d/'shot.ecproj')})
  save(d/'native-inspection.json',s.call('get_comp',{}))
  for f in range(n):
   s.call('render_frame',{'time':f/24,'path':str(d/'frames'/f'{f:06d}.png'),'max_side':0,'inline':False})
  # Reopen saved source and render one matching frame to check persistence.
  s.call('open_project',{'path':str(d/'shot.ecproj')})
  s.call('render_frame',{'time':(n-1)/24,'path':str(d/'reopened-last.png'),'max_side':0,'inline':False})
 subprocess.run(['ffmpeg','-v','error','-n','-framerate','24','-i',str(d/'frames/%06d.png'),'-frames:v',str(n),'-c:v','libx264','-crf','16','-pix_fmt','yuv420p','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709',str(d/'preview.mp4')],check=True)
 print(sid,'saved and rendered',flush=True)
save(OUT/'recipe.json',recipe)
