from pathlib import Path
import json, math, shutil, hashlib, subprocess
import numpy as np
from PIL import Image
from studio.craft import Session
ROOT=Path.cwd();OUT=Path(__file__).resolve().parent
OLD=ROOT/'production/runs/episode1-picture-motion/tasks/water-motion'
for n in ['sources','drawings','frames','qa']: (OUT/n).mkdir(parents=True,exist_ok=True)
project=json.loads((OLD/'S01-01-water-motion.ecproj').read_text());sources=[]
for item in project['items'].values():
 k=item.get('kind',{})
 if k.get('type')=='Footage' and k.get('path'):
  p=Path(k['path']);dst=OUT/('drawings' if p.parent.name=='drawings' else 'sources')/p.name
  shutil.copy2(p,dst);k['path']=str(dst)
  sources.append(dict(source=str(p),snapshot=str(dst),sha256=hashlib.sha256(dst.read_bytes()).hexdigest()))
(OUT/'source-provenance.json').write_text(json.dumps(dict(native_source=str(OLD/'S01-01-water-motion.ecproj'),native_sha256=hashlib.sha256((OLD/'S01-01-water-motion.ecproj').read_bytes()).hexdigest(),items=sources),indent=2))
(OUT/'S01-01-relinked-source.ecproj').write_text(json.dumps(project))
stages=[(0,-50,1160,10),(.375,-50,1160,10),(1.125,825,1160,10),(1.65,1340,1170,6),(2.45,1400,1230,-3),(3.125,730,1265,-8),(3.875,-50,1300,-8),(6,-50,1300,-8)]
def sample(f,k):
 t=f/24
 for a,b in zip(stages,stages[1:]):
  if a[0]<=t<=b[0]:
   u=(t-a[0])/(b[0]-a[0]);u=u*u*(3-2*u);return a[k]+u*(b[k]-a[k])
 return stages[-1][k]
alpha=np.array(Image.open(OUT/'sources/paddle.png').convert('RGBA'))[:,:,3]
outline=[]
for y in range(alpha.shape[0]):
 xs=np.where(alpha[y]>150)[0]
 if len(xs):outline.append((xs[0],y,xs[-1]))
poly=[(a,y) for a,y,b in outline]+[(b,y) for a,y,b in reversed(outline)]
def transform(f,x,y):
 a=math.radians(sample(f,3));x=(x-113)*1.6;y=(y-983)*1.6
 return sample(f,2)+x*math.cos(a)-y*math.sin(a),sample(f,1)+x*math.sin(a)+y*math.cos(a)
def crossing(f):
 pts=[transform(f,*p) for p in poly];v=[]
 for (x,y),(xx,yy) in zip(pts,pts[1:]+pts[:1]):
  if (y<760<=yy) or (yy<760<=y):v.append(x+(xx-x)*(760-y)/(yy-y))
 return (min(v),max(v)) if v else None
def tip(f):return transform(f,115,991)
BLUE='#426b7f';LIGHT='#83a6b3';INK='#091820'
def path(d,color=BLUE,width=3,opacity=1,fill='none'):
 return f'<path d="{d}" stroke="{color}" stroke-width="{width}" fill="{fill}" stroke-linecap="round" stroke-linejoin="round" opacity="{opacity:.3f}"/>'
def brush_polygon(points,color,opacity):
 return path('M '+' L '.join(f'{x:.2f},{y:.2f}' for x,y in points)+' Z',color,0,opacity,color)
def arc(cx,cy,rx,ry,start,end,w,opacity,phase=0):
 # Registered pressure-shaped brush islands. Fixed tooth pattern travels with wave.
 result=[]
 for j in range(5):
  a0=start+(end-start)*(j/5+.008)
  a1=start+(end-start)*((j+1)/5-.025)
  outer=[];inner=[]
  for i in range(19):
   u=i/18;a=a0+(a1-a0)*u
   tooth=math.sin(a*83+phase)*1.1+math.sin(a*151)*.65
   x=cx+rx*math.cos(a)+math.sin(a*27)*2.4
   y=cy+ry*math.sin(a)+math.sin(a*31)*1.1
   pressure=math.sin(math.pi*u)**.5
   thick=(3.2+w*1.4)*(0.8+.35*math.sin(a*13))*pressure
   outer.append((x,y-thick*.3+tooth*pressure))
   inner.append((x+math.sin(a*43)*2,y+thick+tooth*pressure))
  color=['#315064','#294858','#3b596c','#284757','#395a6b'][j]
  result.append(brush_polygon(outer+inner[::-1],color,opacity*.85))
  # Small, broken upper-plane catches, never a continuous bright contour.
  if j in (0,3):
   pts=outer[5:12]+[(x+2,y+1.6) for x,y in reversed(outer[5:12])]
   result.append(brush_polygon(pts,'#72909f',opacity*.32))
 return ''.join(result)
