from pathlib import Path
import json,hashlib
from PIL import Image
from studio.craft import Session
R=Path('/home/alabs/Projects/Ilan-Anime');O=R/'production/character-completion-episode1/reviews';B=R/'production/runs/cemi-90s-production/tasks';M=B/'episode1-modern-assets';C=B/'amaia-complete/contact-s01-13';out=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
with Session('effectcraft',R,O/'modern-slate-evidence') as s:
 s.call('open_project',{'new':True})
 for p in sorted((M/'generated').glob('*.png')):
  w,h=Image.open(p).size;a=Image.open(p).getchannel('A');s.call('execute_command',{'command':'file.import','params':{'paths':[str(p)]}});s.call('execute_command',{'command':'comp.new','params':{'name':p.stem,'width':w,'height':h,'frameRate':24,'duration':1,'background':'#26323e'}});s.call('execute_command',{'command':'layer.addItem','params':{'item':p.name,'position':[w/2,h/2],'index':1}});s.call('render_frame',{'time':0,'path':str(O/(p.stem+'-slate.png')),'max_side':0,'inline':False});out.append({'path':str(p.relative_to(R)),'sha256':sha(p),'size':[w,h],'alpha_range':a.getextrema(),'corner_alpha':[a.getpixel(q) for q in [(0,0),(w-1,0),(0,h-1),(w-1,h-1)]]})
 s.call('save_project',{'path':str(O/'modern-slate-review.ecproj')})
 p=C/'contact-source.ecproj';before=sha(p);state=s.call('open_project',{'path':str(p)});s.call('render_frame',{'time':0,'path':str(O/'contact-independent-slate.png'),'max_side':0,'inline':False});out.append({'path':str(p.relative_to(R)),'sha256':before,'unchanged':before==sha(p),'reopened':True})
with Session('photocraft',R,O/'modern-native-reopen') as s:
 for p in sorted((M/'native').glob('*/master.pcraft'))+[C/'contact-source.pcraft']:
  before=sha(p);v=s.call('doc_open',{'path':str(p)});st=s.call('doc_inspect',{});out.append({'path':str(p.relative_to(R)),'sha256':before,'unchanged':sha(p)==before,'reopened':True,'layers':st['layers']});s.call('command_run',{'id':'file.close','params':{}})
(O/'modern-contact-checks.json').write_text(json.dumps(out,indent=2));print('Checks',len(out))
