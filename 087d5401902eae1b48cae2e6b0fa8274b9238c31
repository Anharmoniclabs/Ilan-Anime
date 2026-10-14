"""S14-03 revision: editable native paths/text, discrete three-frame drawings.
Run this file to create recipe.json; execute through python -m studio craft run.
No source art is modified. All art is authored UI geometry, not character art.
"""
from pathlib import Path
import json,math,random
OUT=Path(__file__).resolve().parent
INK='#202b39'; PAPER='#eee3ce'; GOLD='#c68a48'; BLUE='#bfd0d4'; RED='#ae5d48'; STEEL='#667d87'
steps=[]; objects=[]
def cmd(command,**params):
 steps.append({'command':command,'params':params});return len(steps)
def life(ref,start=0,end=384):
 cmd('layer.timing',layers=[ref],**{'in':start/24,'out':end/24})
def layer(name,start=0,end=384,category='icon'):
 n=cmd('layer.newShape',kind='none',name=name);r=f'${n}.layer';life(r,start,end)
 objects.append({'name':name,'category':category,'start':start,'end':end,'recipe_step':n});return r
def path(r,pts,fill=False,stroke=INK,width=2,closed=False,name='Ink contour'):
 return cmd('shape.newPath',layer=r,vertices=pts,space='comp',closed=closed,fill=fill,stroke=stroke,strokeWidth=width,name=name)
def poly(r,pts,fill,stroke=INK,width=2):return path(r,pts,fill,stroke,width,True)
def ellipse(r,x,y,rx,ry,fill,stroke=INK,width=2):
 return poly(r,[[round(x+rx*math.cos(a*math.pi/16),2),round(y+ry*math.sin(a*math.pi/16),2)] for a in range(32)],fill,stroke,width)
def text(name,x,y,s,size=18,start=0,end=384,color=INK):
 n=cmd('layer.newText',name=name,text=s,font='DejaVu Sans',size=size,fill=color,position=[x,y]);r=f'${n}.layer';life(r,start,end)
 objects.append({'name':name,'category':'text','text':s,'start':start,'end':end,'recipe_step':n});return r
def panel(name,rect,fill,start=0,end=384,hatch=True,category='node'):
 x,y,w,h=rect;r=layer(name,start,end,category)
 poly(r,[[x+5,y+6],[x+w+6,y+5],[x+w+4,y+h+6],[x+3,y+h+5]],'#c6b8a2',False,0)
 poly(r,[[x,y+1],[x+w*.48,y],[x+w,y+2],[x+w-1,y+h],[x+w*.36,y+h-1],[x-1,y+h-2]],fill)
 path(r,[[x+2,y+5],[x+2,y+h-4],[x+15,y+h-3]],False,INK,3.2)
 if hatch:
  for i in range(4):path(r,[[x+w-22+i*5,y+h-4],[x+w-14+i*5,y+h-13]],False,STEEL,.8)
 return r
def node(name,x,y,w,h,labels,start,fill=BLUE,size=18):
 panel(name,(x-w/2,y,w,h),fill,start)
 for i,s in enumerate(labels):text(name+' / type '+str(i),x,y+25+i*25,s,size,start)
def partial(pts,p):
 total=sum(math.dist(a,b) for a,b in zip(pts,pts[1:]));target=total*p;out=[pts[0]]
 for a,b in zip(pts,pts[1:]):
  d=math.dist(a,b)
  if target>=d:out.append(b);target-=d
  else:
   out.append([a[0]+(b[0]-a[0])*target/d,a[1]+(b[1]-a[1])*target/d]);break
 return out
def connector(name,pts,start,duration=12,color=GOLD):
 # Separate editable exposure paths: no tweened path deformation.
 count=duration//3
 for i in range(count):
  r=layer(name+' / ink '+str(i+1),start+i*3,start+(i+1)*3 if i<count-1 else 384,'connector')
  q=partial(pts,(i+1)/count);path(r,q,False,INK,4.8);path(r,q,False,color,2.2)

