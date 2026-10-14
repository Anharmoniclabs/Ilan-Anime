"""Incremental local native source packaging. No image alteration or generation.
Run from repository root with PYTHONPATH=. .venv/bin/python path/to/assemble.py.
Each source digest gets its own directory. Complete existing versions are skipped;
partial versions stop the run for inspection. Existing native files never overwritten.
"""
import hashlib,json,shutil,re
from pathlib import Path
import numpy as np
from PIL import Image
from studio.craft import ROOT,Session
OUT=Path(__file__).resolve().parent
SOURCE=OUT.parent/'generated'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2);f.write('\n')
def delta(a,b):
 a=np.array(Image.open(a).convert('RGBA')).astype(float);b=np.array(Image.open(b).convert('RGBA')).astype(float)
 return {'alpha_max_delta':float(np.abs(a[...,3]-b[...,3]).max()),'premultiplied_rgb_max_delta':float(np.abs(a[...,:3]*a[...,3:]/255-b[...,:3]*b[...,3:]/255).max())}
records=[]
versions={}
for candidate in sorted(SOURCE.glob('*.png')):
 match=re.fullmatch(r'(.*?)(?:-v([0-9]+))?',candidate.stem)
 identity=match.group(1);version=int(match.group(2) or 1)
 versions.setdefault(identity,[]).append((version,candidate))
selected=[max(group,key=lambda x:x[0])[1] for group in versions.values()]
superseded=[str(path.relative_to(ROOT)) for group in versions.values() for _,path in group if path not in selected]
for source in sorted(selected):
 digest=sha(source);dest=OUT/(source.stem+'-'+digest[:12]); record=dest/'manifest.json'
 if record.exists():
  records.append(json.loads(record.read_text()));continue
 if dest.exists():raise RuntimeError('Partial output requires inspection: '+str(dest))
 dest.mkdir();snapshot=dest/'source-still.png';shutil.copy2(source,snapshot)
 with Session('photocraft',ROOT,dest/'evidence'/'photocraft') as s:
  s.call('doc_open',{'path':str(snapshot)})
  original=s.call('doc_inspect',{})['activeLayer']
  s.call('command_run',{'id':'layer.setProps','params':{'name':'Preserved generated source — exploratory','locked':False}})
  s.call('command_run',{'id':'layer.duplicate','params':{}})
  editable=s.call('doc_inspect',{})['activeLayer']
  s.call('command_run',{'id':'layer.setProps','params':{'name':'Editable master — not separated rig parts','locked':False}})
  s.call('command_run',{'id':'layer.setProps','params':{'layer':original,'visible':False,'locked':True}})
  s.call('doc_save',{'path':str(dest/'master.pcraft')})
  s.call('doc_export',{'path':str(dest/'master.psd')})
  s.call('doc_export',{'path':str(dest/'preview.png')})
  s.call('command_run',{'id':'file.close','params':{}})
  s.call('doc_open',{'path':str(dest/'master.pcraft')})
  native_state=s.call('doc_inspect',{})
  s.call('command_run',{'id':'file.close','params':{}})
  s.call('doc_open',{'path':str(dest/'master.psd')})
  psd_state=s.call('doc_inspect',{})
  s.call('doc_export',{'path':str(dest/'psd-reopened.png')})
 a=np.array(Image.open(source).convert('RGBA'));alpha=a[...,3]
 entry={'source_name':source.name,'source':str(source.relative_to(ROOT)),'source_sha256':digest,'directory':str(dest.relative_to(ROOT)),'status':'exploratory','kind':'editable-generated-master-library','size':[int(a.shape[1]),int(a.shape[0])],'source_alpha':{'min':int(alpha.min()),'max':int(alpha.max()),'zero_pixels':int((alpha==0).sum()),'partial_pixels':int(((alpha>0)&(alpha<255)).sum()),'opaque_pixels':int((alpha==255).sum())},'native_sha256':sha(dest/'master.pcraft'),'psd_sha256':sha(dest/'master.psd'),'source_snapshot_exact':sha(snapshot)==digest,'native_export_delta':delta(snapshot,dest/'preview.png'),'psd_reopened_delta':delta(snapshot,dest/'psd-reopened.png'),'native_reopened':True,'psd_reopened':True,'native_layers':native_state['layers'],'psd_layers':psd_state['layers'],'separated_parts':False,'rigged':False,'motion_validated':False,'approval':'No technical or author approval inferred','limitations':['One generated source drawing, not a rig or registered pose sequence.','Hair, clothing, accessories and body overlap surfaces remain flattened within the editable layer.','Hidden surfaces, expressions, mouth shapes, alternative views and action drawings require separate artwork.','Source alpha and artwork are preserved; no matte correction is implied.']}
 write(record,entry);records.append(entry);print('assembled',source.name,flush=True)
set_digest=hashlib.sha256(json.dumps([(r['source_name'],r['source_sha256']) for r in records]).encode()).hexdigest()[:12]
manifest=OUT/('assembly-'+set_digest+'.json')
if not manifest.exists():
 lib=OUT/('effectcraft-'+set_digest);lib.mkdir()
 with Session('effectcraft',ROOT,lib/'evidence') as s:
  commands={n:s.call('describe_command',{'command':n}) for n in ['file.import']}
  write(lib/'command-schema.json',commands)
  s.call('open_project',{'new':True})
  s.call('execute_command',{'command':'file.import','params':{'paths':[str(ROOT/r['directory']/'source-still.png') for r in records]}})
  s.call('save_project',{'path':str(lib/'source-library.ecproj')})
  s.call('open_project',{'path':str(lib/'source-library.ecproj')})
  state=s.call('get_project',{})
  write(lib/'reopened-project.json',state)
 write(manifest,{'status':'exploratory','asset_count':len(records),'assets':records,'superseded_sources':superseded,'effectcraft_library':str((lib/'source-library.ecproj').relative_to(ROOT)),'effectcraft_reopened':True,'effectcraft_kind':'Imported image library only; no animation or puppet composition.','mutations':'No source files altered. Existing complete asset versions skipped by digest.'})
print('manifest',manifest,flush=True)
