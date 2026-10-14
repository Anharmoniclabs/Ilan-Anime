from pathlib import Path
import json,math
from PIL import Image
from studio.craft import Session
R=Path('/home/alabs/Projects/Ilan-Anime');O=R/'production/runs/cemi-90s-production/tasks/episode1-cast';d=json.load(open(O/'cast.json'));rows=d['entries'];pages=math.ceil(len(rows)/4)
with Session('designcraft',R,O/'native-evidence') as s:
 s.call('new_document',{'title':'Episode 1 character inventory — submitted planning index','width':792,'height':612,'pages':pages,'facingPages':False})
 def txt(p,rect,text,size=10):
  x=s.call('execute',{'command':'frame.create','params':{'spread':p,'rect':rect,'content':'text','text':text}})
  s.call('execute',{'command':'type.char','params':{'attrs':{'size':size,'leading':{'kind':'points','value':size+3}}}})
 for p in range(pages):
  txt(p,[28,18,764,45],f'EPISODE 1 / CHARACTER INVENTORY / {p+1} of {pages}',16)
  txt(p,[28,46,764,78],'Submitted planning index • reference thumbnails are not finished assets • full shot list and hashes in cast.json',10)
  for j,r in enumerate(rows[p*4:p*4+4]):
   y=86+j*122
   if r['references']:
    s.call('place_image',{'path':str(R/r['references'][0]['path']),'spread':p,'x':28,'y':y,'width':min(115,100*Image.open(R/r['references'][0]['path']).width/Image.open(R/r['references'][0]['path']).height)})
   else:txt(p,[28,y+8,148,y+98],'No dedicated\nreference found' if r['appearance'] not in ['mentioned-only','text-ui-only','audio-only','optional-implied'] else 'Text / mention /\nconditional only',10)
   txt(p,[161,y,764,y+22],r['name'],13)
   shot=', '.join(r['shot_evidence']);shot=shot if len(shot)<150 else shot[:147]+'… (full list in JSON)'
   text=f"{r['appearance']} | {r['era']} | {r['production_state']}\n{r['script_constraints']}\nShots: {shot}"
   txt(p,[161,y+24,764,y+116],text,10)
  txt(p,[28,588,764,606],'Amaia r2: design + limited face controls approved. Full character animation remains unfinished. No new approvals.',9)
 s.call('save_document',{'path':str(O/'episode1-cast.designcraft')})
 evidence=s.call('inspect_document',{});(O/'native-inspection.json').write_text(json.dumps(evidence,indent=2))
 print(s.call('execute',{'command':'file.exportPdf','params':{'path':str(O/'episode1-cast.pdf'),'title':'Episode 1 Character Inventory','author':'Production inventory','compressImages':True}}))
 for p in [0,4,pages-1]:s.call('export_png',{'path':str(O/f'index-page-{p+1}.png'),'page':p,'scale':1})
 print('pages',pages,'overset',[x for x in evidence['stories'] if x.get('overset')])
