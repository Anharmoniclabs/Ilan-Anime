from pathlib import Path
import json,hashlib
from PIL import Image
from studio.engine.fx import gen_sigil,gen_text
out=Path(__file__).resolve().parent
size=(1920,1080)
cards={
'S00-01':[('sigil',dict(center=[960,540],radius=235,width=2,color='#C9A24A'))],
'S00-02':[('text',dict(text=['ELLOS CUENTAN.','NOSOTROS RECORDAMOS.'],size=40,tracking=.18,position=[960,465],leading=1.65)),('text',dict(text='They count. We remember. — ABUELA.',size=18,tracking=.1,color='#C9A24A',position=[960,665]))],
'S02-01':[('sigil',dict(center=[960,310],radius=150,width=2,color='#C9A24A')),('text',dict(text='HERALDS OF THE CEMÍ',size=42,tracking=.13,position=[960,610])),('text',dict(text='EPISODE 1 · 3:07',size=22,tracking=.15,position=[960,750]))],
'S15-09':[]}
for sid,layers in cards.items():
 im=Image.new('RGBA',size,'black' if sid=='S15-09' else '#14202B')
 for kind,spec in layers:im=Image.alpha_composite(im,(gen_sigil if kind=='sigil' else gen_text)(spec,100,size))
 f=out/(sid+'.png');assert not f.exists();im.convert('RGB').save(f)
 r=dict(shot_id=sid,path=str(f),sha256=hashlib.sha256(f.read_bytes()).hexdigest(),size=list(size),tool='native studio.engine.fx editorial generator',layers=layers,key_moment='Static editorial endpoint per script; no animated draw-on/audio claimed.',animation=False,author_approved=False,status='native-editorial-frame')
 (out/(sid+'.json')).write_text(json.dumps(r,indent=2))
print('4 native editorial cards saved')
