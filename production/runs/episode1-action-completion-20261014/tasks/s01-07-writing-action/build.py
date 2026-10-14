"""Bounded S01-07 cel assembly. Generated poses, never a warped full scene."""
from pathlib import Path
import json, hashlib, math
from PIL import Image, ImageDraw, ImageFilter
P=Path(__file__).resolve().parent
R=P.parents[4]
SOURCE=R/'production/runs/episode1-anime90s-scenes/tasks/opening/generated/S01-07.png'
A=Image.open(P/'action-sheet.png').convert('RGB')
T=[]
for i in range(9):
    c,r=i%3,i//3
    T.append(A.crop((round(c*A.width/3),round(r*A.height/3),round((c+1)*A.width/3),round((r+1)*A.height/3))).resize((591,296)))
# Polygons follow actual ink contours. No generated ledger pixels enter arm cels.
outlines={
1:[(0,0),(190,0),(165,103),(210,130),(239,118),(266,122),(292,133),(305,147),(308,172),(301,178),(285,189),(244,198),(200,202),(170,213),(139,219),(65,220),(19,209),(0,188)],
2:[(0,0),(190,0),(170,111),(209,133),(236,137),(271,123),(296,125),(320,141),(334,156),(337,174),(326,183),(309,189),(269,199),(221,203),(192,211),(167,218),(72,222),(19,210),(0,188)],
4:[(0,0),(190,0),(171,88),(207,97),(235,101),(254,72),(278,65),(302,67),(321,88),(330,105),(321,113),(313,128),(299,143),(277,154),(252,162),(233,163),(211,184),(195,199),(179,202),(163,193),(80,211),(21,208),(0,185)],
5:[(0,0),(190,0),(168,100),(205,118),(230,126),(252,109),(275,109),(296,119),(313,140),(315,162),(311,170),(295,182),(276,190),(253,193),(227,190),(207,183),(207,199),(192,211),(169,217),(151,211),(74,222),(21,210),(0,190)],
6:[(0,0),(190,0),(170,106),(212,126),(232,130),(254,115),(276,116),(299,130),(317,150),(319,170),(311,177),(301,184),(285,193),(268,197),(240,199),(219,196),(205,208),(185,216),(161,219),(72,222),(20,212),(0,190)],
7:[(0,0),(190,0),(170,104),(217,126),(253,133),(275,126),(301,112),(326,115),(349,128),(362,145),(372,165),(370,171),(358,179),(341,188),(313,194),(282,197),(254,194),(236,199),(211,208),(193,213),(185,208),(76,223),(20,211),(0,190)]}
quills={
1:[(191,36),(216,42),(246,60),(266,85),(283,127),(311,190),(309,191),(281,129),(257,116),(234,101),(212,76)],
2:[(210,36),(234,42),(261,59),(286,84),(306,125),(341,186),(338,187),(304,129),(272,113),(250,96),(229,71)],
4:[(215,4),(241,7),(271,25),(290,46),(302,65),(337,122),(335,125),(299,68),(269,60),(247,40),(232,22)],
5:[(219,27),(243,32),(270,50),(288,75),(296,121),(319,190),(317,191),(293,124),(268,111),(244,86),(232,58)],
6:[(214,35),(241,40),(269,61),(288,86),(297,121),(322,190),(319,191),(295,123),(268,109),(247,85),(229,58)],
7:[(244,34),(268,39),(295,58),(319,81),(338,120),(375,180),(373,182),(335,122),(306,111),(284,91),(261,62)]}
nibs={1:(311,190),2:(340,186),4:(336,123),5:(318,190),6:(321,190),7:(374,181)}
(P/'layers').mkdir(exist_ok=True)
(P/'cels').mkdir(exist_ok=True)
T[0].save(P/'layers/locked-ledger.png')
arms={}
for i,poly in outlines.items():
    mask=Image.new('L',(591,296));d=ImageDraw.Draw(mask);d.polygon(poly,fill=255);d.polygon(quills[i],fill=255)
    arm=T[i].convert('RGBA');arm.putalpha(mask)
    arm.save(P/f'layers/arm-{i}.png');arms[i]=arm
def full(im):
    # Script permits pen/page closeup; this intentionally frames the writing region.
    return im.crop((32,0,558,296)).resize((1280,720),Image.Resampling.LANCZOS)
def ink(draw, end, offset=0):
    # Story-required handwritten marks, no invented readable dialogue/text.
    pts=[]
    for x in range(309,int(end)+1):
        y=190-(x-311)*9/63+offset + math.sin((x-309)*1.7)*.75
        pts.append((x,y))
    if len(pts)>1: draw.line(pts,fill=(65,34,20),width=1)
timeline=[];contacts=[]
def save(name,im,frames,pose=None,offset=0,line=0):
    path=f'cels/{name}.png';im.convert('RGB').save(P/path)
    timeline.append({'path':path,'frames':frames})
    if pose is not None:
        contacts.append({'cel':path,'pose':pose,'nib':[nibs[pose][0],nibs[pose][1]+offset], 'page_contact':pose!=4 and 'return-above' not in name,'line':line,'registration_translation':[0,offset]})
def cel(name,pose,frames,line=1,offset=0,first=False,end=None):
    im=T[0].convert('RGBA');d=ImageDraw.Draw(im)
    if line==2 or first:ink(d,374)
    if line and pose!=4:ink(d,nibs[pose][0] if end is None else end,8 if line==2 else 0)
    if line==2 and pose==4:ink(d,374,8)
    im.alpha_composite(arms[pose],(0,offset));save(name,full(im),frames,pose,offset,line)
save('wide-establish',Image.open(SOURCE).resize((1280,720)),24)
cel('line-one-start',1,12)
cel('line-one-breakdown',6,9)
cel('line-one-middle',2,12)
cel('line-one-end',7,15)
cel('pen-lift',4,12,line=0,first=True)
cel('return-above-line',5,9,line=0,offset=-9,first=True)
cel('line-two-start',1,12,line=2,offset=8)
cel('line-two-breakdown',6,9,line=2,offset=8)
cel('line-two-middle',2,12,line=2,offset=8)
cel('line-two-end',7,18,line=2,offset=8)
cel('finish-lift',4,24,line=2,first=True)
assert sum(x['frames'] for x in timeline)==168
(P/'exposures.json').write_text(json.dumps({'shot':'S01-07','width':1280,'height':720,'fps':24,'exposures':timeline},indent=2)+'\n')
(P/'contacts.json').write_text(json.dumps({'coordinate_space':'591x296 closeup before 16:9 crop','locked_ledger':'layers/locked-ledger.png','contacts':contacts,'limits':['6 distinct generated replacement poses; deliberate exposures range 9–24 frames (all multiples of 3), not 56 distinct drawings.','Second line reuses registered drawn arm bank at +8px page offset.','Generated end poses 3 and 8 excluded: nib crosses book gutter.','No sound; technical and author review remain outstanding.']},indent=2)+'\n')
sheet=Image.new('RGB',(1280,720))
for i,t in enumerate(timeline[:12]):
    thumb=Image.open(P/t['path']).resize((320,180));sheet.paste(thumb,((i%4)*320,(i//4)*180))
sheet.save(P/'contact-sheet.jpg',quality=95)
provenance={'source':str(SOURCE.relative_to(R)),'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'generated_sha256':hashlib.sha256((P/'action-sheet.png').read_bytes()).hexdigest(),'tool':'built-in imagegen','calls':1,'host_agent_id':'/root/counter_writing','status':'exploratory','frame_count':168,'fps':24,'retained_raw_generated_sheet':True}
(P/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
