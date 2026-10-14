from pathlib import Path
import math,json,subprocess
from studio.craft import Session
OUT=Path(__file__).resolve().parent; TASK=OUT.parent; GEN=TASK/'generated'; ROOT=Path.cwd(); R2=TASK.parent/'amaia-assets-r2'
# Two measured anatomical landmarks determine a single uniform similarity transform.
PARTS=[
 ('right-upper',[150,30,270,490],[339,85],[239,476],[365,322],[344,544],'body-control'),
 ('left-upper',[605,30,270,490],[685,85],[785,476],[629,322],[650,544],'body-control'),
 ('right-forearm',[170,580,190,480],[282,625],[224,1010],[344,544],[290,778],'right-upper'),
 ('left-forearm',[666,580,190,480],[742,625],[798,1010],[650,544],[731,778],'left-upper'),
 ('right-hand',[160,1120,190,390],[239,1177],[304,1467],[290,778],[304,893],'right-forearm'),
 ('left-hand',[674,1120,190,390],[787,1177],[720,1467],[731,778],[710,893],'left-forearm')]
def similarity(a,b,c,d):
 u=[b[i]-a[i] for i in [0,1]];v=[d[i]-c[i] for i in [0,1]]
 return 100*math.hypot(*v)/math.hypot(*u),math.degrees(math.atan2(v[1],v[0])-math.atan2(u[1],u[0]))