# Native background: restrained paper flecks, border and inked tab row.
r=layer('Paper field',category='background');poly(r,[[0,0],[1280,0],[1280,720],[0,720]],PAPER,False,0)
r=layer('Paper tooth',category='texture');rng=random.Random(14)
for i in range(220):
 x=rng.randrange(12,1267);y=rng.randrange(53,709)
 path(r,[[x,y],[x+rng.randrange(1,4),y+.5]],False,'#ded2bd',.65)
path(r,[[15,52],[1264,52]],False,INK,2)
tabs=['Aperture','Registry','People','Shell 1','Shell 2','Shell 3','Holding','Youth','Music','Permits','Notes']
for i,label in enumerate(tabs):
 panel('Tab '+str(i+1),(18+i*113,12,108,32),BLUE if i==0 else '#ded3be',hatch=False,category='tab')
 text('Tab label '+str(i+1),72+i*113,34,label,13)
# Scripted polished website facade: landscape motif and controlled white-space.
r=panel('Aperture website facade',(34,80,225,119),'#f6efdf',category='icon')
poly(r,[[43,89],[249,89],[249,146],[43,146]],'#849dab',False,0)
ellipse(r,211,105,14,14,'#e5b66f',False,0)
poly(r,[[43,135],[100,110],[134,128],[183,118],[249,137],[249,147],[43,147]],'#436477',False,0)
poly(r,[[43,146],[101,131],[143,143],[198,133],[249,145]],'#adbeaa',False,0)
text('Website masthead',147,174,'Aperture Civic',19)
path(r,[[79,185],[215,185]],False,GOLD,2)
node('Aperture Civic',505,79,430,121,['APERTURE CIVIC','Registered 2024','Website: five months','No employees on record'],0,BLUE,18)
# Adjust last root line rhythm to fit; four baselines finish at179.
for i,x in enumerate([185,505,825]):
 start=36+i*15
 connector('Aperture to shell '+str(i+1),[[505,200],[505,216],[x,216],[x,238]],start,9)
 node('Shell '+str(i+1),x,238,190,44,['Shell '+str(i+1)],start+9,'#e7d4ad')
