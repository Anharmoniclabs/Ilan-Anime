from pathlib import Path
import json, subprocess, math
from studio.craft import Session
ROOT=Path.cwd(); OUT=Path(__file__).resolve().parent; ATLAS=OUT/'amaia-parts-atlas.png'
# Crops and landmarks measured from the actual 1254px atlas, not expected grid sizes.
# Forearms/thighs are assigned by silhouette direction for the actual screen-side anatomy.
DATA=[
 ('pony',[998,0,205,327],[1090,114],[428,220],[100,160],None),
 ('right-thigh',[68,938,175,288],[165,969],[433,703],[145,205],None),
 ('right-shin-foot',[1031,620,116,304],[1097,650],[370,1201],[100,105],'right-thigh'),
 ('left-thigh',[710,634,160,280],[779,660],[563,703],[145,205],None),
 ('left-shin-foot',[423,926,112,316],[477,960],[655,1201],[100,105],'left-thigh'),
 ('right-upper-arm',[58,324,177,296],[176,356],[352,330],[100,100],'torso'),
 ('right-forearm',[85,641,142,272],[181,674],[287,562],[95,95],'right-upper-arm'),
 ('right-hand',[715,344,133,261],[784,370],[234,772],[60,60],'right-forearm'),
 ('left-upper-arm',[1018,324,188,294],[1070,350],[647,330],[95,95],'torso'),
 ('left-forearm',[420,329,138,282],[466,352],[724,556],[95,95],'left-upper-arm'),
 ('left-hand',[426,650,130,250],[484,678],[771,774],[60,60],'left-forearm'),
 ('torso',[330,16,292,296],[477,36],[500,246],[120,120],None),
 ('skirt',[0,0,1024,1536],[520,60],[506,569],[50,55],None),
 ('head-neutral',[20,8,285,300],[176,237],[500,235],[105,105],'head-control'),
 ('head-blink',[646,940,280,298],[791,1170],[500,235],[105,105],'head-control'),
 ('head-talk',[961,939,287,299],[1104,1170],[500,235],[105,105],'head-control'),
]
def run():
 (OUT/'parts').mkdir(exist_ok=True); (OUT/'rig-frames').mkdir(exist_ok=True)
 with Session('effectcraft',ROOT,OUT/'rig-evidence') as s:
  def cmd(c,**kw):return s.call('execute_command',{'command':c,'params':kw})
  def prop(l,p,v=None,expr=None):
   a={'layer':l,'path':p}
   if expr is not None:a['expression']=expr
   else:a['value']=v
   return s.call('set_property',a)
  s.call('open_project',{'new':True});cmd('file.import',paths=[str(ATLAS)])
  for name,(x,y,w,h),anchor,pos,scale,parent in DATA:
   if name=='skirt': x,y,w,h=656,0,266,331
   cmd('comp.new',name='SOURCE - '+name,width=w,height=h,frameRate=24,duration=3)
   cmd('layer.addItem',item=ATLAS.name,position=[627-x,627-y])
   s.call('render_frame',{'time':0,'path':str(OUT/'parts'/f'{name}.png'),'transparent':True,'max_side':0,'inline':False})
  cmd('project.delete',items=['SOURCE - '+a[0] for a in DATA])
  comp=cmd('comp.new',name='AMAIA - editable full body',width=1024,height=1536,frameRate=24,duration=3,background='#26323e')
  cmd('file.import',paths=[str(OUT/'parts'/f'{a[0]}.png') for a in DATA]+[str(OUT/'amaia-skirt-hires.png')])
  layers={}
  # Root and head nulls expose neutral transforms separately from replacement art.
  for name,pos in [('body-control',[506,569]),('head-control',[500,235])]:
   layer=cmd('layer.newNull',name=name)['layer']; layers[name]=layer
   prop(layer,'transform/position',pos)
  face=cmd('layer.newNull',name='Face controls')['layer']; layers['Face controls']=face
  s.call('add_effect',{'layer':face,'effect':'Slider Control'})
  for name,(x,y,w,h),anchor,pos,scale,parent in DATA:
   layer=cmd('layer.addItem',item=('amaia-skirt-hires.png' if name=='skirt' else name+'.png'),position=pos,index=1)['layer'];layers[name]=layer
   cmd('layer.rename',layer=layer,name=name)
   prop(layer,'transform/anchor',[anchor[0]-x,anchor[1]-y]);prop(layer,'transform/position',pos);prop(layer,'transform/scale',scale)
   # Native overlap masks suppress the atlas's dark cut-edge caps inside joints.
   if name in ['right-upper-arm','left-upper-arm']:
    cmd('mask.new',layer=layer,vertices=([[0,0],[177,0],[177,210],[95,250],[82,260],[40,260],[36,205],[25,170],[0,120]] if name=='right-upper-arm' else [[0,0],[188,0],[188,130],[164,190],[156,215],[150,258],[95,258],[85,220],[0,190]]),closed=True,mode='Add')
    prop(layer,'masks/#1/feather',[2,2])
   if name in ['right-forearm','left-forearm']:
    cmd('mask.new',layer=layer,vertices=([[0,0],[142,0],[142,272],[55,272],[25,250],[18,220],[0,190]] if name=='right-forearm' else [[0,0],[138,0],[138,190],[116,250],[110,282],[0,282]]),closed=True,mode='Add')
    prop(layer,'masks/#1/feather',[1.5,1.5])
   if name=='right-thigh':cmd('mask.new',layer=layer,vertices=[[90,0],[160,0],[175,288],[0,288],[40,170],[75,90]],closed=True,mode='Add')
   if name=='left-thigh':cmd('mask.new',layer=layer,vertices=[[35,0],[94,0],[140,100],[160,280],[0,280],[0,110]],closed=True,mode='Add')
   if name=='torso':cmd('mask.new',layer=layer,vertices=[[110,0],[178,0],[186,35],[255,52],[292,84],[292,168],[245,205],[226,296],[70,296],[44,228],[20,166],[0,127],[10,69],[100,39]],closed=True,mode='Add')
   if name.startswith('head-'):
    cmd('layer.addMask',layer=layer,shape='rect',rect=[0,0,w,h-24],mode='Add')
    prop(layer,'masks/#1/feather',[1.5,2.5])

  for name,rect,anchor,pos,scale,parent in DATA:
   if name=='pony':parent='head-control'
   elif parent is None:parent='body-control'
   cmd('layer.setParent',layers=[layers[name]],parent=layers[parent])
  cmd('layer.setParent',layers=[layers['head-control']],parent=layers['torso'])
  for name,expr in [('head-neutral','m<0.5?100:0'),('head-blink','m>=0.5&&m<1.5?100:0'),('head-talk','m>=1.5?100:0')]:
   prop(layers[name],'transform/opacity',expr='var m=thisComp.layer("Face controls").effect("Slider Control")("Slider"); '+expr)
  compinfo=s.call('get_comp',{}); cid=compinfo.get('id',comp.get('comp'))
  cmd('essential.setPrimary',comp=cid);cmd('essential.setName',name='Amaia - full body controls')
  cmd('essential.addProperty',layer=face,path='effects/#1/slider',name='Face: 0 neutral / 1 blink / 2 talk')
  for name in ['body-control','torso','head-control','pony','right-upper-arm','right-forearm','right-hand','left-upper-arm','left-forearm','left-hand','right-thigh','right-shin-foot','left-thigh','left-shin-foot','skirt']:
   cmd('essential.addProperty',layer=layers[name],path='transform/rotation',name=name+' rotation')
  cmd('essential.addProperty',layer=layers['body-control'],path='transform/position',name='Body position')
  s.call('save_project',{'path':str(OUT/'amaia-puppet.ecproj')})
  s.call('render_frame',{'time':0,'path':str(OUT/'assembled.png'),'max_side':0,'inline':False,'transparent':True})
  s.call('render_frame',{'time':0,'path':str(OUT/'assembled-slate.png'),'max_side':0,'inline':False,'transparent':False})
  (OUT/'rig-comp.json').write_text(json.dumps(s.call('get_comp',{}),indent=2))
  (OUT/'rig.json').write_text(json.dumps({'canvas':[1024,1536],'status':'exploratory','fps':24,'layers':layers,'source':'amaia-parts-atlas.png','layout':[dict(name=n,crop=r,atlas_anchor=a,position=p,scale=sc,parent=pa) for n,r,a,p,sc,pa in DATA],'limits':['Front view only; limited joint rotation','Three entire-head replacement states; no full phoneme library','Atlas detail resolution limits closeups; skirt uses separate1024x1536 source' ]},indent=2))
  # Optional native layered painting source at assembled positions.
  cmd('comp.saveFrameAsPsd',path=str(OUT/'amaia-layered.psd'),time=0)
  # Controller demo is a separate composition; editable neutral comp remains untouched.
  demo=cmd('project.duplicate',items=[cid]); did=demo['items'][0];cmd('comp.open',comp=did)
  cmd('comp.settings',name='AMAIA - bounded control demonstration')
  dc=s.call('get_comp',{}); dl={a['name']:a['id'] for a in dc['layers']}
  for n,amount in [('head-control',2.5),('right-upper-arm',3),('right-forearm',-6),('left-forearm',5),('pony',-2)]:
   s.call('add_keyframe',{'layer':dl[n],'path':'transform/rotation','keys':[{'time':i/8,'value':amount*math.sin(math.pi*i/12)*(1 if i<=12 else .5)} for i in range(25)],'interpolation':'hold'})
  s.call('add_keyframe',{'layer':dl['Face controls'],'path':'effects/#1/slider','keys':[{'time':0,'value':0},{'time':.75,'value':1},{'time':.875,'value':0},{'time':1.625,'value':2},{'time':2,'value':0},{'time':2.25,'value':2},{'time':2.5,'value':0}],'interpolation':'hold'})
  s.call('render_frame',{'time':.75,'path':str(OUT/'posed-blink.png'),'max_side':0,'inline':False})
  s.call('render_frame',{'time':1.75,'path':str(OUT/'posed-talk.png'),'max_side':0,'inline':False})
  for i in range(72):s.call('render_frame',{'time':i/24,'path':str(OUT/'rig-frames'/f'{i:04d}.png'),'max_side':1080,'inline':False})
  cmd('comp.open',comp=cid);cmd('comp.openInEssentialGraphics',comp=cid)
  s.call('save_project',{'path':str(OUT/'amaia-puppet.ecproj')})
 subprocess.run(['ffmpeg','-v','error','-y','-framerate','24','-i',str(OUT/'rig-frames/%04d.png'),'-c:v','libx264','-pix_fmt','yuv420p','-crf','18',str(OUT/'amaia-control-demo.mp4')],check=True)
 with Session('photocraft',ROOT,OUT/'paint-evidence') as s:
  s.call('doc_open',{'path':str(OUT/'amaia-layered.psd')})
  for layer in s.call('doc_inspect',{})['layers']:
   if layer['name'] in ['head-blink','head-talk']:
    s.call('command_run',{'id':'layer.setProps','params':{'layer':layer['id'],'visible':False}})
  s.call('doc_save',{'path':str(OUT/'amaia-layered.pcraft')})
  s.call('doc_export',{'path':str(OUT/'amaia-layered.psd'),'format':'psd'})
 print('DONE',OUT)
if __name__=='__main__':run()
