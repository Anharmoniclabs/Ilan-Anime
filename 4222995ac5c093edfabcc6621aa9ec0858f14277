#!/usr/bin/env python3
"""Bounded offline wiring. No generation, approval writing, or implicit latest-file selection."""
import argparse, collections, hashlib, html, json, os, subprocess, sys
from pathlib import Path
from fractions import Fraction
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[4]
sys.path.insert(0,str(ROOT))
EP='projects/cemi_episode_01/data/episode.json'
BASE='production/runs/episode1-picture-motion'
CON=BASE+'/tasks/motion-contracts/contracts.json'
ART='production/runs/episode1-anime90s-scenes/shot-index.json'
DECISIONS='production/runs/episode1-full-picture/author-decisions.json'
TICK=254016000000//24

def read(p): return json.loads((ROOT/p).read_text())
def save(p,d):
 p=Path(p); p.resolve().relative_to(OUT); p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
def digest(p):
 h=hashlib.sha256()
 with open(ROOT/p,'rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def probe(p):
 d=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_frames','-show_streams','-of','json',str(ROOT/p)]))
 vs=[s for s in d['streams'] if s['codec_type']=='video']
 assert len(vs)==1 and not any(s['codec_type']=='audio' for s in d['streams']), 'Requires one video, no audio'
 s=vs[0];assert Fraction(s['r_frame_rate'])==Fraction(s['avg_frame_rate'])==24,'Rate must be 24 CFR'
 assert s['width']*9==s['height']*16,'Requires exact 16:9'
 assert s.get('sample_aspect_ratio','1:1') in ['1:1','N/A'],'Non-square pixels'
 n=int(s['nb_read_frames'])
 timestamps=[Fraction(f['best_effort_timestamp_time']) for f in d['frames'] if f['media_type']=='video']
 assert len(timestamps)==n and all(abs((t-timestamps[0])-Fraction(i,24))<Fraction(1,100000) for i,t in enumerate(timestamps)), 'Non-CFR frame timestamps'
 assert abs(float(s['duration'])-n/24)<.0001,'Duration mismatch'
 return {'frames':n,'width':s['width'],'height':s['height'],'fps':24,'audio_streams':0,'sha256':digest(p),'color_space':s.get('color_space','unspecified')}
def seed():
 d={}
 for sh in ['S00-01','S00-02','S01-15','S02-01','S15-09']:
  d[sh]={'path':BASE+'/tasks/editorial-motion-r1/'+sh+'/preview.mp4','native':BASE+'/tasks/editorial-motion-r1/'+sh+'/shot.ecproj','status':'unreviewed','task_result':BASE+'/tasks/editorial-motion-r1/result.json'}
 d['S01-01']={'path':BASE+'/tasks/water-motion-r1/S01-01-silent-preview.mp4','native':BASE+'/tasks/water-motion-r1/S01-01-water-motion.filmcraft','status':'unreviewed','task_result':BASE+'/tasks/water-motion-r1/result.json'}
 d['S01-03']={'path':'production/runs/episode1-picture-motion-continuation/tasks/amaia-registration/S01-03-partial-silent-v2.mp4','native':'production/runs/episode1-picture-motion-continuation/tasks/amaia-registration/edit-v2.filmcraft','status':'partial','task_result':'production/runs/episode1-picture-motion-continuation/tasks/amaia-registration/result.json'}
 d['S14-03']={'path':BASE+'/tasks/research-graph/native-v1/preview.mp4','native':BASE+'/tasks/research-graph/native-v1/edit.filmcraft','status':'rejected','task_result':BASE+'/tasks/research-graph/result.json','review':BASE+'/reviews/research-graph/review.json'}
 for sh,x in d.items():
  review=BASE+'/reviews/editorial-motion-r1/review.json'
  if 'editorial-motion-r1/' in x['path'] and (ROOT/review).is_file():
   x['review']=review
   x['status']='technical-approved' if read(review)['decision']=='approve' else 'rejected'
  x['sha256']=digest(x['path'])
 save(OUT/'links.json',d)
def validate_slots(rows):
 assert len(rows)==128 and len({r['shot'] for r in rows})==128
 cur=0
 for r in rows:
  assert r['start_frame']==cur and r['frames']>0
  cur+=r['frames']; assert r['end_frame_exclusive']==cur
 assert cur==27120

def refresh():
 from PIL import Image
 ep=read(EP); contracts={x['shot']:x for x in read(CON)['shots']}; arts={x['shot']:x for x in read(ART)['shots']};links=read(str((OUT/'links.json').relative_to(ROOT)))
 assert set(links)<=set(contracts)
 rows=[]
 for s in ep['shots']:
  sh=s['id']; c=dict(contracts[sh]);a=arts[sh];assert digest(a['path'])==a['sha256']
  if (ROOT/DECISIONS).exists() and sh in read(DECISIONS):
   c['current_author_decision']=read(DECISIONS)[sh]
   for line in s['script'].splitlines():
    if line.startswith('- **Action:** '):c['script_action']=line.removeprefix('- **Action:** ')
  assert (c['start_frame'],c['frames'])==(s['start_frame'],s['frames'])
  assert (a['start_frame'],a['frames'])==(s['start_frame'],s['frames'])
  l=links.get(sh); status=l['status'] if l else 'missing'
  assert status in ['missing','partial','rejected','unreviewed','technical-approved','complete']
  if l and l.get('review'):
   decision=read(l['review']).get('decision')
   if decision=='reject':status='rejected'
   elif decision=='approve' and status=='unreviewed':status='technical-approved'
  missing=c['coverage_gap']['missing_work']
  r={'shot':sh,'start_frame':s['start_frame'],'end_frame_exclusive':s['end_frame'],'frames':s['frames'],'status':status,'final_eligible':False,'artwork':a,'action_contract':c,'contract_reference':CON+'#/shots/'+str(list(contracts).index(sh)),'draft':l,'missing_or_unvalidated_actions':missing,'missing_drawings':c['departments']['character']['required_registered_drawings'],'required_props':c['departments']['props']['requirements'],'required_environment':c['departments']['environment_fx']['requirements'],'legacy_animation_status':s['animation_status']}
  if l:
   r['provenance_hashes']={p:digest(p) for p in [l['native'],l.get('task_result'),l.get('review')] if p}
   assert digest(l['path'])==l['sha256'],'Clip hash changed; explicit relink required'
   r['probe']=probe(l['path']);assert r['probe']['frames']==s['frames'],'Clip must fill exact slot; never pad or loop'
   assert (ROOT/l['native']).is_file()
   if l.get('task_result'):
    tr=read(l['task_result']);r['source_task_status']=tr['status'];r['source_limitations']=tr.get('blockers',[])
   if l.get('review'):r['independent_review']=read(l['review'])
  r['placement']={'kind':'clip' if l and status!='rejected' else 'gap','start_frame':s['start_frame'],'end_frame_exclusive':s['end_frame'],'source_in_frame':0 if l and status!='rejected' else None}
  thumb=OUT/'thumbs'/f'{sh}.jpg';thumb.parent.mkdir(exist_ok=True)
  with Image.open(ROOT/a['path']) as im:im.thumbnail((256,144));im.convert('RGB').save(thumb,quality=80)
  rows.append(r)
 validate_slots(rows)
 timeline={'schema':'cemi.episode-wiring.v1','status':'inspection-only; incomplete animation','fps':24,'width':1280,'height':720,'frames':27120,'frame_convention':'zero-based half-open','sound':'excluded','source_hashes':{p:digest(p) for p in [EP,CON,ART,BASE+'/author-direction.json','production/art_direction.json']},'shots':rows}
 if (ROOT/DECISIONS).exists():timeline['source_hashes'][DECISIONS]=digest(DECISIONS)
 save(OUT/'timeline.json',timeline)
 index(rows)
 save(OUT/'validation.json',{'slots':128,'contiguous':True,'total_frames':27120,'artwork_hashes_verified':128,'status_counts':dict(collections.Counter(r['status'] for r in rows)),'draft_clips_verified':sum(bool(r['draft']) for r in rows),'timeline_sha256':digest(OUT/'timeline.json')})
 return timeline

def index(rows):
 def url(p):return html.escape(os.path.relpath(ROOT/p,OUT),quote=True)
 parts=['<!doctype html><meta charset="utf-8"><title>Episode 1 — inspection wiring</title><style>body{font:16px sans-serif;background:#17212b;color:#eee;margin:2em}a{color:#9cd5ff}article{border-top:1px solid #789;padding:1em}img{float:left;margin:0 1em 1em 0}article:after{content:"";display:block;clear:both}summary{cursor:pointer}</style><h1>Episode 1 — incomplete silent inspection timeline</h1><p>128 slots · 27,120 frames · 24 fps · 16:9. Stills below are artwork thumbnails, not motion evidence. Empty native gaps are intentional. No completed episode export.</p><p><a href="episode.filmcraft">Native edit</a> · <a href="timeline.json">Machine timeline</a> · <a href="README.md">Commands and limits</a></p>']
 for r in rows:
  sh=r['shot'];parts.append(f'<article id="{sh}"><img src="thumbs/{sh}.jpg" alt="{sh} source still"><h2>{sh}: {r["status"]}</h2><p>Frames [{r["start_frame"]}, {r["end_frame_exclusive"]})</p><a href="{url(r["artwork"]["path"])}">New artwork</a>')
  if r['draft']:
   d=r['draft'];parts.append(f' · <a href="{url(d["path"])}">Inspection clip ({r["status"]})</a> · <a href="{url(d["native"])}">Shot native project</a>')
  if r['draft']:
   for label,key in [('Source result','task_result'),('Independent review','review')]:
    if r['draft'].get(key):parts.append(f' · <a href="{url(r["draft"][key])}">{label}</a>')
  parts.append('<details><summary>Action contract, missing drawings and source limits</summary><pre style="white-space:pre-wrap">'+html.escape(json.dumps({k:r[k] for k in ['missing_or_unvalidated_actions','missing_drawings','required_props','required_environment','action_contract']},indent=2,ensure_ascii=False))+'</pre></details>'+html.escape('; '.join(r.get('source_limitations',[])))+'</article>')
 (OUT/'index.html').write_text('\n'.join(parts))

def native(t):
 from studio.craft import Session
 ev=OUT/('native-receipts-'+str(len(list(OUT.glob('native-receipts*')))+1));ev.mkdir(exist_ok=False)
 recipe=[]
 with Session('filmcraft',ROOT,ev) as fc:
  def call(tool,args):recipe.append({'app':'filmcraft','tool':tool,'arguments':args});return fc.call(tool,args)
  call('command_run',{'id':'file.newSequence','params':{'name':'Episode 1 INCOMPLETE inspection — gaps are missing motion','width':1280,'height':720,'fps':24,'video':1,'audio':0}})
  for r in t['shots']:
   call('command_run',{'id':'markers.addRange','params':{'time':r['start_frame']*TICK,'durationFrames':r['frames'],'name':r['shot']+' '+r['status'],'comment':'; '.join(r['missing_or_unvalidated_actions'])}})
   d=r['draft']
   if d and r['status']!='rejected':
    item=call('media_import',{'text':str(ROOT/d['path'])})['items'][0]
    placed=call('command_run',{'id':'timeline.place','params':{'item':item,'track':'V1','frame':r['start_frame'],'insert':False,'sourceIn':0,'duration':r['frames']*TICK}})
    clip=call('sequence_inspect',{})['video'][0]['items'][-1]['clip']
    call('command_run',{'id':'timeline.select','params':{'clips':[clip],'add':False,'toggle':False}})
    call('command_run',{'id':'clip.scaleToFrameSize','params':{}})
    call('command_run',{'id':'clip.rename','params':{'clip':clip,'name':r['shot']+' '+r['status']}})
  call('command_run',{'id':'file.saveAs','params':{'path':str(OUT/'episode.filmcraft')}})
  save(OUT/'native-inspect.json',call('sequence_inspect',{}))
  call('command_run',{'id':'file.open','params':{'path':str(OUT/'episode.filmcraft')}})
  reopened=call('sequence_inspect',{});save(OUT/'native-reopened.json',reopened)
  assert reopened['durationFrames']==27120
  clips=reopened['video'][0]['items']
  expected=[r for r in t['shots'] if r['draft'] and r['status']!='rejected']
  assert len(clips)==len(expected) and len(reopened['markers'])==128
  for clip,r in zip(clips,expected):
   assert (clip['startFrame'],clip['durationFrames'],clip['sourceIn'],clip['speed'])==(r['start_frame'],r['frames'],0,1.0)
  for marker,r in zip(reopened['markers'],t['shots']):
   assert (marker['start'],marker['duration'])==(r['start_frame']*TICK,r['frames']*TICK)
  assert reopened['settings']['frame_rate']=={'num':24,'den':1}
  save(OUT/'native-validation.json',{'reopened':True,'markers':128,'exact_placed_clips':len(clips),'empty_slots':128-len(clips),'frames':27120,'fps':24,'native_sha256':digest(OUT/'episode.filmcraft')})
 save(OUT/'native-recipe.json',{'steps':recipe})

def guard(t):
 errors=[]
 validate_slots(t['shots'])
 for r in t['shots']:
  d=r['draft'];sh=r['shot']
  if not d or r['status']!='complete':errors.append(sh+': '+r['status']);continue
  try:
   assert probe(d['path'])['frames']==r['frames']
   assert digest(d['path'])==d['sha256']
   assert not d.get('review') or read(d['review']).get('decision')!='reject'
   # Attestations must be supplied by coordinator; never written by this worker.
   from production.asset_registry import AssetRegistry
   registry=AssetRegistry(ROOT).verify()
   ref=(d['asset_id'],d['version'])
   registered=registry['assets'][ref]
   assert registry['states'][ref]=='canonical'
   assert registered['path']==d['path'] and registered['sha256']==d['sha256'] and sh in registered['shots']
   assert any(v['asset_id']==ref[0] and v['version']==ref[1] and sh in v['shots'] for v in registry['final_uses'].values())
   assert digest(d['release_attestation'])==d['release_attestation_sha256']
   a=read(d['release_attestation'])
   assert a['shot']==sh and a['sha256']==d['sha256'] and a['full_action_coverage'] is True
   assert a['technical']['sha256']==d['sha256'] and a['author']['sha256']==d['sha256']
   assert a['technical']['decision']=='approve' and a['technical']['reviewer_id']!=a['creator_id']
   assert a['author']['decision']=='approve' and a['author']['id']=='luis-m-minier'
   assert a['status']=='canonical'
  except (AssertionError,KeyError,FileNotFoundError,ValueError) as e:errors.append(sh+': release evidence/technical check failed '+str(e))
 return errors

def assemble(t):
 errors=guard(t);save(OUT/'assembly-check.json',{'allowed':not errors,'errors':errors})
 if errors:print('REFUSED: '+str(len(errors))+' unavailable or non-final shots');return 2
 dest=OUT/'assembly';dest.mkdir(exist_ok=False)
 for r in t['shots']:
  subprocess.run(['ffmpeg','-v','error','-i',str(ROOT/r['draft']['path']),'-an','-vf','scale=1280:720,setsar=1','-c:v','libx264','-pix_fmt','yuv420p','-colorspace','bt709','-color_primaries','bt709','-color_trc','bt709',str(dest/(r['shot']+'.mp4'))],check=True)
 (dest/'concat.txt').write_text(''.join("file '"+r['shot']+".mp4'\n" for r in t['shots']))
 subprocess.run(['ffmpeg','-v','error','-f','concat','-safe','0','-i',str(dest/'concat.txt'),'-c','copy','-an',str(dest/'episode-silent.mp4')],check=True)
 p=probe(dest/'episode-silent.mp4');assert p['frames']==27120;save(dest/'verification.json',p)
 return 0

def main():
 ap=argparse.ArgumentParser();ap.add_argument('command',choices=['seed','refresh','native','assemble','relink']);ap.add_argument('--shot');ap.add_argument('--record',help='Repository-relative JSON link record with pinned sha256');a=ap.parse_args()
 if a.command=='seed':seed();return 0
 if a.command=='relink':
  links=read(OUT/'links.json');record=read(a.record);assert a.shot in {s['id'] for s in read(EP)['shots']};assert digest(record['path'])==record['sha256'];p=probe(record['path']);assert p['frames']==next(s['frames'] for s in read(EP)['shots'] if s['id']==a.shot);links[a.shot]=record;save(OUT/'links.json',links)
 t=refresh()
 if a.command in ['native','relink']:native(t)
 if a.command=='assemble':return assemble(t)
 return 0
if __name__=='__main__':sys.exit(main())