def ring(cx,cy,age,strength=1):
 if age<0 or age>92:return ''
 rx=18+age*5.9;ry=3+age*1.16
 op=strength*(1-age/105)
 return '<g mask="url(#paddlemask)">'+''.join(arc(cx,cy,rx,ry,a,b,4.5-age/70,op,0) for a,b in [(0.06,1.12),(1.39,2.81),(3.16,4.22),(4.58,5.95)])+'</g>'

births=[78,81,84];drops=[]
for j,b in enumerate(births):
 x,y=tip(b);vx=[-1.5,0.9,-.45][j];vy=-1.8;g=.9
 impact=b+(-vy+math.sqrt(vy*vy+2*g*(760-y)))/g
 drops.append(dict(id=j,birth=b,x=x,y=y,vx=vx,vy=vy,g=g,impact=impact,impact_x=x+vx*(impact-b)))
exposures=[]
for f in range(0,144,3):
 parts=[];contact=crossing(f);states=[]
 # expanding disconnected arcs from entry and release; never scale full image
 for born,cx,strength in [(24,1160,.8),(36,1174,.58),(75,1266,.8)]:
  parts.append(ring(cx,760,f-born,strength))
 if contact:
  l,r=contact;mid=(l+r)/2
  # Broken lateral meniscus, restrained painted swells; no bright U-shaped cap.
  parts.append(arc(mid,762,(r-l)/2+31,10,.06,1.21,3,.65))
  parts.append(arc(mid,762,(r-l)/2+39,8,1.65,3.05,3,.57))
  parts.append(brush_polygon([(l-13,760),(l-4,751),(l+3,747),(l+7,752),(l+3,759),(l+14,763)],'#3a5967',.66))
  parts.append(brush_polygon([(r-10,760),(r-3,755),(r+3,751),(r+10,756),(r+7,760),(r+22,764)],'#365464',.56))
  if 24<=f<=36:
   age=f-24
   for side in [-1,1]:
    x=mid+side*(25+age*5);y=752-4*age+.32*age*age
    parts.append(path(f'M {x:.1f},{y-5:.1f} Q {x+side*6:.1f},{y:.1f} {x+side*10:.1f},{y+2:.1f}',BLUE,3,.85))
 tx,ty=tip(f)
 if f in (75,78):
  # short drainage filament behind the lifting tip, narrowing before detachment
  tail=min(760,ty+(20 if f==75 else 35))
  parts.append(path(f'M {tx:.2f},{ty-4:.2f} Q {tx-4:.2f},{(ty+tail)/2:.2f} {tx+2:.2f},{tail:.2f}',LIGHT,2.2,.65))
 for d in drops:
  age=f-d['birth']
  if age<0:continue
  if f<d['impact']:
   x=d['x']+d['vx']*age;y=d['y']+d['vy']*age+.5*d['g']*age*age
   length=9+min(9,max(0,d['vy']+d['g']*age)*.5)
   parts.append(path(f'M {x:.2f},{y-length:.2f} C {x-5:.2f},{y-2:.2f} {x-5:.2f},{y+4:.2f} {x:.2f},{y+5:.2f} C {x+5:.2f},{y+4:.2f} {x+5:.2f},{y-2:.2f} {x:.2f},{y-length:.2f} Z','#325165',0,.86,'#325165'))
   parts.append(path(f'M {x-1:.2f},{y-3:.2f} L {x-1:.2f},{y+1:.2f}','#8ea8b4',1.4,.72))
   states.append(dict(id=d['id'],state='detached-falling',x=x,y=y,blade_tip=[tx,ty]))
  else:
   impact_age=f-d['impact'];x=d['impact_x']
   parts.append(ring(x,760,impact_age,.75))
   if impact_age<7:
    h=18*(1-impact_age/7)
    parts.append(path(f'M {x-14:.2f},762 Q {x-6:.2f},{757-h:.2f} {x-4:.2f},758 Q {x:.2f},{750-h:.2f} {x+5:.2f},759 Q {x+10:.2f},{758-h*.5:.2f} {x+17:.2f},762','#547183',3.1,.68))
   states.append(dict(id=d['id'],state='impact-ring',age=impact_age,x=x,y=760))
 maskpoly=' '.join(f'{x:.2f},{y:.2f}' for x,y in [transform(f,*p) for p in poly])
 defs='<defs><clipPath id="above"><rect width="1920" height="760"/></clipPath><mask id="paddlemask"><rect width="1920" height="1080" fill="white"/><polygon points="'+maskpoly+'" fill="black" clip-path="url(#above)"/></mask></defs>'
 svg='<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080">'+defs+''.join(parts)+'</svg>'
 name=f'water-fx-{chr(65+f//78)}{chr(65+(f//3)%26)}'
 s=OUT/'drawings'/f'{name}.svg';png=s.with_suffix('.png');s.write_text(svg)
 subprocess.run(['rsvg-convert',str(s),'-o',str(png)],check=True)
 exposures.append(dict(start_frame=f,frames=3,path=str(png),svg=str(s),contact_span=list(contact) if contact else None,blade_tip=[tx,ty],droplets=states))
