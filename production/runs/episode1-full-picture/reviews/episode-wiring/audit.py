import os,sys,json,hashlib,importlib.util,shutil,subprocess
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import unquote
R=Path.cwd(); O=R/'production/runs/episode1-full-picture/reviews/episode-wiring'; S=R/'production/runs/episode1-full-picture/tasks/episode-wiring'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
before={str(p):sha(p) for p in S.rglob('*') if p.is_file()}
spec=importlib.util.spec_from_file_location('wire',S/'wire.py');w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w);w.OUT=O/'sandbox';w.OUT.mkdir(exist_ok=True);shutil.copyfile(S/'links.json',w.OUT/'links.json')
t=read(S/'timeline.json'); ep=read(R/w.EP); contracts=read(R/w.CON); arts=read(R/w.ART)
assert [(r['shot'],r['start_frame'],r['frames'],r['end_frame_exclusive']) for r in t['shots']]==[(s['id'],s['start_frame'],s['frames'],s['end_frame']) for s in ep['shots']]
w.validate_slots(t['shots'])
for p,h in t['source_hashes'].items():assert sha(R/p)==h,p
for r in t['shots']:
 assert sha(R/r['artwork']['path'])==r['artwork']['sha256']
 if r['draft']:
  assert w.probe(r['draft']['path'])==r['probe']
  subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(R/r['draft']['path']),'-f','null','-'],check=True)
class Links(HTMLParser):
 def handle_starttag(self,tag,attrs):
  for k,v in attrs:
   if k in ('href','src'):assert (S/unquote(v.split('#')[0])).is_file(),v
Links().feed((S/'index.html').read_text())
n=read(S/'episode.filmcraft');items=n['project']['items'];seq=next(i['kind']['Sequence'] for i in items.values() if 'Sequence' in i['kind']);clips=seq['video_tracks'][0]['items'];expected=[r for r in t['shots'] if r['placement']['kind']=='clip']
assert len(clips)==len(expected)==7
for c,r in zip(clips,expected):
 assert (c['start'],c['duration'],c['source_in'],c['speed'])==(r['start_frame']*w.TICK,r['frames']*w.TICK,0,1.0)
 assert str((R/r['draft']['path']).resolve()) in json.dumps(items[str(c['item'])])
assert len(seq['markers'])==128
for m,r in zip(seq['markers'],t['shots']): assert (m['start'],m['duration'])==(r['start_frame']*w.TICK,r['frames']*w.TICK)
a=w.refresh();h=sha(w.OUT/'timeline.json');b=w.refresh();assert h==sha(w.OUT/'timeline.json');assert a==t
assert w.assemble(b)==2 and not (w.OUT/'assembly').exists()
assert before=={str(p):sha(p) for p in S.rglob('*') if p.is_file()}
report={'canonical_slots':128,'total_frames':27120,'native_clips':7,'native_range_markers':128,'empty_slots':121,'artwork_hashes':128,'decoded_clips':8,'source_hashes_current':True,'refresh_matches_submission':True,'refresh_deterministic':True,'assembly_exit':2,'submission_unchanged':True,'offline_links_resolve':True}
(O/'audit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
