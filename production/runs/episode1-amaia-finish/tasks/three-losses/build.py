from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
import numpy as np,json,shutil,hashlib
P=Path(__file__).resolve().parent
R=Path('production/runs/episode1-picture-motion-continuation/tasks/amaia-registration').resolve()
N=Path('production/runs/episode1-full-picture/amaia-breakdowns').resolve()
def sj(n,o): (P/n).write_text(json.dumps(o,indent=2)+'\n')
for d in ['sources','masks','layers','cels','review','decoded']: (P/d).mkdir(exist_ok=True)
for d in ['masks','cels','layers']:
 for f in (R/d).glob('*.png'): shutil.copy2(f,P/d/f.name)
for f in [R/'sources/rest.png',R/'sources/head-down.png',N/'head-early.png',N/'head-lower-candidate.png',N/'three-seated-memories.png']: shutil.copy2(f,P/'sources'/f.name)
base=Image.open(P/'sources/rest.png').convert('RGB'); size=base.size
head=Image.new('L',size)
ImageDraw.Draw(head).polygon([(205,35),(715,35),(715,309),(655,309),(630,318),(609,326),(593,337),(579,350),(568,357),(549,357),(531,356),(518,359),(505,377),(496,395),(475,386),(443,363),(418,346),(330,355),(215,384)],fill=255)
head=head.filter(ImageFilter.GaussianBlur(1))
a=np.asarray(head).copy();a[360:620,520:755]=0;head=Image.fromarray(a);head.save(P/'masks/new-head.png')
for n in ['head-early','head-lower-candidate']:
 raw=Image.open(P/'sources'/f'{n}.png').convert('RGB')
 cel=Image.composite(raw,base,head)
 cel.save(P/'cels'/f'{n}-native.png');cel.resize((1280,720),Image.Resampling.LANCZOS).save(P/'cels'/f'{n}.png')
 patch=raw.convert('RGBA');patch.putalpha(head);patch.save(P/'layers'/f'{n}-overlay.png')
# Drawn source landmarks, manually inspected at native coordinates. No pose transforms.
sj('head-landmarks.json',{'method':'Manual visual landmarks, approximate native pixels; all drawings identity transform','order':['rest','head-early','head-down','head-lower-candidate'],'landmarks':{'rest':{'near_eye':[540,213],'chin':[566,318]},'head-early':{'near_eye':[541,233],'chin':[561,332]},'head-down':{'near_eye':[553,248],'chin':[559,344]},'head-lower-candidate':{'near_eye':[554,260],'chin':[554,351]}},'return':'reverse identical registered drawings; no synthesized or warped inbetweens'})
# Three hand-traced silhouette masks, separated along the visible overlapping contours.
polys=[[(724,504),(731,480),(759,455),(778,429),(785,391),(793,353),(810,318),(834,295),(836,279),(850,263),(876,255),(897,260),(918,279),(929,290),(960,302),(983,323),(1002,349),(1004,374),(991,397),(974,434),(958,456),(963,481),(979,511),(991,558),(1020,620),(1060,676),(1140,722),(1139,862),(892,866),(877,803),(856,733),(829,686),(811,602),(758,548)],[(958,455),(980,433),(1009,419),(1025,370),(1045,326),(1072,292),(1105,281),(1130,271),(1152,274),(1175,292),(1200,309),(1215,335),(1235,350),(1243,379),(1233,420),(1221,450),(1233,490),(1236,534),(1246,582),(1263,642),(1290,694),(1298,730),(1370,751),(1417,802),(1416,861),(1140,862),(1139,722),(1060,676),(1020,620),(991,558),(979,511)],[(1239,544),(1248,516),(1270,487),(1293,466),(1311,432),(1345,392),(1359,366),(1381,349),(1414,339),(1451,342),(1487,358),(1517,382),(1525,412),(1526,451),(1531,484),(1557,517),(1559,558),(1567,604),(1585,635),(1594,671),(1599,709),(1620,727),(1640,755),(1648,789),(1644,831),(1630,858),(1416,861),(1417,802),(1370,751),(1298,730),(1263,642),(1246,582)]]
ghost=Image.open(P/'sources/three-seated-memories.png').convert('RGBA')
ga=np.asarray(ghost).copy();ga[:,:,:3]=np.clip(ga[:,:,:3].astype(float)*1.3+np.array([55,65,85]),0,255).astype('uint8');ghost=Image.fromarray(ga)
# The source gunwale is in front. Restore it and everything below it, including bench.
occ=Image.new('L',size); dr=ImageDraw.Draw(occ)
dr.polygon([(698,451),(754,492),(828,534),(911,575),(1004,613),(1104,650),(1208,686),(1330,724),(1453,762),(1582,800),(1672,827),(1672,941),(0,941),(0,780),(233,864),(892,864),(854,736),(822,682),(814,621),(779,515)],fill=255)
# Explicit living-character exclusion; candidate must never replace Amaia or child.
dr.polygon([(0,0),(722,0),(722,444),(758,483),(764,535),(807,595),(826,678),(862,737),(895,869),(0,941)],fill=255)
occ.save(P/'masks/foreground-occlusion.png')
for i,poly in enumerate(polys,1):
 m=Image.new('L',size);ImageDraw.Draw(m).polygon(poly,fill=255);m=m.filter(ImageFilter.GaussianBlur(.6))
 a=np.asarray(m).copy();a[np.asarray(occ)>0]=0;m=Image.fromarray(a);m.save(P/'masks'/f'memory-{i}.png')
 im=ghost.copy();im.putalpha(m);im.save(P/'layers'/f'memory-{i}-native.png');im.resize((1280,720),Image.Resampling.LANCZOS).save(P/'layers'/f'memory-{i}.png')
