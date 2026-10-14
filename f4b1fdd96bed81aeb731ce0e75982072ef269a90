"""Build this exploratory pack through the installed Craft engines; no generation API."""
import json
from pathlib import Path
import subprocess
from studio.craft import Session
from studio.paths import ROOT, write_json

HERE = Path(__file__).resolve().parent
ART = HERE / 'art'
PUPPET = HERE / 'puppet'


def command(s, command_id, **params):
    return s.call('execute_command', {'command': command_id, 'params': params})


def build_puppet():
    out = PUPPET / 'take-04'
    out.mkdir(exist_ok=False)
    (out/'parts').mkdir()
    (out/'frames').mkdir()
    atlas = ART/'amaia-puppet-atlas-v1.png'
    names = ['head', 'torso', 'left-upper', 'right-upper', 'left-forearm', 'right-forearm']
    with Session('effectcraft', ROOT, out/'evidence') as s:
        s.call('open_project', {'new': True})
        command(s, 'file.import', paths=[str(atlas)])
        for i,name in enumerate(names):
            command(s,'comp.new',name='part-'+name,width=512,height=512,frameRate=24,duration=2)
            command(s,'layer.addItem',item=atlas.name,position=[768-(i%3)*512,512-(i//3)*512])
            s.call('render_frame',{'time':0,'path':str(out/'parts'/f'{name}.png'), 'max_side':0,'inline':False,'transparent':True})
        command(s,'comp.new',name='AMAIA - exploratory bust puppet',width=1024,height=1024,frameRate=24,duration=2)
        command(s,'file.import',paths=[str(out/'parts'/f'{n}.png') for n in names])
        layout = {
            'right-upper': ([270,88],[398,388],55),
            'right-forearm': ([240,45],[349,565],48),
            'left-upper': ([224,100],[625,388],55),
            'left-forearm': ([243,46],[675,575],48),
            'torso': ([256,44],[512,310],85),
            'head': ([255,423],[512,335],55),
        }
        layers = {}
        for name,(anchor,position,scale) in layout.items():
            layer=command(s,'layer.addItem',item=name+'.png',position=position)['layer']
            command(s,'layer.rename',layer=layer,name=name)
            for path,value in [('transform/anchor',anchor),('transform/position',position),('transform/scale',[scale,scale])]:
                s.call('set_property',{'layer':layer,'path':path,'value':value})
            layers[name]=layer
        # Parent commands preserve world pose in the installed engine.
        for child,parent in [('head','torso'),('right-upper','torso'),('left-upper','torso'),
                             ('right-forearm','right-upper'),('left-forearm','left-upper')]:
            command(s,'layer.setParent',layers=[layers[child]],parent=layers[parent])
        write_json(out/'rig.json',{'character':'Amaia','status':'exploratory','kind':'six-part bust cutout control prototype',
                   'canvas':[1024,1024],'fps':24,'frames':48,'layout':layout,'layers':layers,
                   'limits':['No legs, mouth or blink replacements','Restricted rotations; not replacement-drawing acting',
                             'Source pencil likeness missing; author design approval required']})
        for name,amount in [('head',4),('right-forearm',-8),('left-forearm',6)]:
            s.call('add_keyframe',{'layer':layers[name],'path':'transform/rotation',
                'keys':[{'time':0,'value':0},{'time':0.5,'value':amount},{'time':1,'value':0},
                        {'time':1.5,'value':-amount/2},{'time':47/24,'value':0}]})
        s.call('save_project',{'path':str(out/'amaia-puppet.ecproj')})
        write_json(out/'comp.json',s.call('get_comp',{}))
        s.call('render_frame',{'time':0,'path':str(out/'assembled.png'),'max_side':0,'inline':False,'transparent':True})
        for n in range(48):
            s.call('render_frame',{'time':n/24,'path':str(out/'frames'/f'{n:06d}.png'),'max_side':720,'inline':False})
    subprocess.run(['ffmpeg','-v','error','-n','-framerate','24','-i',str(out/'frames/%06d.png'),
                    '-c:v','libx264','-pix_fmt','yuv420p','-crf','18',str(out/'rig-control-preview.mp4')],check=True)
    with Session('filmcraft',ROOT,out/'film-evidence') as s:
        r=s.call('media_import',{'text':str(out/'rig-control-preview.mp4')})
        s.call('command_run',{'id':'file.newSequence','params':{'name':'Amaia rig control test - not episode footage',
                    'width':720,'height':720,'fps':24,'fromItem':r['items'][0]}})
        s.call('command_run',{'id':'file.saveAs','params':{'path':str(out/'rig-preview.filmcraft')}})


def save_art():
    out=HERE/'native-art-v2'
    out.mkdir(exist_ok=False)
    with Session('photocraft',ROOT,out/'evidence') as s:
        for p in sorted(ART.glob('*.png')):
            s.call('doc_open',{'path':str(p)})
            s.call('doc_save',{'path':str(out/(p.stem+'.pcraft'))})


def book():
    out=HERE/'production-book-v3'
    out.mkdir(exist_ok=False)
    pages=[('Amaia - exploratory model sheet',ART/'amaia-model-v2.png'),
           ('Dairon - exploratory model sheet',ART/'dairon-model-v1.png'),
           ('BEFORE boards: S01-01 through S01-08',ART/'storyboard-s01-01-08-v2.png'),
           ('BEFORE boards: S01-09 through S01-15',ART/'storyboard-s01-09-15-v2.png'),
           ('Amaia - six-part construction atlas',ART/'amaia-puppet-atlas-v1.png')]
    with Session('designcraft',ROOT,out/'evidence') as s:
        s.call('new_document',{'title':'Heralds of the Cemi - Arthouse Pack 01','width':864,'height':648,
                              'pages':len(pages),'facingPages':False,'margins':24})
        doc=s.call('inspect_document',{})
        write_json(out/'document-before.json',doc)
        # Spread IDs are discovered; never inferred from page numbers.
        spreads=doc['spreads']
        for i,(title,path) in enumerate(pages):
            sid=spreads[i]['index']
            s.call('execute',{'command':'frame.create','params':{'spread':sid,'rect':[24,18,840,50],
                        'content':'text','text':title+' | EXPLORATORY'}})
            s.call('execute',{'command':'file.place','params':{'spread':sid,'path':str(path),'x':24,'y':65,'width':816}})
        s.call('save_document',{'path':str(out/'arthouse-art-book.designcraft')})
        s.call('execute',{'command':'file.exportPdf','params':{'path':str(out/'arthouse-art-book.pdf'),
                          'title':'Heralds of the Cemi - Exploratory Art Pack','author':'Luis M. Minier / Ilan-Anime'}})


if __name__=='__main__':
    import sys
    {'puppet':build_puppet,'art':save_art,'book':book}[sys.argv[1]]()
