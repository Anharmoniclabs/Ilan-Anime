"""Native Craft extraction and editable sheet packaging of generated artwork."""
from pathlib import Path
import json, hashlib
from studio.craft import Session

ROOT = Path.cwd()
BASE = Path(__file__).resolve().parent
OUT = BASE / 'library-v2'
SPECS = {
 'turnaround': (1536,1024,[('front',(30,0,380,1024)),('three-quarter',(413,0,369,1024)),('profile',(796,0,320,1024)),('back',(1120,0,406,1024))]),
 'expressions': (1536,1024,[(n,((i%3)*512,(i//3)*512,512,512)) for i,n in enumerate(['neutral','concern','grief','resolve','fear','reassurance'])]),
 'mouths': (1254,1254,[(n,((i%3)*418,(i//3)*418,418,418)) for i,n in enumerate(['closed-a','closed-b','parted','open','wide','rounded','pursed','teeth','tongue'])]),
 'hands': (1536,1024,[(n,((i%4)*384,(i//4)*512,384,512)) for i,n in enumerate(['right-relaxed','right-open','right-cupped','right-grip','left-relaxed','left-open','left-cupped','left-grip'])]),
 'seated-son-poses': (1024,1536,[('cradle',(10,0,550,753)),('look-back',(565,0,459,756)),('lean',(0,739,548,797)),('count',(549,739,475,797))]),
 'ribs-son-closeup': (1536,1024,[('sleep-speaking',(0,0,1536,1024))]),
}
POSE_EXCLUSIONS = {
 'cradle': [[140,746,240,20]],
 'look-back': [[720,741,130,25]],
 'lean': [[0,739,150,12],[380,739,168,12]],
 'count': [[549,739,170,20],[840,739,184,20]],
}

def main():
 OUT.mkdir(exist_ok=True)
 (OUT/'cels').mkdir(exist_ok=True)
 entries=[]; sheets=[]; first=None
 with Session('effectcraft',ROOT,OUT/'effect-evidence') as s:
  def cmd(c,**p):return s.call('execute_command',{'command':c,'params':p})
  s.call('open_project',{'new':True})
  cmd('file.import',paths=[str(BASE/'generated'/f'{n}.png') for n in SPECS])
  for sheet,(sw,sh,cells) in SPECS.items():
   for name,(x,y,w,h) in cells:
    label=f'{sheet} - {name}'
    cmd('comp.new',name=label,width=w,height=h,frameRate=24,duration=1,background='#26323e')
    layer=cmd('layer.addItem',item=f'{sheet}.png',position=[sw/2-x,sh/2-y],index=1)['layer']
    cmd('layer.rename',layer=layer,name=label)
    if sheet=='seated-son-poses':
     for rect in POSE_EXCLUSIONS[name]:cmd('layer.addMask',layer=layer,shape='rect',rect=rect,mode='Subtract')
    s.call('add_effect',{'layer':layer,'effect':'ec.color.levels','values':{'channel':4,'inBlack':0.012,'inWhite':1.0,'alphaInBlack':0.012}})
    target=OUT/'cels'/f'{sheet}--{name}.png'
    s.call('render_frame',{'time':0,'path':str(target),'max_side':0,'transparent':True,'inline':False})
    entries.append({'name':label,'file':str(target.relative_to(BASE)),'source':f'generated/{sheet}.png','crop':[x,y,w,h], 'status':'reference/cel source; shot registration pending'})
   cmd('comp.new',name=f'SHEET - {sheet}',width=sw,height=sh,frameRate=24,duration=1,background='#26323e')
   for name,(x,y,w,h) in cells:
    layer=cmd('layer.addItem',item=f'{sheet}.png',position=[sw/2,sh/2],index=1)['layer']
    cmd('layer.rename',layer=layer,name=name)
    cmd('layer.addMask',layer=layer,shape='rect',rect=[x,y,w,h],mode='Add')
    if sheet=='seated-son-poses':
     for rect in POSE_EXCLUSIONS[name]:cmd('layer.addMask',layer=layer,shape='rect',rect=rect,mode='Subtract')
    s.call('add_effect',{'layer':layer,'effect':'ec.color.levels','values':{'channel':4,'inBlack':0.012,'inWhite':1.0,'alphaInBlack':0.012}})
   if first is None:first=s.call('get_comp',{})['id']
   psd=OUT/f'{sheet}.psd'
   cmd('comp.saveFrameAsPsd',path=str(psd),time=0)
   s.call('render_frame',{'time':0,'path':str(OUT/f'{sheet}-slate.png'),'max_side':0,'inline':False})
   sheets.append({'name':sheet,'layers':len(cells),'psd':str(psd.relative_to(BASE))})
  cmd('comp.open',comp=first)
  s.call('save_project',{'path':str(OUT/'Amaia-asset-library.ecproj')})
  s.call('open_project',{'path':str(OUT/'Amaia-asset-library.ecproj')})
  reopened=s.call('get_comp',{})
 with Session('photocraft',ROOT,OUT/'paint-evidence') as s:
  for spec in sheets:
   s.call('doc_open',{'path':str(BASE/spec['psd'])})
   got=s.call('doc_inspect',{})
   if len(got['layers'])!=spec['layers']:raise ValueError(f"Layer count differs for {spec['name']}")
   target=OUT/f"{spec['name']}.pcraft"
   s.call('doc_save',{'path':str(target)})
   spec['pcraft']=str(target.relative_to(BASE))
 manifest={'status':'exploratory additions to approved Amaia design','assets':entries,'sheets':sheets,'reopened_main':reopened.get('name'),'source_hashes':{n:hashlib.sha256((BASE/'generated'/f'{n}.png').read_bytes()).hexdigest() for n in SPECS},'limits':['Views and poses are individual drawings, not registered frame sequences.','Two closed mouth cells are near-duplicates; names describe shapes, not validated phonemes.','Sleeping son is a new proposed design derived for script poses.','Joint experiments are deliberately excluded from this reference library; working controls are in native/.']}
 (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print(json.dumps({'individual_assets':len(entries),'editable_sheets':len(sheets),'output':str(OUT)}))

if __name__=='__main__':main()
