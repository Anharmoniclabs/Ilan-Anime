from pathlib import Path
from PIL import Image, ImageDraw
import numpy as np, json, hashlib
P=Path(__file__).resolve().parent
raw=Image.open(P/'hand-breakdowns.png').convert('RGBA')
(P/'cells').mkdir(exist_ok=True)
rows=[]
sheet=Image.new('RGB',(1200,1620),(55,60,69))
for i in range(36):
    x,y=i%6,i//6
    cel=raw.crop((295*x,148*y,295*(x+1),148*(y+1)))
    path=P/'cells'/f'pose-{i+1:02d}.png';cel.save(path)
    alpha=np.array(cel)[:,:,3]
    yy,xx=np.where(alpha>=128)
    minx,maxx,miny,maxy=int(xx.min()),int(xx.max()),int(yy.min()),int(yy.max())
    # Hand and quill point right in all cells; rightmost opaque point is nib.
    tip=(maxx,round(float(yy[xx==maxx].mean()),2))
    edge_y=yy[xx==minx]
    elbow=(minx,round(float(edge_y.mean()),2))
    registered=(round(tip[0]-elbow[0],2),round(tip[1]-elbow[1],2))
    item={'cell':i+1,'bounds':[minx,miny,maxx,maxy],'nib_candidate':tip,'sleeve_cut_midpoint':elbow,'nib_relative_to_sleeve_cut':registered,'opaque_top_border':int((alpha[0,:]>=128).sum()),'opaque_bottom_border':int((alpha[-1,:]>=128).sum()),'path':str(path.relative_to(P))}
    rows.append(item)
    bg=Image.new('RGBA',cel.size,(55,60,69,255));bg.alpha_composite(cel);bg=bg.convert('RGB');draw=ImageDraw.Draw(bg);draw.ellipse((tip[0]-3,tip[1]-3,tip[0]+3,tip[1]+3),outline=(0,255,255),width=1);draw.line((elbow[0]-3,elbow[1],elbow[0]+3,elbow[1]),fill=(255,255,255))
    thumb=bg.resize((300,150)); sheet.paste(thumb,((i%4)*300,(i//4)*180))
    draw=ImageDraw.Draw(sheet);draw.text(((i%4)*300+8,(i//4)*180+151),f'{i+1:02d}: nib {tip}; root {elbow}',fill=(255,255,255))
(P/'measurements.json').write_text(json.dumps({'method':'Threshold actual alpha at128. Nib candidate is rightmost opaque point; sleeve registration uses leftmost alpha edge midpoint. Automatic landmarks must be visually checked; no rotation, scaling, warping or translation applied to output cells.','cells':rows},indent=2)+'\n')
sheet.save(P/'landmark-inspection.jpg',quality=95)
for a,b,label in [(0,12,'first line'),(12,18,'lift-return'),(18,30,'second line'),(30,36,'final lift')]:
 print(label,[(r['cell'],r['nib_relative_to_sleeve_cut'],r['opaque_top_border'],r['opaque_bottom_border']) for r in rows[a:b]])
