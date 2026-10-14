"""Native vector/title animation; no generated paintings are modified."""
import json, math, hashlib
from pathlib import Path
from PIL import Image, ImageDraw
from studio.engine.fx import gen_text, _partial

OUT=Path(__file__).resolve().parent
SIZE=(1280,720)
NAVY='#14202B'; GOLD='#C9A24A'
# One uninterrupted open stroke: center curl -> outer spiral -> triangle's
# descending side -> base. No crossing closed triangle around the spiral.
unit=[]
for i in range(481):
    t=i/480; theta=-1.12-2*math.pi*1.65*(1-t); radius=.72*t
    unit.append([radius*math.cos(theta),radius*math.sin(theta)])
unit += [[.94,.76],[-.85,.76]]
master={'status':'continuity-cleanup proposal','source':'S05-13 selected coin motif, simplified single-stroke construction','path':unit,'closed':False,'stroke_width':.019,'notes':'One shared asset for editorial/coin/stone graphics; scene props still require explicit perspective registration.'}
(OUT/'shared-sigil.json').write_text(json.dumps(master,indent=2))
points=' '.join(f'{x*250+300:.3f},{y*250+300:.3f}' for x,y in unit)
(OUT/'shared-sigil.svg').write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600"><polyline points="{points}" fill="none" stroke="{GOLD}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/></svg>')

def sigil(fraction,center,radius):
    scale=3;layer=Image.new('RGBA',(SIZE[0]*scale,SIZE[1]*scale))
    if fraction>0:
        pts=_partial([((center[0]+x*radius)*scale,(center[1]+y*radius)*scale) for x,y in unit],fraction)
        ImageDraw.Draw(layer).line(pts,fill=GOLD,width=2*scale,joint='curve')
    return layer.resize(SIZE,Image.Resampling.LANCZOS)

def alpha(layer,amount):
    layer=layer.copy();layer.putalpha(layer.getchannel('A').point(lambda v:round(v*max(0,min(1,amount)))))
    return layer

cards={
 'S00-01':96,'S00-02':120,'S02-01':288,'S01-15':96,'S15-09':192,
}
summary=[]
for sid,length in cards.items():
    d=OUT/sid;d.mkdir(exist_ok=True);c=d/'drawings';c.mkdir(exist_ok=True)
    exposures=[];last_digest=None
    for frame in range(0,length,3):
        im=Image.new('RGBA',SIZE,'black' if sid in ['S01-15','S15-09'] else NAVY)
        if sid=='S00-01':
            im=Image.alpha_composite(im,sigil(min(1,frame/72),(640,330),200))
        elif sid=='S00-02':
            title=gen_text({'text':['ELLOS CUENTAN.','NOSOTROS RECORDAMOS.'],'size':40,'tracking':.18,'position':[640,310],'leading':1.65},frame,SIZE)
            sub=gen_text({'text':'They count. We remember. — ABUELA.','size':18,'tracking':.1,'color':GOLD,'position':[640,444]},frame,SIZE)
            im=Image.alpha_composite(im,alpha(Image.alpha_composite(title,sub),frame/24))
        elif sid=='S02-01':
            im=Image.alpha_composite(im,sigil(min(1,frame/72),(640,190),128))
            title=gen_text({'text':'HERALDS OF THE CEMÍ','size':42,'tracking':.13,'position':[640,407]},frame,SIZE)
            sub=gen_text({'text':'EPISODE 1 · 3:07','size':22,'tracking':.15,'position':[640,500]},frame,SIZE)
            text=alpha(Image.alpha_composite(title,sub),(frame-54)/24)
            # One restrained traveling luminance highlight, confined to title ink.
            if 102<=frame<138:
                band=Image.new('RGBA',SIZE,(242,217,155,0));mask=Image.new('L',SIZE)
                x=round(230+(frame-102)/36*850);ImageDraw.Draw(mask).rectangle((x-12,370,x+12,448),fill=45)
                import PIL.ImageChops
                band.putalpha(PIL.ImageChops.multiply(mask,title.getchannel('A')))
                text=Image.alpha_composite(text,band)
            im=Image.alpha_composite(im,text)
        digest=hashlib.sha256(im.tobytes()).hexdigest()
        if digest==last_digest:exposures[-1]['frames']+=3
        else:
            path=c/f'cel-{frame:04d}.png';im.save(path)
            exposures.append({'path':str(path.relative_to(d)),'frames':3})
        last_digest=digest
    manifest={'shot':sid,'width':1280,'height':720,'fps':24,'exposures':exposures}
    (d/'exposures.json').write_text(json.dumps(manifest,indent=2))
    summary.append({'shot':sid,'frames':length,'distinct_cels':len(exposures),'exposures':str((d/'exposures.json').relative_to(OUT)),'audio':False})
(OUT/'editorial-index.json').write_text(json.dumps({'shots':summary,'sigil':'shared-sigil.svg','status':'unreviewed silent editorial animation'},indent=2))
print(json.dumps(summary))