# Stable held framing for three separate count/fade beats. Then camera closes.
seq=[('rest',18),('look-a',6),('count-a',6),('look-a',12),('rest',9),('look-o',6),('count-o',6),('look-o',12),('rest',9),('look-a',6),('count-a',6),('look-o',12),('rest',9),('blink',3),('head-early',6),('head-down',6),('head-lower-candidate',18),('head-down',6),('head-early',6),('rest',12),('look-a',9),('rest',9)]
assert sum(n for _,n in seq)==192,sum(n for _,n in seq)
ex=[];cursor=0
for name,n in seq:ex.append({'start':cursor,'end_exclusive':cursor+n,'drawing':name,'source':f'cels/{name}.png'});cursor+=n
beats=[{'memory':1,'start':24,'end':42,'opacity_start':.25,'opacity_end':0},{'memory':2,'start':57,'end':75,'opacity_start':.25,'opacity_end':0},{'memory':3,'start':90,'end':108,'opacity_start':.25,'opacity_end':0}]
cam=[{'frame':0,'scale':100,'position':[640,360]},{'frame':111,'scale':100,'position':[640,360]},{'frame':191,'scale':155,'position':[910,520]}]
sj('action-timeline.json',{'shot':'S01-03','status':'exploratory','frames':192,'fps':24,'size':[1280,720],'sound':'silent','count':'fourteen to eleven: exactly THREE losses','cadence':3,'exposures':ex,'apparitions':beats,'camera':cam})
points={'shoulder':[230,318],'child-cheek':[449,389],'cradle':[533,495],'hull':[780,540]}
sj('motion.json',{'shot':'S01-03','status':'exploratory','size':[1280,720],'frames':192,'elements':[{'name':'stable-reference','kind':'plate','source':str(P/'layers/stable-plate.png')},{'name':'Amaia-replacements','kind':'character','rate':3,'poses':[{'frame':e['start'],'drawing':str(P/e['source']),'points':points} for e in ex]}],'contacts':[{'element':'Amaia-replacements','point':n,'anchor':{'element':'stable-reference','xy':xy},'start':0,'end':192,'tolerance':.1} for n,xy in points.items()]})
metrics={}
for n,_ in seq:
 im=np.asarray(Image.open(P/'cels'/f'{n}-native.png')).astype(int);b=np.asarray(base).astype(int)
 metrics[n]={k:int(np.abs(im[y:Y,x:X]-b[y:Y,x:X]).max()) for k,(x,y,X,Y) in {'body':(280,520,820,730),'child':(520,360,755,620),'hull':(900,700,1600,930),'shoulder':(278,395,355,490)}.items()}
sj('contact-pixels.json',metrics)
sj('source-hashes.json',[{'path':str(f),'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in [R/'sources/rest.png',R/'sources/head-down.png',N/'head-early.png',N/'head-lower-candidate.png',N/'three-seated-memories.png']])
steps=[]
def tool(t,a):steps.append({'app':'effectcraft','tool':t,'arguments':a})
def cmd(c,p):tool('execute_command',{'command':c,'params':p})
tool('open_project',{'new':True});cmd('comp.new',{'name':'S01-03 three losses draft','width':1280,'height':720,'frameRate':24,'duration':8})
paths=list(dict.fromkeys(str(P/e['source']) for e in ex))+[str(P/'layers'/f'memory-{i}.png') for i in range(1,4)]
cmd('file.import',{'paths':paths})
def camera(start):
 for k in cam:
  for path,v in [('transform/scale',[k['scale']]*2),('transform/position',k['position'])]:cmd('prop.addKey',{'layer':'#1','path':path,'time':(k['frame']-start)/24,'value':v})
for e in ex:
 cmd('layer.addItem',{'item':Path(e['source']).name,'time':e['start']/24,'duration':(e['end_exclusive']-e['start'])/24,'index':1});camera(e['start'])
for b in beats:
 cmd('layer.addItem',{'item':f"memory-{b['memory']}.png",'time':0,'duration':8,'index':1});camera(0)
 for f,v in [(0,25),(b['start'],25),(b['end'],0),(191,0)]:cmd('prop.addKey',{'layer':'#1','path':'transform/opacity','time':f/24,'value':v})
tool('save_project',{'path':'${OUT}/shot.ecproj'})
for f in range(192):tool('render_frame',{'time':f/24,'path':f'${{OUT}}/{f:06}.png','max_side':0,'inline':False})
sj('native-recipe.json',{'steps':steps,'outputs':['shot.ecproj','000191.png']})
# Preflight compositing preview at native resolution and head ordering sheet.
im=base.convert('RGBA')
for i in range(1,4):
 q=Image.open(P/'layers'/f'memory-{i}-native.png');q.putalpha(q.getchannel('A').point(lambda v:round(v*.25)));im=Image.alpha_composite(im,q)
im.save(P/'review/ghost-preflight.png')
sheet=Image.new('RGB',(1400,430))
for i,n in enumerate(['rest','head-early','head-down','head-lower-candidate']):
 q=Image.open(P/'cels'/f'{n}-native.png').crop((300,60,660,400)).resize((350,390));sheet.paste(q,(i*350,0));ImageDraw.Draw(sheet).text((i*350+5,400),n,fill='white')
sheet.save(P/'review/head-order.jpg')
print('built',len(steps),'steps',metrics)
