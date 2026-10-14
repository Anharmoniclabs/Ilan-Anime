"""Package saved generated drawings using native masks, without inventing paint."""
from pathlib import Path
import json, hashlib
from studio.craft import Session

ROOT=Path.cwd()
OUT=Path(__file__).resolve().parent
def main():
    (OUT/'library').mkdir(exist_ok=True)
    entries=[]
    with Session('effectcraft',ROOT,OUT/'library-evidence') as s:
        def cmd(c,**p):return s.call('execute_command',{'command':c,'params':p})
        def prop(l,p,v):return s.call('set_property',{'layer':l,'path':p,'value':v})
        s.call('open_project',{'new':True})
        files=list((OUT/'generated').glob('*.png'))+[OUT/'amaia-master.png']
        cmd('file.import',paths=[str(p) for p in files])
        def comp(name,item,rect=None,pivot=None,position=None,scale=100):
            cmd('comp.new',name=name,width=1024,height=1536,frameRate=24,duration=2,background='#26323e')
            l=cmd('layer.addItem',item=item,position=[512,768],index=1)['layer']
            cmd('layer.rename',layer=l,name=name)
            if rect:cmd('layer.addMask',layer=l,shape='rect',rect=rect,mode='Add')
            if pivot:prop(l,'transform/anchor',pivot)
            if position:prop(l,'transform/position',position)
            prop(l,'transform/scale',[scale,scale])
            s.call('render_frame',{'time':0,'path':str(OUT/'library'/f'{name}.png'),'max_side':0,'transparent':True,'inline':False})
            cmd('comp.saveFrameAsPsd',path=str(OUT/'library'/f'{name}.psd'),time=0)
            entries.append({'name':name,'source':item,'rect':rect,'anchor':pivot,'position':position,'scale':scale,'canvas':[1024,1536],'comp':s.call('get_comp',{})['id']})
        comp('approved-neutral','amaia-master.png')
        comp('body-underpaint','body-underpaint.png')
        # Four source views, no synthesized intermediate turn. Each uses the same
        # scale and foot baseline; source column centers are explicit anchors.
        for name,rect,pivot in [('view-front',[30,0,380,1024],[223,990]),('view-three-quarter',[413,0,369,1024],[589,990]),('view-profile',[796,0,320,1024],[972,990]),('view-back',[1120,0,406,1024],[1322,990])]:
            comp(name,'turnaround.png',rect,pivot,[512,1518],150)
        # Keep atlas coordinates and pixels intact. These are source-space
        # pieces, not a claim of fit to the approved master or moving joints.
        for side,x,w in [('screen-left',60,400),('screen-right',570,400)]:
            comp(f'{side}-whole-arm','arms-only.png',[x,100,w,1350])
        for side,x,w in [('screen-left',130,300),('screen-right',590,310)]:
            for part,y,h in [('upper-arm',0,550),('forearm',560,530),('hand',1100,420)]:
                comp(f'{side}-{part}','arm-joints.png',[x,y,w,h])
        # Editable isolated-piece atlas; masks select existing source paint.
        cmd('comp.new',name='ARM JOINT ATLAS - source coordinates',width=1024,height=1536,frameRate=24,duration=2,background='#26323e')
        for e in entries:
            if e['source']!='arm-joints.png':continue
            l=cmd('layer.addItem',item='arm-joints.png',position=[512,768],index=1)['layer']
            cmd('layer.rename',layer=l,name=e['name'])
            cmd('layer.addMask',layer=l,shape='rect',rect=e['rect'],mode='Add')
        cmd('comp.saveFrameAsPsd',path=str(OUT/'library'/'arm-joints-separated.psd'),time=0)
        s.call('render_frame',{'time':0,'path':str(OUT/'library'/'arm-joints-separated-slate.png'),'max_side':0,'inline':False})
        s.call('save_project',{'path':str(OUT/'amaia-asset-library.ecproj')})
    with Session('photocraft',ROOT,OUT/'library-paint-evidence') as s:
        s.call('doc_open',{'path':str(OUT/'library'/'arm-joints-separated.psd')})
        layers=s.call('doc_inspect',{})
        (OUT/'library'/'paint-layer-inspection.json').write_text(json.dumps(layers,indent=2))
        s.call('doc_save',{'path':str(OUT/'amaia-joint-library.pcraft')})
    data={'status':'submitted','art_direction_mode':'CHARACTER_ASSET','authority':'approved-reference.json','entries':entries,'source_sha256':{str(p.relative_to(OUT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},'limits':['Turnaround views share scale and foot baseline, but are discrete model views, not animation cels.','Joint pieces retain atlas coordinates; anatomical registration and hidden-surface overlap are unvalidated.','No synthesized paint, deformation, or geometric joint patches.','Only approved-neutral is the approved master; generated new views and pieces remain exploratory.']}
    (OUT/'asset-library.json').write_text(json.dumps(data,indent=2))
    print('Saved native library with',len(entries),'independent assets')
if __name__=='__main__':main()