for i,x in enumerate([185,505,825]):connector('Shell '+str(i+1)+' to document',[[x,282],[x,301],[505,301],[505,315]],84)
# Paper-to-lunch: twelve distinct replacement drawings; common left/right register.
# Four initial paper frames (96-107), then page corner folds; crease becomes bread cut.
for k in range(15):
 start=96+3*k;end=start+3 if k<14 else 384
 r=layer('Lunch transformation drawing '+str(k).zfill(2),start,end,'replacement_icon')
 x=505;y=362
 if k<4:
  fold=[0,8,18,30][k]
  poly(r,[[x-67,y-45],[x+67-fold,y-45],[x+67,y-45+fold],[x+67,y+36],[x-67,y+36]],'#faf1dc')
  if fold:path(r,[[x+67-fold,y-45],[x+67-fold,y-45+fold],[x+67,y-45+fold]],False,INK,2)
  for j in range(4):path(r,[[x-52,y-25+j*12],[x+35-j*5,y-25+j*12]],False,STEEL,1.5)
 elif k<8:
  # The lower page folds upward in three dimensions as separately drawn polygons.
  z=k-4;bottom=y+36-z*4;crease=y+4-z*3
  poly(r,[[x-67,y-45+z*4],[x+55,y-45+z*4],[x+67,y-29+z*3],[x+67,bottom],[x-67,bottom]],'#f4e8cf')
  poly(r,[[x-67,bottom],[x-56,crease],[x+53,crease-4],[x+67,bottom]],'#d9c6a4')
  path(r,[[x-53,crease+4],[x+49,crease]],False,INK,2)
  for j in range(2):path(r,[[x-49,y-29+z*4+j*10],[x+39,y-29+z*4+j*10]],False,STEEL,1.3)
 elif k<11:
  z=k-8
  # Folded page's inner edges become lettuce/filling before its outer paper turns bread.
  poly(r,[[x-67,y+20],[x+66,y+17],[x+64,y+32],[x-64,y+35]],'#d3a36c')
  poly(r,[[x-67,y+10],[x-52,y+6],[x-36,y+12],[x-22,y+6],[x-8,y+11],[x+8,y+4],[x+30,y+9],[x+49,y+3],[x+66,y+7],[x+65,y+20],[x-66,y+23]],'#799664')
  poly(r,[[x-66,y-24+z*3],[x-51,y-32+z*3],[x+50,y-32+z*3],[x+66,y-20+z*3],[x+66,y+8],[x-66,y+11]],['#ead8b6','#e1bd86','#d9ae71'][z])
  path(r,[[x-51,y-17+z*2],[x-7,y-18+z*2]],False,STEEL,1.4)
  path(r,[[x+3,y-16+z*2],[x+44,y-17+z*2]],False,STEEL,1.4)
 else:
  # Four settled bread drawings: filling compresses, upper crust settles on threes.
  z=k-11;lift=[-6,-2,1,0][z]
  poly(r,[[x-66,y+20],[x+65,y+17],[x+66,y+29],[x+59,y+35],[x-57,y+37],[x-67,y+31]],'#cb9558')
  poly(r,[[x-66,y+14],[x+65,y+11],[x+64,y+23],[x-64,y+27]],'#a76752')
  poly(r,[[x-67,y+6],[x-55,y],[x-43,y+7],[x-29,y],[x-17,y+6],[x-2,y],[x+15,y+5],[x+31,y-1],[x+44,y+4],[x+61,y-2],[x+69,y+5],[x+63,y+14],[x+45,y+12],[x+31,y+18],[x+13,y+14],[x-4,y+19],[x-22,y+15],[x-41,y+20],[x-57,y+17]],'#86965b')
  poly(r,[[x-68,y+lift],[x-62,y-13+lift],[x-47,y-24+lift],[x-22,y-27+lift],[x+7,y-29+lift],[x+39,y-27+lift],[x+61,y-20+lift],[x+70,y-9+lift],[x+65,y+3+lift],[x+42,y+7+lift],[x+9,y+6+lift],[x-21,y+10+lift],[x-52,y+8+lift]],'#e8c287',INK,2.5)
  poly(r,[[x-64,y+lift],[x-39,y+3+lift],[x-6,y+1+lift],[x+26,y+2+lift],[x+66,y-4+lift],[x+64,y+4+lift],[x+36,y+8+lift],[x-20,y+11+lift],[x-53,y+8+lift]],'#c99b62',False,0)
  for j in range(5):path(r,[[x-45+j*20,y-16+lift],[x-39+j*20,y-12+lift]],False,'#73553d',1.5)
  for j in range(6):path(r,[[x-48+j*19,y+31],[x-42+j*19,y+27]],False,'#73553d',1)
text('Lawyer lunch label',505,427,"A lawyer's lunch",17,132)
connector('Lunch to holding',[[505,433],[505,449]],150,9)
node('Holding company',505,449,280,44,['Holding company'],159,'#b6c2a5',19)
for x,start,labels,fill in [(180,180,['Youth digital-wellness','nonprofit'],BLUE),(480,204,['Music-licensing','outfit'],'#d5bcb9'),(780,228,['Development group','Four building permits'],'#e5c294')]:
 connector(labels[0]+' branch',[[505,493],[505,511],[x,511],[x,538]],start)
 node(labels[0],x,538,278,68,labels,start+12,fill)
