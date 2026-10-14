"""Build script-ordered review PDF and verify selected original PNG coverage."""
import hashlib, io, json, re, textwrap, os
from pathlib import Path
from PIL import Image

RUN=Path(__file__).resolve().parent
ROOT=RUN.parents[2]
episode=json.loads((ROOT/'projects/cemi_episode_01/data/episode.json').read_text())
selected={}
limitations={}
for task in ['opening','ballroom-morning','cafe-library','research-ending']:
    manifest=json.loads((RUN/'tasks'/task/'manifest.json').read_text())
    limitations[task]=manifest.get('limitations',[])
    for row in manifest.get('shots',manifest.get('items',[])):
        sid=row.get('shot',row.get('shot_id',row.get('id')))
        assert sid not in selected, sid
        p=Path(row['path'])
        if not p.is_absolute(): p=ROOT/p
        digest=hashlib.sha256(p.read_bytes()).hexdigest()
        assert digest==row['sha256'],sid
        with Image.open(p) as im:
            im.load(); size=im.size
            assert im.convert('RGBA').getchannel('A').getextrema()==(255,255),sid
        selected[sid]={**row,'shot':sid,'path':str(p.relative_to(ROOT)),'dimensions':size,'task':task}
assert set(selected)=={s['id'] for s in episode['shots']}
items=[{**selected[s['id']],'start_frame':s['start_frame'],'frames':s['frames'],'script':s['script']} for s in episode['shots']]
index={'status':'generated shot illustrations; not animated or author approved','shot_count':len(items),'fps':episode['fps'],'body_frames':episode['body_frames'],'limitations':limitations,'shots':items}
(RUN/'shot-index.json').write_text(json.dumps(index,indent=2,ensure_ascii=False))
delivery=RUN/'selected-shots'
delivery.mkdir(exist_ok=True)
for item in items:
    link=delivery/(item['shot']+'.png')
    target=os.path.relpath(ROOT/item['path'],delivery)
    if link.is_symlink():
        if os.readlink(link)==target: continue
        link.unlink()
    assert not link.exists(),str(link)
    link.symlink_to(target)

objects=[b'',b'']
def obj(b):
    objects.append(b);return len(objects)
def stream(data,extra=''):
    return obj(('<< /Length %d %s >>\nstream\n'%(len(data),extra)).encode()+data+b'\nendstream')
font=obj(b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>')
def txt(x,y,size,s):
    s=s.replace('\u2192','>').encode('cp1252','replace').decode('cp1252')
    s=s.replace('\\','\\\\').replace('(','\\(').replace(')','\\)')
    return f'BT /F1 {size} Tf {x} {y} Td ({s}) Tj ET\n'
pages=[]
for start in range(0,len(items),4):
    content='0.95 0.95 0.93 rg 0 0 1000 720 re f\n0.08 0.09 0.12 rg\n'
    content+=txt(24,690,19,'HERALDS OF THE CEMI / EPISODE 1')
    content+=txt(24,672,10,'1990s anime shot illustrations - one selected moment per shot - animation and audio pending')
    resources=[]
    for j,it in enumerate(items[start:start+4]):
        # Document preview only: source PNG remains untouched and hash-verified.
        with Image.open(ROOT/it['path']) as source:
            im=source.convert('RGB');im.thumbnail((1000,565),Image.Resampling.LANCZOS)
            w,h=im.size;buf=io.BytesIO();im.save(buf,format='JPEG',quality=88)
        rgb=stream(buf.getvalue(),f'/Type /XObject /Subtype /Image /Width {w} /Height {h} /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode')
        x=24+(j%2)*490;y=377-(j//2)*322
        scale=min(465/w,263/h);dw=w*scale;dh=h*scale
        content+=f'q {dw:.3f} 0 0 {dh:.3f} {x:.3f} {y:.3f} cm /I{j} Do Q\n'
        content+=txt(x,y-17,12,it['shot']+f"  /  {it['frames']} frames scripted")
        action=re.search(r'\*\*Action:\*\*\s*(.*)',it['script'])
        label=action.group(1) if action else it.get('selected_moment','')
        for k,line in enumerate(textwrap.wrap(label,90)[:2]): content+=txt(x,y-31-k*11,9,line)
        resources.append(f'/I{j} {rgb} 0 R')
    content+=txt(918,12,9,f'{start//4+1} / 32')
    c=stream(content.encode('cp1252'))
    pages.append(obj(f'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 1000 720] /Resources << /Font << /F1 {font} 0 R >> /XObject << {" ".join(resources)} >> >> /Contents {c} 0 R >>'.encode()))
objects[0]=b'<< /Type /Catalog /Pages 2 0 R >>'
objects[1]=f'<< /Type /Pages /Count {len(pages)} /Kids [{" ".join(str(p)+" 0 R" for p in pages)}] >>'.encode()
out=bytearray(b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n');offsets=[0]
for i,b in enumerate(objects,1):
    offsets.append(len(out));out+=f'{i} 0 obj\n'.encode()+b+b'\nendobj\n'
pos=len(out);out+=f'xref\n0 {len(objects)+1}\n0000000000 65535 f \n'.encode()
for n in offsets[1:]:out+=f'{n:010d} 00000 n \n'.encode()
out+=f'trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{pos}\n%%EOF\n'.encode()
(RUN/'episode1-shot-review.pdf').write_bytes(out)
print(json.dumps({'shots':len(items),'pages':len(pages),'pdf_bytes':len(out)}))
