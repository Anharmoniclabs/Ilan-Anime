from pathlib import Path
from studio.craft import Session
from PIL import Image
import hashlib,json,numpy as np
R=Path('/home/alabs/Projects/Ilan-Anime');O=R/'production/character-completion-episode1/reviews';B=R/'production/runs/cemi-90s-production/tasks';A=B/'amaia-complete';V=B/'river-character-library'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
checks={'river':[],'amaia_hashes':[],'amaia_native':[]}
with Session('photocraft',R,O/'photo-native-evidence') as s:
 for c in json.load(open(V/'library-manifest.json'))['characters']:
  p=V/'native-alpha-preserved-v2'/f"{c['id']}.pcraft";before=sha(p)
  op=s.call('doc_open',{'path':str(p)});st=s.call('doc_inspect',{})
  dest=O/f"river-{c['id']}.png";s.call('doc_export',{'path':str(dest)})
  source=np.array(Image.open(R/c['source']).convert('RGBA')).astype('int32');export=np.array(Image.open(dest).convert('RGBA')).astype('int32')
  checks['river'].append({'id':c['id'],'native_sha256':before,'unchanged_after_reopen':sha(p)==before,'source_hash_matches':sha(R/c['source'])==c['source_sha256'],'alpha_equal':bool(np.array_equal(source[:,:,3],export[:,:,3])),'premultiplied_rgb_equal':bool(np.array_equal(source[:,:,:3]*source[:,:,3:],export[:,:,:3]*export[:,:,3:])),'layers':st['layers'],'size':[st['width'],st['height']]})
  s.call('command_run',{'id':'file.close','params':{}})
 for name in ['amaia-joint-library.pcraft','amaia-layered.pcraft']:
  p=A/name;before=sha(p);opened=s.call('doc_open',{'path':str(p)});st=s.call('doc_inspect',{});checks['amaia_native'].append({'path':name,'sha256':before,'opened':opened,'layers':st['layers'],'unchanged':sha(p)==before});s.call('command_run',{'id':'file.close','params':{}})
with Session('effectcraft',R,O/'effect-native-evidence') as s:
 for name in ['amaia-asset-library.ecproj','amaia-controls-16x9.ecproj']:
  p=A/name;before=sha(p);v=s.call('open_project',{'path':str(p)});checks['amaia_native'].append({'path':name,'sha256':before,'opened':v,'unchanged':sha(p)==before})
for p,h in json.load(open(A/'delivery-hashes.json')).items():checks['amaia_hashes'].append({'path':p,'matches':sha(A/p)==h,'sha256':sha(A/p)})
frames=[np.array(Image.open(p)) for p in sorted((A/'widescreen-frames').glob('*.png'))]
checks['amaia_frames']={'count':len(frames),'dimensions':list(frames[0].shape),'unique':len({x.tobytes() for x in frames}),'holds_on_threes':all(np.array_equal(frames[i],frames[i//3*3]) for i in range(len(frames))),'body_below_y200_fixed':all(np.array_equal(x[200:],frames[0][200:]) for x in frames)}
(O/'native-verification.json').write_text(json.dumps(checks,indent=2));print({'river_count':len(checks['river']),'river_all_equal':all(x['alpha_equal'] and x['premultiplied_rgb_equal'] and x['unchanged_after_reopen'] and x['source_hash_matches'] for x in checks['river']),'amaia_hash_matches':all(x['matches'] for x in checks['amaia_hashes']),'frames':checks['amaia_frames']})
