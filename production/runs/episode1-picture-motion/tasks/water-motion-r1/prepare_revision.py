from pathlib import Path
out=Path(__file__).resolve().parent
src=Path('production/runs/episode1-picture-motion/tasks/water-motion/build_motion.py').read_text()
src=src.replace("OLD=ROOT/'production/runs/cemi-90s-production/tasks/s01-01'", "OLD=ROOT/'production/runs/episode1-picture-motion/tasks/water-motion'")
src=src.replace("OLD/'S01-01.ecproj'", "OLD/'S01-01-water-motion.ecproj'")
src=src.replace("dst=OUT/'sources'/p.name", "dst=OUT/('drawings' if p.parent.name=='drawings' else 'sources')/p.name")
a=src.index('def arc(');b=src.index('\nbirths=',a)
src=src[:a]+'''def brush_polygon(points,color,opacity):
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
''' + src[b:]
a=src.index('  # dark wet crescent');b=src.index('  if 24<=f<=36:',a)
src=src[:a]+'''  # Broken lateral meniscus, restrained painted swells; no bright U-shaped cap.
  parts.append(arc(mid,762,(r-l)/2+31,10,.06,1.21,3,.65))
  parts.append(arc(mid,762,(r-l)/2+39,8,1.65,3.05,3,.57))
  parts.append(brush_polygon([(l-13,760),(l-4,751),(l+3,747),(l+7,752),(l+3,759),(l+14,763)],'#3a5967',.66))
  parts.append(brush_polygon([(r-10,760),(r-3,755),(r+3,751),(r+10,756),(r+7,760),(r+22,764)],'#365464',.56))
''' + src[b:]
src=src.replace("LIGHT,1.4,.8,BLUE", "'#325165',0,.86,'#325165'")
src=src.replace("LIGHT,1.6,.9", "'#8ea8b4',1.4,.72")
src=src.replace("LIGHT,2,.8", "'#547183',3.1,.68")
# Preserve existing native graph and IDs, with new cel footage at relinked paths.
a=src.index("with Session('effectcraft'");b=src.index("subprocess.run(['ffmpeg'",a)
src=src[:a]+'''# Revise only the existing foreground mask; rigid prop transform keys are untouched.
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
''' + src[b:]
(out/'build_motion.py').write_text(src)
