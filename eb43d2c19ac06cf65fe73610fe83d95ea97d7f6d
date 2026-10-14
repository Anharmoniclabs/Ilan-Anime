from pathlib import Path
import json,math,subprocess
from PIL import Image
from studio.craft import Session
ROOT=Path.cwd();OUT=Path(__file__).resolve().parent
(OUT/'cels').mkdir(exist_ok=True);(OUT/'frames').mkdir(exist_ok=True)
def command(s,c,**p):return s.call('execute_command',{'command':c,'params':p})
with Session('effectcraft',ROOT,OUT/'effect-receipts') as s:
 def c(cmd,**p):return command(s,cmd,**p)
 def prop(layer,path,value):return s.call('set_property',{'layer':layer,'path':path,'value':value})
 def keys(layer,path,ks,hold=False):return s.call('add_keyframe',{'layer':layer,'path':path,'keys':[{'time':t,'value':v} for t,v in ks],'interpolation':'hold' if hold else 'linear'})
 atlas=OUT/'water-cels-atlas.png';aw,ah=Image.open(atlas).size
 s.call('open_project',{'new':True});c('file.import',paths=[str(atlas)])
 crops={'paddle':(95,0,245,1024),'ripple-contact':(540,200,350,205),'ripple-small':(990,190,530,220),'ripple-medium':(395,575,580,285),'ripple-large':(965,570,570,305)}
 for name,(x,y,w,h) in crops.items():
  c('comp.new',name='CEL '+name,width=w,height=h,frameRate=24,duration=6)
  c('layer.addItem',item=atlas.name,position=[aw/2-x,ah/2-y])
  s.call('render_frame',{'time':0,'path':str(OUT/'cels'/f'{name}.png'),'max_side':0,'inline':False,'transparent':True})
 c('file.import',paths=[str(OUT/'night-water.png')]+[str(p) for p in (OUT/'cels').glob('*.png')])
 c('comp.new',name='S01-01 - BEFORE - generated cel draft',width=1920,height=1080,frameRate=24,duration=6,background='#091218')
 bg=c('layer.addItem',item='night-water.png',position=[960,320])['layer'];bw,bh=Image.open(OUT/'night-water.png').size
 prop(bg,'transform/scale',[1920/bw*160,1080/bh*160]);c('layer.rename',layer=bg,name='Painted mangrove water background')
 paddle=c('layer.addItem',item='paddle.png',position=[1160,-30])['layer'];prop(paddle,'transform/anchor',[113,983]);prop(paddle,'transform/scale',[160,160]);c('layer.rename',layer=paddle,name='Rigid generated paddle - drawn exposures on3s')
 stages=[(0,-50,1160,10),(.375,-50,1160,10),(1.125,825,1160,10),(1.65,1340,1170,6),(2.45,1400,1230,-3),(3.125,730,1265,-8),(3.875,-50,1300,-8),(6,-50,1300,-8)]
 def sample(t,k):
  for a,b in zip(stages,stages[1:]):
   if a[0]<=t<=b[0]:
    u=(t-a[0])/(b[0]-a[0]);u=u*u*(3-2*u);return a[k]+u*(b[k]-a[k])
  return stages[-1][k]
 ts=[i/24 for i in range(0,144,3)]
 keys(paddle,'transform/position',[(t,[sample(t,2),sample(t,1)]) for t in ts],True)
 keys(paddle,'transform/rotation',[(t,sample(t,3)) for t in ts],True)
 water=c('layer.addItem',item='night-water.png',position=[960,320])['layer'];prop(water,'transform/scale',[1920/bw*160,1080/bh*160]);c('layer.rename',layer=water,name='Water foreground - submerges paddle')
 c('mask.new',layer=water,vertices=[[0,((760-320)/(1080/bh*1.6)+bh/2)],[bw,((760-320)/(1080/bh*1.6)+bh/2)],[bw,bh],[0,bh]],closed=True,mode='Add')
 for name,start,end,scale in [('ripple-contact',1.0,1.25,100),('ripple-small',1.25,1.875,75),('ripple-medium',1.875,2.75,95),('ripple-large',2.75,5.875,125)]:
  layer=c('layer.addItem',item=name+'.png',position=[1203,760])['layer'];c('layer.rename',layer=layer,name=name+' - replacement water cel')
  prop(layer,'transform/scale',[scale,scale]);keys(layer,'transform/opacity',[(0,0),(start,80),(end,0)],True)
  if name=='ripple-large':keys(layer,'transform/opacity',[(0,0),(start-1/24,0),(start,70),(4.5,35),(5.875,0)])
  if name=='ripple-large':keys(layer,'transform/scale',[(t,[scale*(1+0.12*(t-start)),scale*(1+0.12*(t-start))]) for t in ts if t>=start],True)
  c('essential.addProperty',layer=layer,path='transform/opacity',name=name+' opacity')
 text=c('layer.newText',text='BEFORE',name='BEFORE - live typography',position=[114,970],font='DejaVu Serif',size=30,fill='#b5c2bf',tracking=170)['layer']
 keys(text,'transform/opacity',[(0,0),(.4,85),(5.5,85),(5.958,0)])
 c('essential.addProperty',layer=paddle,path='transform/position',name='Paddle placement')
 c('essential.addProperty',layer=paddle,path='transform/rotation',name='Paddle rotation')
 c('project.delete',items=['CEL '+n for n in crops])
 s.call('save_project',{'path':str(OUT/'S01-01.ecproj')})
 (OUT/'composition.json').write_text(json.dumps(s.call('get_comp',{}),indent=2))
 for n in range(144):
  s.call('render_frame',{'time':n/24,'path':str(OUT/'frames'/f'{n:06d}.png'),'inline':False,'max_side':0})
 c('comp.saveFrameAsPsd',path=str(OUT/'S01-01-layered.psd'),time=1.5)
 print('Native144frames complete',flush=True)
subprocess.run(['ffmpeg','-v','error','-y','-framerate','24','-i',str(OUT/'frames/%06d.png'),'-c:v','libx264','-crf','17','-pix_fmt','yuv420p','-movflags','+faststart',str(OUT/'S01-01-preview.mp4')],check=True)
with Session('filmcraft',ROOT,OUT/'film-receipts') as s:
 r=s.call('media_import',{'text':str(OUT/'S01-01-preview.mp4')});s.call('command_run',{'id':'file.newSequence','params':{'name':'S01-01 - picture draft - audio pending','width':1920,'height':1080,'fps':24,'fromItem':r['items'][0]}});s.call('command_run',{'id':'file.saveAs','params':{'path':str(OUT/'S01-01.filmcraft')}})
with Session('photocraft',ROOT,OUT/'paint-receipts') as s:
 s.call('doc_open',{'path':str(OUT/'S01-01-layered.psd')});s.call('doc_save',{'path':str(OUT/'S01-01-layered.pcraft')})
print('Saved shot projects and current MP4',flush=True)
