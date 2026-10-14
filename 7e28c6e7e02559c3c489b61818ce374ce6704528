import json
from studio.craft import ROOT,Session
OUT=ROOT/'production/runs/cemi-90s-production/tasks/river-character-library'
rows=json.loads((OUT/'library-manifest.json').read_text())['characters']
with Session('designcraft',ROOT,OUT/'index-evidence') as s:
 s.call('new_document',{'title':'River cast — source reference library, not rigs','width':1000,'height':850,'pages':12,'facingPages':False,'margins':25})
 for i,r in enumerate(rows):
  s.call('execute',{'command':'frame.create','params':{'spread':i,'rect':[25,15,975,55],'content':'text','text':f"{i+1:02d} / {r['name']} — exploratory source reference"}})
  s.call('place_image',{'path':str(OUT/r['id']/'source.png'),'spread':i,'x':25,'y':60,'width':950})
  s.call('execute',{'command':'frame.create','params':{'spread':i,'rect':[25,700,975,835],'content':'text','text':'Native: '+r['id']+'.pcraft\n'+r['identity_observations']+'\nRequired: '+r['missing_art']+'\nUnapproved historical reference. No separated joints, rig, pose registration or motion approval.'}})
 s.call('save_document',{'path':str(OUT/'river-source-index.designcraft')})
 print(s.call('execute',{'command':'file.exportPdf','params':{'path':str(OUT/'river-source-index.pdf'),'title':'River cast source reference library','author':'Ilan Anime production'}}))
 print(s.call('export_png',{'path':str(OUT/'index-page-01.png'),'page':0,'scale':1}))
 (OUT/'index-inspection.json').write_text(json.dumps(s.call('inspect_document',{}),indent=2))
checks=[]
with Session('photocraft',ROOT,OUT/'reopen-evidence') as s:
 for r in rows:
  p=OUT/'native'/f"{r['id']}.pcraft"
  s.call('doc_open',{'path':str(p)})
  state=s.call('doc_inspect',{})
  checks.append({'id':r['id'],'native_reopened':True,'state':state})
  s.call('command_run',{'id':'file.close','params':{}})
(OUT/'reopen-checks.json').write_text(json.dumps(checks,indent=2))
