import json,hashlib,sys,re
from pathlib import Path
from studio.craft import ROOT,Session
OUT=Path(__file__).resolve().parent
manifest=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else OUT/'assembly-ec9957a945c6.json';rows=json.loads(manifest.read_text())['assets'];dest=OUT/('review-'+manifest.stem.removeprefix('assembly-'));dest.mkdir()
notes={
'jc-master.png':'Lean youthful face, short dense curls, charcoal hoodie, headphones and mic puck. No coin held in this pose. A source master only; expression and action banks are missing.',
'manny-master.png':'Very broad shoulders and chest, close crop, warm grin, rust tee and track pants. Conga and performance pose absent; hands remain part of the flat source drawing.',
'mama-master.png':'Gray-streaked pulled-back hair, watchful brow, plum blouse, slacks and rosary. House pose only; younger variant absent.',
'sofia-master.png':'Claw-clipped hair, glasses, teal cardigan, jeans and flats. Laptop and seated acting are absent.',
'rodriguez-master.png':'Cafe keeper source-design proposal. Revised body build and clean-shaven face require identity review; serving and speaking views absent.',
'vale-master.png':'Tall pale silver-haired man in charcoal overcoat and suit, small black notebook. One hand pocketed; notebook elastic needs review. Scripted photo scissors and specific photo pose are absent.',
'window-man-master.png':'Deliberately anonymous dark silhouette with cool rim. Facial identity is withheld; preserve anonymity in episode staging.',
'abuela-hands-master.png':'Aged hands and floral cuffs, open palm bearing a spiral coin; face intentionally absent. Exploratory hand source, not a finished handoff pose. Spiral coin lacks the script spiral-to-triangle detail; exact prop design needs review.'}
with Session('designcraft',ROOT,dest/'evidence') as s:
 (dest/'tools.json').write_text(json.dumps(list(s.tools.values()),indent=2))
 (dest/'commands.json').write_text(json.dumps(s.call('list_commands',{}),indent=2))
 s.call('new_document',{'title':'Episode 1 modern cast — eight exploratory masters','width':1000,'height':1100,'pages':9,'facingPages':False,'margins':25})
 def text(page,rect,body):s.call('execute',{'command':'frame.create','params':{'spread':page,'rect':rect,'content':'text','text':body}})
 text(0,[25,20,975,70],'EPISODE 1 / MODERN CHARACTER SOURCE REVIEW\nEight exploratory drawings, displayed at independent fit scales. Native source libraries only — no rigs or animation approval.')
 for i,r in enumerate(rows):
  x=25+(i%4)*245;y=100+(i//4)*460
  w,h=r['size'];dw=min(225,360*w/h)
  s.call('place_image',{'path':str(ROOT/r['directory']/'source-still.png'),'spread':0,'x':x+(225-dw)/2,'y':y,'width':dw})
  text(0,[x,y+370,x+230,y+415],r['source_name'].replace('-master.png','').replace('-',' ').upper())
 text(0,[25,1030,975,1085],'Sources preserve transparency; white is review-page backing. Exact source hashes and per-file alpha checks are in the assembly manifest. New drawings require separate technical and author review.')
 for i,r in enumerate(rows,1):
  text(i,[25,20,975,65],r['source_name']+' / exploratory source-design review')
  w,h=r['size'];dw=min(900,850*w/h)
  s.call('place_image',{'path':str(ROOT/r['directory']/'source-still.png'),'spread':i,'x':(1000-dw)/2,'y':75,'width':dw})
  text(i,[25,950,975,1080],notes[re.sub(r'-v[0-9]+(?=\.png$)','',r['source_name'])]+'\nSHA-256: '+r['source_sha256']+'\nNative PhotoCraft + layered PSD: protected hidden original and one visible editable copy. Body parts remain flattened.\nSource alpha and premultiplied RGB preserved exactly in native and reopened PSD exports.')
 s.call('save_document',{'path':str(dest/'review-book.designcraft')})
 s.call('execute',{'command':'file.exportPdf','params':{'path':str(dest/'review-book.pdf'),'title':'Episode 1 — eight exploratory character sources'}})
 for i in range(9):s.call('export_png',{'path':str(dest/f'page-{i:02d}.png'),'page':i,'scale':1})
 (dest/'inspection.json').write_text(json.dumps(s.call('inspect_document',{}),indent=2))
 (dest/'hashes.json').write_text(json.dumps({'sources':{r['source_name']:r['source_sha256'] for r in rows},'pdf_sha256':hashlib.sha256((dest/'review-book.pdf').read_bytes()).hexdigest(),'native_sha256':hashlib.sha256((dest/'review-book.designcraft').read_bytes()).hexdigest()},indent=2))
print(dest)
