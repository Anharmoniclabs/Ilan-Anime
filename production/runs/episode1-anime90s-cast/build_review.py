"""Build a native PDF layout embedding original image RGB and alpha unchanged."""
from pathlib import Path
import json, zlib, hashlib
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
RUN = Path(__file__).resolve().parent
items = []
for task in ['main-cast','age-variants','historical-cast','supporting-cast','river-cast','ensemble-cast']:
    m = RUN/'tasks'/task/'manifest.json'
    if not m.exists(): continue
    d = json.loads(m.read_text())
    entries = d.get('sources',d.get('entries',d.get('assets',[])))
    for e in entries:
        if task=='supporting-cast' and e.get('id')=='banner-people': continue
        p = Path(e.get('file',e.get('path','')))
        if not p.is_absolute(): p=ROOT/p
        if not p.is_file() or p.suffix.lower()!='.png': continue
        ids=e.get('cast_ids',[e.get('cast_id',e.get('id',p.stem))])
        if ids==['banner-people-v2']: ids=['banner-people']
        items.append(dict(task=task,label=e.get('name',e.get('id',p.stem)),cast_ids=ids,path=str(p.relative_to(ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
amaia=ROOT/'production/runs/cemi-90s-production/tasks/amaia-assets-r2/amaia-master.png'
items.insert(0,dict(task='approved-style-reference',label='Amaia (existing approved reference)',cast_ids=['amaia'],path=str(amaia.relative_to(ROOT)),sha256=hashlib.sha256(amaia.read_bytes()).hexdigest()))
def normalize(cid):
    if cid=='lost-ghosts': return 'lost-survivor-ghosts'
    if cid.startswith('mama-younger-'): return 'mama-younger'
    if cid.startswith('canoe-survivor-'): return 'canoe-survivors'
    if cid.startswith('ballroom-hero-couple-'): return 'ballroom-hero-couples'
    if cid.startswith('ballroom-crowd-bank-'): return 'ballroom-crowd'
    return cid
for it in items: it['cast_ids']=[normalize(c) for c in it['cast_ids']]
(RUN/'source-index.json').write_text(json.dumps({'status':'exploratory source generation; not rigs or animation','items':items},indent=2))
cast=json.loads((ROOT/'production/runs/cemi-90s-production/tasks/episode1-cast/cast.json').read_text())['entries']
coverage=[]
for e in cast:
    paths=[i['path'] for i in items if e['id'] in i['cast_ids']]
    required=e['appearance'] in ['on-screen','background-group','partial-body','photo-only']
    coverage.append(dict(id=e['id'],name=e['name'],appearance=e['appearance'],generation_required=required,sources=paths,status=('source_available' if paths else 'MISSING' if required else 'no_drawn_source_required')))
(RUN/'cast-coverage.json').write_text(json.dumps({'entries':coverage,'required_roles':sum(x['generation_required'] for x in coverage),'covered_roles':sum(x['generation_required'] and bool(x['sources']) for x in coverage),'missing':[x['id'] for x in coverage if x['status']=='MISSING']},indent=2))

objects=[b'',b'']
def obj(b):
    objects.append(b);return len(objects)
def stream(data,extra=''):
    return obj(('<< /Length %d %s >>\nstream\n'%(len(data),extra)).encode()+data+b'\nendstream')
font=obj(b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>')
def txt(x,y,size,s):
    s=s.encode('ascii','replace').decode().replace('\\','\\\\').replace('(','\\(').replace(')','\\)')
    return f'BT /F1 {size} Tf {x} {y} Td ({s}) Tj ET\n'
pages=[]
for start in range(0,len(items),4):
    content='0.94 0.94 0.91 rg 0 0 1000 850 re f\n0.08 0.09 0.12 rg\n'
    content+=txt(24,819,18,'Episode 1 - new 1990s anime cast')
    content+=txt(24,800,10,'Source drawings / exploratory - poses, rigs and scene contacts remain separate work')
    resources=[]
    for j,it in enumerate(items[start:start+4]):
        im=Image.open(ROOT/it['path']).convert('RGBA');w,h=im.size
        alpha=stream(zlib.compress(im.getchannel('A').tobytes()),f'/Type /XObject /Subtype /Image /Width {w} /Height {h} /ColorSpace /DeviceGray /BitsPerComponent 8 /Filter /FlateDecode')
        rgb=stream(zlib.compress(im.convert('RGB').tobytes()),f'/Type /XObject /Subtype /Image /Width {w} /Height {h} /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /FlateDecode /SMask {alpha} 0 R')
        col=j%2;row=j//2;x=24+col*490;y=425-row*382
        scale=min(465/w,333/h);dw=w*scale;dh=h*scale
        content+=f'q {dw:.3f} 0 0 {dh:.3f} {x+(465-dw)/2:.3f} {y+35+(333-dh)/2:.3f} cm /I{j} Do Q\n'
        content+=txt(x,y+20,12,it['label'])+txt(x,y+5,9,it['task'])
        resources.append(f'/I{j} {rgb} 0 R')
    content+=txt(930,15,9,str(start//4+1))
    c=stream(content.encode())
    pages.append(obj(f'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 1000 850] /Resources << /Font << /F1 {font} 0 R >> /XObject << {" ".join(resources)} >> >> /Contents {c} 0 R >>'.encode()))
objects[0]=b'<< /Type /Catalog /Pages 2 0 R >>'
objects[1]=f'<< /Type /Pages /Count {len(pages)} /Kids [{" ".join(str(p)+" 0 R" for p in pages)}] >>'.encode()
out=bytearray(b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n');offsets=[0]
for i,b in enumerate(objects,1):
    offsets.append(len(out));out+=f'{i} 0 obj\n'.encode()+b+b'\nendobj\n'
pos=len(out);out+=f'xref\n0 {len(objects)+1}\n0000000000 65535 f \n'.encode()
for n in offsets[1:]:out+=f'{n:010d} 00000 n \n'.encode()
out+=f'trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{pos}\n%%EOF\n'.encode()
(RUN/'episode1-new-anime-cast.pdf').write_bytes(out)
print(json.dumps({'sources_including_Amaia':len(items),'pages':len(pages),'pdf_bytes':len(out)}))
