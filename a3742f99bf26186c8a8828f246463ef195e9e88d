from pathlib import Path
import json,hashlib,shutil
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
P=Path(__file__).resolve().parent
S=Path('production/runs/episode1-picture-motion/tasks/amaia-motion').resolve()
def savej(n,x): (P/n).write_text(json.dumps(x,indent=2)+'\n')
for n in ['sources','masks','layers','cels','review']: (P/n).mkdir(exist_ok=True)
prov=[]
for f in sorted((S/'raw').glob('*.png')):
 shutil.copy2(f,P/'sources'/f.name)
 prov.append({'path':str(f),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'provenance':json.load(open(S/'provenance'/(f.stem+'.json')))})
savej('source-provenance.json',prov)
base=Image.open(P/'sources/rest.png').convert('RGB'); w,h=base.size
base.save(P/'layers/stable-plate-native.png')
base.resize((1280,720),Image.Resampling.LANCZOS).save(P/'layers/stable-plate.png')
lock=Image.new('L',(w,h));d=ImageDraw.Draw(lock)
for box in [(280,520,820,730),(520,380,755,620),(900,700,1600,930),(278,390,355,490)]:d.rectangle(box,fill=255)
lock.save(P/'masks/contact-lock.png')
def mask(name,polys,blur=1):
 m=Image.new('L',(w,h));d=ImageDraw.Draw(m)
 for poly in polys:d.polygon(poly,fill=255)
 m=m.filter(ImageFilter.GaussianBlur(blur));m.save(P/'masks'/(name+'.png'));return m
mouth=mask('mouth',[[(552,257),(598,252),(603,280),(594,301),(552,294)]],1.3)
eyes=mask('eyes',[[(495,199),(511,193),(553,195),(562,222),(550,234),(510,234),(495,223)],[(582,192),(600,183),(609,194),(608,219),(587,224),(579,211)]],1)
head=mask('head-down',[[(205,35),(715,35),(715,311),(654,311),(634,318),(615,315),(599,321),(580,316),(564,322),(549,320),(533,332),(518,349),(505,377),(496,395),(475,386),(443,363),(418,346),(330,355),(215,384)]],3)
hd=np.asarray(head).copy();hd[360:620,520:755]=0;head=Image.fromarray(hd);head.save(P/'masks/head-down.png')
raw={n:Image.open(P/'sources'/f'{n}.png').convert('RGB') for n in ['rest','count-a','count-o','blink','head-down']}
used={}
for name,src,m in [('rest','rest',None),('count-a','count-a',mouth),('count-o','count-o',mouth),('look-a','count-a',eyes),('look-o','count-o',eyes),('blink','blink',eyes),('head-down','head-down',head)]:
 if name in ['count-a','count-o']:m=Image.fromarray(np.maximum(np.asarray(mouth),np.asarray(eyes)))
 im=base.copy() if m is None else Image.composite(raw[src],base,m)
 im.save(P/'cels'/f'{name}-native.png');im.resize((1280,720),Image.Resampling.LANCZOS).save(P/'cels'/f'{name}.png')
 overlay=raw[src].convert('RGBA');overlay.putalpha(m if m else Image.new('L',(w,h)));overlay.save(P/'layers'/f'{name}-overlay.png')
 used[name]=im
# Long rests are deliberate counting pauses, all state changes on 3s. No interpolated acting.
sequence=[('rest',18),('look-a',9),('count-a',6),('rest',6),('count-o',6),('look-o',9),('rest',9),('count-a',6),('rest',6),('count-o',6),('rest',9),('blink',3),('rest',9),('look-o',9),('count-a',6),('rest',6),('count-o',6),('rest',9),('blink',3),('head-down',24),('rest',27)]
assert sum(n for _,n in sequence)==192
cursor=0;ex=[]
for name,n in sequence:
 ex.append({'start':cursor,'end_exclusive':cursor+n,'drawing':name,'source':f'cels/{name}.png','cadence':3});cursor+=n
savej('exposures.json',{'shot':'S01-03','status':'exploratory-partial','frames':192,'fps':24,'exposures':ex})
savej('craft-exposures.json',{'shot':'S01-03 partial acting','width':1280,'height':720,'fps':24,'exposures':[{'path':f'cels/{name}.png','frames':n} for name,n in sequence]})
# Output camera MCU to CU. Shared whole-composition transform, independent of drawings.
# Initial MCU crops lap only. Final CU retains Amaia hair, shoulders, and son's face intentionally.
camera=[{'frame':0,'scale':1.15,'x':70,'y':42},{'frame':191,'scale':1.85,'x':210,'y':130}]
savej('camera.json',{'scope':'whole composition only; does not count as acting','keys':camera})
points={'shoulder':[230,318],'child-cheek':[449,389],'cradle':[533,495],'hull':[780,540]}
motion={'shot':'S01-03','status':'exploratory','size':[1280,720],'frames':192,'camera':camera,'elements':[{'name':'stable-reference','kind':'plate','source':str(P/'layers/stable-plate.png')},{'name':'Amaia-replacements','kind':'character','rate':3,'poses':[{'frame':e['start'],'drawing':str(P/e['source']),'points':points} for e in ex]}],'contacts':[{'element':'Amaia-replacements','point':n,'anchor':{'element':'stable-reference','xy':xy},'start':0,'end':192,'tolerance':0.1} for n,xy in points.items()]}
savej('motion.json',motion)
# Exact frozen areas audit before camera. Human review still required for head join.
metrics={}
for name,im in used.items():
 a=np.asarray(im).astype(float);b=np.asarray(base).astype(float)
 regions={'body':[280,520,820,730],'child':[520,360,755,620],'hull':[900,700,1600,930],'shoulder':[278,395,355,490]}
 metrics[name]={k:float(np.abs(a[y:Y,x:X]-b[y:Y,x:X]).max()) for k,(x,y,X,Y) in regions.items()}
savej('composite-lock-metrics.json',metrics)
sheet=Image.new('RGB',(1200,840))
for i,name in enumerate(['rest','count-a','count-o','blink','head-down','rest']):
 sheet.paste(used[name].crop((255,40,720,480)).resize((400,380)),((i%3)*400,(i//3)*420));ImageDraw.Draw(sheet).text(((i%3)*400+10,(i//3)*420+385),name,fill='white')
sheet.save(P/'review/composite-heads.jpg')
print(metrics)