(OUT/'exposures.json').write_text(json.dumps(dict(shot='S01-01',width=1920,height=1080,fps=24,frames=144,waterline_y=760,exposures=exposures,droplet_physics=drops,notes='New vector effect drawings registered to native rigid paddle silhouette; each drawing held3frames. Gravity px/frame^2; impact at waterline.'),indent=2))
# Revise only the existing foreground mask; rigid prop transform keys are untouched.
comp=project['items']['128']['kind']
foreground=next(l for l in comp['layers'] if l['id']==175)
mask=foreground['props']['children'][0]['children'][0]['children'][0]
keys=[]
for f in range(0,144,3):
 contact=crossing(f)
 vertices=[]
 for x in range(0,1921,8):
  y=760
  if contact:
   l,r=contact;mid=(l+r)/2;span=(r-l)/2+28
   envelope=max(0,1-abs(x-mid)/span)
   y=760+envelope*(-3+5*math.sin((x-mid)*.073)+2*math.sin(x*.21))
  vertices.append([(x-960)/1.8373205741626793+836,(y-320)/1.8363443145589798+470.5])
 vertices += [[1672,941],[0,941]]
 v={'vertices':vertices,'in_tangents':[[0,0]]*len(vertices),'out_tangents':[[0,0]]*len(vertices),'closed':True}
 keys.append({'time':f*10584000000,'value':{'t':'Path','v':v},'in_interp':'Hold','out_interp':'Hold','in_ease':[],'out_ease':[],'continuous':False,'auto_bezier':False,'spatial_in':[0,0,0],'spatial_out':[0,0,0],'spatial_auto':False,'spatial_continuous':False,'roving':False})
mask['keys']=keys;mask['value']=keys[0]['value']
foreground['name']='Water foreground - registered irregular contact occlusion r1'
(OUT/'S01-01-relinked-source.ecproj').write_text(json.dumps(project))
with Session('effectcraft',ROOT,OUT/'native-receipts') as s:
 s.call('open_project',{'path':str(OUT/'S01-01-relinked-source.ecproj')})
 s.call('execute_command',{'command':'comp.open','params':{'comp':128}})
 s.call('save_project',{'path':str(OUT/'S01-01-water-motion.ecproj')})
 (OUT/'composition.json').write_text(json.dumps(s.call('get_comp',{}),indent=2))
 for n in range(144):
  s.call('render_frame',{'time':n/24,'path':str(OUT/'frames'/f'{n:06d}.png'),'inline':False,'max_side':0})
  if n%24==0:print('Rendered',n,flush=True)
 print('Native144frame render saved',flush=True)
subprocess.run(['ffmpeg','-v','error','-y','-framerate','24','-i',str(OUT/'frames/%06d.png'),'-c:v','libx264','-crf','17','-pix_fmt','yuv420p','-movflags','+faststart',str(OUT/'S01-01-silent-preview.mp4')],check=True)
with Session('filmcraft',ROOT,OUT/'film-receipts') as s:
 r=s.call('media_import',{'text':str(OUT/'S01-01-silent-preview.mp4')})
 s.call('command_run',{'id':'file.newSequence','params':{'name':'S01-01 silent water motion','width':1920,'height':1080,'fps':24,'fromItem':r['items'][0]}})
 s.call('command_run',{'id':'file.saveAs','params':{'path':str(OUT/'S01-01-water-motion.filmcraft')}})
print('DONE',flush=True)

