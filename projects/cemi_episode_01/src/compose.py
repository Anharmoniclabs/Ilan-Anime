"""General exposure-sheet compositor for replacement cels and cutout layers.

Each layer can use a held PNG, a directory of numbered replacement PNGs,
or explicit cel exposures. Transform keys interpolate on that layer's clock.
RGBA is preserved. The camera is evaluated on every output frame.
This module has no illustration generation and no hidden API calls.
"""
from pathlib import Path
import argparse,json,subprocess,sys
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]

def interpolate(keys,frame,defaults):
    if not keys:return defaults.copy()
    keys=sorted(keys,key=lambda k:k['frame'])
    a=keys[0];b=keys[-1]
    for k in keys:
        if k['frame']<=frame:a=k
        if k['frame']>=frame:b=k;break
    if frame<=keys[0]['frame']:a=b=keys[0]
    if frame>=keys[-1]['frame']:a=b=keys[-1]
    t=0 if a['frame']==b['frame'] else (frame-a['frame'])/(b['frame']-a['frame'])
    if a.get('ease')=='smooth':t=t*t*(3-2*t)
    if a.get('ease')=='hold':t=0
    return {k:a.get(k,v)+(b.get(k,v)-a.get(k,v))*t for k,v in defaults.items()}

class Compositor:
    def __init__(self,spec):self.spec=spec;self.cache={};self.size=tuple(spec.get('size',[1280,720]))
    def load(self,path):
        if path not in self.cache:
            self.cache[path]=Image.open(ROOT/path).convert('RGBA')
        return self.cache[path].copy()
    def draw(self,frame):
        s=self.spec;canvas=Image.new('RGBA',self.size,tuple(s.get('background',[20,32,43,255])))
        for layer in s['layers']:
            if not layer.get('in',0)<=frame<layer.get('out',s['frames']):continue
            local=frame-layer.get('in',0);rate=layer.get('rate',3);q=local//rate*rate
            src=layer.get('source')
            if layer.get('sequence'):
                bank=layer['sequence'];index=q//rate
                index=index%len(bank) if layer.get('loop') else min(index,len(bank)-1)
                src=bank[index]
            for exp in layer.get('exposures',[]):
                if exp['start']<=q<exp['end']:src=exp['source'];break
            if not src:continue
            im=self.load(src)
            if layer.get('fit_canvas',False):im=im.resize(self.size,Image.Resampling.LANCZOS)
            p=interpolate(layer.get('keys',[]),q,{'x':0,'y':0,'scale':1,'angle':0,'opacity':1})
            if p['scale']!=1:im=im.resize((max(1,round(im.width*p['scale'])),max(1,round(im.height*p['scale']))),Image.Resampling.BICUBIC)
            pivot=layer.get('pivot',[im.width/2,im.height/2])
            if p['angle']:im=im.rotate(p['angle'],Image.Resampling.BICUBIC,center=tuple(pivot))
            if p['opacity']<1:im.putalpha(im.getchannel('A').point(lambda x:round(x*max(0,p['opacity']))))
            canvas.alpha_composite(im,(round(p['x']),round(p['y'])))
        cam=interpolate(s.get('camera',[]),frame,{'x':0,'y':0,'scale':1,'angle':0})
        if cam['angle']:canvas=canvas.rotate(cam['angle'],Image.Resampling.BICUBIC)
        if cam['scale']!=1 or cam['x'] or cam['y']:
            z=cam['scale'];w,h=self.size
            canvas=canvas.transform(self.size,Image.Transform.AFFINE,(1/z,0,w/2-w/(2*z)-cam['x'],0,1/z,h/2-h/(2*z)-cam['y']),Image.Resampling.BICUBIC)
        return canvas.convert('RGB')

def export(spec,out,draft=False):
    if spec.get('status')!='animation_ready' and not draft:
        raise ValueError('This shot is not animation_ready. Finish its layers and review before export. --draft is explicit.')
    c=Compositor(spec);w,h=c.size
    cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pixel_format','rgb24','-video_size',f'{w}x{h}','-framerate','24','-i','pipe:0']
    if spec.get('audio'):cmd+=['-i',str(ROOT/spec['audio'])]
    cmd+=['-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart']
    if spec.get('audio'):cmd+=['-c:a','aac','-b:a','192k','-af','apad','-t',str(spec['frames']/24)]
    cmd+=[str(out)];p=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    for f in range(spec['frames']):p.stdin.write(c.draw(f).tobytes())
    p.stdin.close()
    if p.wait():raise RuntimeError('ffmpeg failed')

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('spec');ap.add_argument('--out',required=True);ap.add_argument('--draft',action='store_true');a=ap.parse_args()
    export(json.loads(Path(a.spec).read_text()),Path(a.out),a.draft)