def run():
 (OUT/'parts').mkdir(exist_ok=True);(OUT/'frames').mkdir(exist_ok=True)
 with Session('effectcraft',ROOT,OUT/'evidence') as s:
  def cmd(c,**p):return s.call('execute_command',{'command':c,'params':p})
  def prop(l,p,v=None,e=None):return s.call('set_property',{'layer':l,'path':p,**({'expression':e} if e is not None else {'value':v})})
  s.call('open_project',{'new':True});cmd('file.import',paths=[str(GEN/'arm-joints.png'),str(GEN/'body-underpaint.png'),str(R2/'amaia-blink.png'),str(R2/'amaia-talk.png')])
  for n,(x,y,w,h),a,b,c,d,parent in PARTS:
   cmd('comp.new',name='SOURCE '+n,width=w,height=h,frameRate=24,duration=2)
   cmd('layer.addItem',item='arm-joints.png',position=[512-x,768-y])
   s.call('render_frame',{'time':0,'path':str(OUT/'parts'/f'{n}.png'),'max_side':0,'transparent':True,'inline':False})
  cmd('project.delete',items=['SOURCE '+a[0] for a in PARTS]);cmd('comp.new',name='AMAIA - articulated candidate',width=1024,height=1536,duration=2,frameRate=24,background='#26323e')
  cmd('file.import',paths=[str(OUT/'parts'/f'{a[0]}.png') for a in PARTS]);ls={};ls['body-control']=cmd('layer.newNull',name='body-control')['layer'];prop(ls['body-control'],'transform/position',[506,560]);ls['body-underpaint']=cmd('layer.addItem',item='body-underpaint.png',position=[512,768],index=1)['layer'];cmd('layer.rename',layer=ls['body-underpaint'],name='body-underpaint');cmd('layer.setParent',layers=[ls['body-underpaint']],parent=ls['body-control'])
  specs=[]
  for n,(x,y,w,h),a,b,c,d,parent in PARTS:
   l=cmd('layer.addItem',item=n+'.png',position=c,index=1)['layer'];ls[n]=l;cmd('layer.rename',layer=l,name=n);sc,angle=similarity(a,b,c,d)
   for p,v in [('transform/anchor',[a[0]-x,a[1]-y]),('transform/position',c),('transform/scale',[sc,sc]),('transform/rotation',angle)]:prop(l,p,v)
   specs.append(dict(name=n,source_crop=[x,y,w,h],source_pivot=a,source_end=b,target_pivot=c,target_end=d,uniform_scale=sc,rotation=angle,parent=parent))
  for n,*_,parent in PARTS:cmd('layer.setParent',layers=[ls[n]],parent=ls[parent])
  ls['Face controls']=cmd('layer.newNull',name='Face controls')['layer'];s.call('add_effect',{'layer':ls['Face controls'],'effect':'Slider Control'})
  for name,item,rect,expr in [('blink-eyes','amaia-blink.png',[446,122,114,38],'m>=0.5&&m<1.5?100:0'),('talk-mouth','amaia-talk.png',[482,181,50,29],'m>=1.5?100:0')]:
   l=cmd('layer.addItem',item=item,position=[512,768],index=1)['layer'];ls[name]=l;cmd('layer.rename',layer=l,name=name);cmd('layer.addMask',layer=l,shape='rect',rect=rect,mode='Add');prop(l,'masks/#1/feather',[3,3]);cmd('layer.setParent',layers=[l],parent=ls['body-control']);prop(l,'transform/opacity',e='var m=thisComp.layer("Face controls").effect("Slider Control")("Slider"); '+expr)
  cid=s.call('get_comp',{})['id'];cmd('essential.setPrimary',comp=cid);cmd('essential.setName',name='Amaia - arm articulation and face')
  for n,*_ in PARTS:cmd('essential.addProperty',layer=ls[n],path='transform/rotation',name=n+' rotation')
  cmd('essential.addProperty',layer=ls['Face controls'],path='effects/#1/slider',name='Face: 0 neutral / 1 blink / 2 talk');cmd('essential.addProperty',layer=ls['body-control'],path='transform/position',name='Body position')
  s.call('render_frame',{'time':0,'path':str(OUT/'assembled.png'),'transparent':True,'max_side':0,'inline':False});s.call('render_frame',{'time':0,'path':str(OUT/'assembled-slate.png'),'max_side':0,'inline':False});s.call('save_project',{'path':str(OUT/'amaia-puppet.ecproj')})
  cmd('comp.saveFrameAsPsd',path=str(OUT/'amaia-layered.psd'),time=0)
  (OUT/'rig.json').write_text(json.dumps({'status':'exploratory','canvas':[1024,1536],'parts':specs,'layers':ls,'uniform_transforms_only':True},indent=2))
  demo=cmd('project.duplicate',items=[cid])['items'][0];cmd('comp.open',comp=demo);cmd('comp.settings',name='AMAIA - bounded articulation test');dl={a['name']:a['id'] for a in s.call('get_comp',{})['layers']}
  for n,amount in [('right-upper',4),('left-upper',-4),('right-forearm',-12),('left-forearm',12),('right-hand',4),('left-hand',-4)]:
   current=next(x['value'] for x in s.call('get_layer',{'layer':dl[n],'flat':True})['properties'] if x['path']=='transform/rotation')
   s.call('add_keyframe',{'layer':dl[n],'path':'transform/rotation','keys':[{'time':i/8,'value':current+amount*math.sin(math.pi*i/16)} for i in range(17)],'interpolation':'hold'})
  s.call('add_keyframe',{'layer':dl['Face controls'],'path':'effects/#1/slider','keys':[{'time':0,'value':0},{'time':.5,'value':1},{'time':.625,'value':0},{'time':1,'value':2},{'time':1.25,'value':0}],'interpolation':'hold'})
  for i in range(48):s.call('render_frame',{'time':i/24,'path':str(OUT/'frames'/f'{i:04d}.png'),'max_side':1080,'inline':False})
  s.call('render_frame',{'time':1,'path':str(OUT/'posed.png'),'max_side':0,'inline':False});cmd('comp.open',comp=cid);cmd('comp.openInEssentialGraphics',comp=cid);s.call('save_project',{'path':str(OUT/'amaia-puppet.ecproj')})
 subprocess.run(['ffmpeg','-v','error','-y','-framerate','24','-i',str(OUT/'frames/%04d.png'),'-c:v','libx264','-pix_fmt','yuv420p','-crf','18',str(OUT/'amaia-controls.mp4')],check=True)
 with Session('photocraft',ROOT,OUT/'paint-evidence') as s:
  s.call('doc_open',{'path':str(OUT/'amaia-layered.psd')})
  for a in s.call('doc_inspect',{})['layers']:
   if a['name'] in ['blink-eyes','talk-mouth']:s.call('command_run',{'id':'layer.setProps','params':{'layer':a['id'],'visible':False}})
  s.call('doc_save',{'path':str(OUT/'amaia-layered.pcraft')});s.call('doc_export',{'path':str(OUT/'amaia-layered.psd'),'format':'psd'})
 print('DONE')
if __name__=='__main__':run()
