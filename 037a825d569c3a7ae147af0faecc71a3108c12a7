"""Authored UI animation for the scripted full-screen research graph."""
from pathlib import Path
import json, math, hashlib
from PIL import Image,ImageDraw,ImageFont

OUT=Path(__file__).resolve().parent
W,H=1280,720
INK='#172936';CREAM='#EDE6D6';GOLD='#B38C3D';MUTED='#617174';RED='#9B4539'
fontpath='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
fonts={n:ImageFont.truetype(fontpath,n) for n in [13,15,17,19,22,28]}

def text(draw,xy,s,size=17,color=INK):draw.text(xy,s,font=fonts[size],fill=color)
def box(draw,rect,lines,size=17):
    draw.rounded_rectangle(rect,radius=4,fill=CREAM,outline=INK,width=2)
    x0,y0,x1,y1=rect
    for i,line in enumerate(lines):
        f=fonts[size];w=draw.textlength(line,font=f)
        text(draw,((x0+x1-w)/2,y0+9+i*(size+5)),line,size)
def line(draw,points,p):
    p=max(0,min(1,p));lengths=[0]
    for a,b in zip(points,points[1:]):lengths.append(lengths[-1]+math.dist(a,b))
    target=lengths[-1]*p;done=[points[0]]
    for i in range(1,len(points)):
        if lengths[i]<=target:done.append(points[i])
        else:
            f=(target-lengths[i-1])/(lengths[i]-lengths[i-1]);a,b=points[i-1],points[i]
            done.append((a[0]+f*(b[0]-a[0]),a[1]+f*(b[1]-a[1])));break
    if len(done)>1:draw.line(done,fill=GOLD,width=3,joint='curve')

def frame(q):
    im=Image.new('RGB',(W,H),CREAM);d=ImageDraw.Draw(im)
    # Eleven visible open research tabs. Labels identify views, not invented firms.
    tabs=['Aperture','Registry','People','Shell 1','Shell 2','Shell 3','Holding','Youth','Music','Permits','Notes']
    for i,lab in enumerate(tabs):
        x=18+i*113;d.rectangle((x,12,x+109,45),fill=INK if i==0 else '#D5D2C8',outline=MUTED)
        text(d,(x+8,21),lab,13,CREAM if i==0 else INK)
    text(d,(28,63),'OWNERSHIP / PUBLIC RECORDS',19,MUTED)
    box(d,(300,105,710,191),['APERTURE CIVIC','Registered 2024 · website: five months','No employees on record'],19)
    shell_centers=[185,505,825]
    for i,x in enumerate(shell_centers):
        start=36+i*15
        if q>=start:line(d,[(505,191),(505,213),(x,213),(x,234)],(q-start)/9)
        if q>=start+9:box(d,(x-95,234,x+95,279),[f'Shell company {i+1}'])
    if q>=84:
        for x in shell_centers:line(d,[(x,279),(x,298),(505,298),(505,319)],(q-84)/12)
    if q>=96:
        if q<132:
            # Document card, then four drawn folding states into the sandwich gag.
            t=max(0,min(1,(q-114)/18));x0=451+20*t;x1=559-20*t;y0=317+15*t;y1=382-9*t
            d.polygon([(x0,y0),(x1-12*(1-t),y0),(x1,y0+12*(1-t)),(x1,y1),(x0,y1)],fill=CREAM,outline=INK,width=2)
            for y in [337,347,357]:d.line((x0+10,y,x1-10,y),fill=MUTED,width=1)
        else:
            # Hand-drawn flat graphic: bread, lettuce and filling are distinct cels.
            d.rounded_rectangle((464,332,548,349),radius=10,fill='#C9A465',outline=INK,width=2)
            d.polygon([(465,349),(477,345),(491,351),(505,346),(521,351),(545,347),(545,356),(465,356)],fill='#8A9B62',outline=INK)
            d.rectangle((465,355,547,362),fill='#A16C53',outline=INK)
            d.rounded_rectangle((464,362,548,375),radius=5,fill='#C9A465',outline=INK,width=2)
        text(d,(370,388),"A lawyer's lunch",17,MUTED)
    if q>=150:line(d,[(505,413),(505,433)],(q-150)/9)
    if q>=159:box(d,(365,433,645,478),['Holding company'],19)
    children=[(180,180,['Youth digital-wellness','nonprofit']),(480,204,['Music-licensing','outfit']),(780,228,['Development group','Four building permits'])]
    for x,start,labels in children:
        if q>=start:line(d,[(505,478),(505,496),(x,496),(x,519)],(q-start)/12)
        if q>=start+12:box(d,(x-139,519,x+139,580),labels)
    if q>=252:
        line(d,[(919,550),(953,550),(953,212),(986,212)],(q-252)/12)
        d.rectangle((976,150,1249,487),fill='#D8D7CD',outline=MUTED,width=2)
        text(d,(991,163),'FOUR PERMITS',17)
        d.rectangle((1072,204,1102,469),fill='#C4B99C')
        for y in [221,337,447]:d.line((985,y,1238,y),fill=CREAM,width=8)
        for j,(x,y) in enumerate([(1010,250),(1131,250),(1010,368),(1131,368)]):
            d.rectangle((x,y,x+88,y+62),fill=CREAM,outline=MUTED,width=2)
            start=264+j*9
            if q>=start:
                # Pin drops on threes with a restrained overshoot.
                t=min(1,(q-start)/9);cy=y+24-round(18*(1-t)**2)
                d.ellipse((x+36,cy-7,x+50,cy+7),fill=RED if j==0 else GOLD,outline=INK,width=1)
                d.polygon([(x+39,cy+5),(x+43,cy+13),(x+47,cy+5)],fill=RED if j==0 else GOLD)
                text(d,(x+4,y+44),'JC / home' if j==0 else f'Permit {j+1}',13)
        text(d,(996,457),'Block diagram',13,MUTED)
    if q>=300:
        d.line((30,610,1248,610),fill=MUTED,width=1)
        text(d,(42,635),'THE BALLROOM  /  THE ARTS SPACE  /  THE MURAL',19)
        text(d,(42,667),'His building. His work.',17,RED)
        # Scripted pie-chart gag, deliberately no fabricated quantitative legend.
        d.ellipse((991,603,1055,667),fill=INK)
        d.pieslice((991,603,1055,667),start=-90,end=-90+min(1,(q-300)/24)*92,fill=GOLD)
        text(d,(1069,624),'Manny owes',15)
        text(d,(1069,646),'me a dollar.',15)
    return im

d=OUT/'drawings';d.mkdir(exist_ok=True);ex=[];last=None
for q in range(0,384,3):
    im=frame(q);digest=hashlib.sha256(im.tobytes()).hexdigest()
    if digest==last:ex[-1]['frames']+=3
    else:
        p=d/f'graph-{q:04d}.png';im.save(p);ex.append({'path':str(p.relative_to(OUT)),'frames':3})
    last=digest
(OUT/'exposures.json').write_text(json.dumps({'shot':'S14-03','width':W,'height':H,'fps':24,'exposures':ex},indent=2))
(OUT/'action-timing.json').write_text(json.dumps({'frames':384,'cadence':3,'phases':{'0-35':'Aperture facts and11tabs','36-95':'Three shells and linked paper','96-149':'Document folds into lawyer lunch','150-251':'Holding andthreebranches','252-299':'Four permits andhomepin','300-383':'Project connection andpiechart gag'},'audio':False,'note':'UI-only scripted shot. Block diagram is illustrative, not geographic evidence.'},indent=2))
print(len(ex),'distinct UI cels')