connector('Development to permit map',[[919,573],[950,573],[950,157],[975,157]],252)
# Abstract block, not a geographic claim. Four distinct building outlines and four pins.
panel('Block map',(975,103,275,342),'#cad0bc',252,category='map')
r=layer('Map roads and parcels',252,category='map')
poly(r,[[986,260],[1239,260],[1239,281],[986,281]],'#eee3ce',False,0)
poly(r,[[1100,155],[1122,155],[1122,430],[1100,430]],'#eee3ce',False,0)
text('Map caption',1112,135,'Four building permits',17,252)
for j,(cx,cy) in enumerate([(1043,370),(1178,212),(1043,212),(1178,370)]):
 r=panel('Building '+str(j+1),(cx-44,cy-42,88,78),'#e4d5b8',252,category='building')
 for wy in [cy-27,cy+13]:
  for wx in [cx-26,cx+18]:poly(r,[[wx,wy],[wx+10,wy],[wx+10,wy+12],[wx,wy+12]],'#9baba7',INK,.9)
 for k,dy in enumerate([-18,-5,2,0]):
  start=264+j*9+k*3
  # Non-overlapping pin exposure; three-frame overshoot, permanent final placement.
  if k==3: start=264+j*9+9
  end=start+3 if k<3 else 384
  rr=layer('Pin '+str(j+1)+' drawing '+str(k),start,end,'pin')
  yy=cy-7+dy
  poly(rr,[[cx,yy+20],[cx-10,yy+2],[cx-11,yy-8],[cx-4,yy-15],[cx+5,yy-14],[cx+11,yy-7],[cx+10,yy+3]],RED if j==0 else GOLD,INK,2.2)
  ellipse(rr,cx,yy-5,4,4,PAPER,INK,1)
 if j==0:text('JC home identification',cx,cy+33,'JC',15,264)
# Discovery terminates at JC's building, with three explicit connected project nodes.
connector('JC building ownership discovery',[[1043,411],[1043,436],[982,436],[982,595]],300,12,RED)
for n,(label,yy,ss) in enumerate([('The Ballroom',497,306),('The arts space',545,312),('The mural',593,318)]):
 connector(label+' ownership link',[[982,yy],[1020,yy]],ss,9,RED)
 panel(label+' discovery node',(1020,yy-20,223,37),'#e6d1a9',ss+9,category='discovery')
 text(label+' editable label',1131,yy+6,label,18,ss+9)
# Script-only final beat. Pie is an unlabelled symbolic icon, not a numeric chart.
for i in range(9):
 start=300+i*3;end=start+3 if i<8 else 384
 rr=layer('Pie chart ink '+str(i),start,end,'chart')
 ellipse(rr,999,663,28,28,BLUE,INK,2)
 a=(i+1)/9*math.pi/2
 pts=[[999,663]]+[[999+28*math.cos(-math.pi/2+t*a/16),663+28*math.sin(-math.pi/2+t*a/16)] for t in range(17)]
 poly(rr,pts,GOLD,INK,1.5)
text('Manny dollar beat line 1',1136,654,'Manny owes',18,324)
text('Manny dollar beat line 2',1136,680,'me a dollar.',18,324)
# Split into bounded batches, converting $ references into global returned layer IDs
# through one saved JSON command script run. Batch tool resolves all refs internally.
recipe={'steps':[{'app':'effectcraft','tool':'open_project','arguments':{'new':True}}, {'app':'effectcraft','tool':'execute_command','arguments':{'command':'comp.new','params':{'name':'S14-03 / research graph r1','width':1280,'height':720,'frameRate':24,'duration':16,'background':PAPER}}},{'app':'effectcraft','tool':'batch','arguments':{'label':'S14-03 editable UI drawing sequence','steps':steps}},{'app':'effectcraft','tool':'save_project','arguments':{'path':'${OUT}/shot.ecproj'}}], 'outputs':['shot.ecproj']}
(OUT/'recipe.json').write_text(json.dumps(recipe,indent=2))
(OUT/'objects.json').write_text(json.dumps({'shot':'S14-03','start_frame':21792,'frames':384,'fps':24,'size':[1280,720],'objects':objects,'status':'exploratory'},indent=2))
print(len(objects),'native objects;',len(steps),'commands')
