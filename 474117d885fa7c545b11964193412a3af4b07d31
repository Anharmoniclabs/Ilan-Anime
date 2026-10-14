"""Read-only source checks and task-local guard regressions."""
import copy, json, subprocess, sys
from pathlib import Path
import wire
out=wire.OUT
checks={}
a=wire.refresh();first=wire.digest(out/'timeline.json');b=wire.refresh();assert first==wire.digest(out/'timeline.json');checks['repeat_refresh_identical_timeline_sha256']=first
errors=wire.guard(b);assert len(errors)==128;checks['current_guard_refuses_all_128']=True
for status in ['missing','partial','rejected','unreviewed','technical-approved']:
 t=copy.deepcopy(b);t['shots'][0]['status']=status;assert any(e.startswith('S00-01: '+status) for e in wire.guard(t))
checks['five_nonfinal_states_refused']=True
for bad in ['duplicate','gap','duration']:
 t=copy.deepcopy(b)
 if bad=='duplicate':t['shots'][1]['shot']=t['shots'][0]['shot']
 if bad=='gap':t['shots'][1]['start_frame']+=1
 if bad=='duration':t['shots'][-1]['frames']+=1
 try:wire.validate_slots(t['shots'])
 except AssertionError:pass
 else:raise AssertionError(bad+' accepted')
checks['duplicate_gap_duration_corruption_refused']=True
t=copy.deepcopy(b);t['shots'][0]['status']='complete';assert any(e.startswith('S00-01: release') for e in wire.guard(t));checks['status_flip_without_registry_approval_refused']=True
# Hash changes rejected before refresh can replace pinned data.
original=(out/'links.json').read_text()
try:
 links=json.loads(original);links['S00-01']['sha256']='0'*64;wire.save(out/'links.json',links)
 try:wire.refresh()
 except AssertionError as e:assert 'hash changed' in str(e)
 else:raise AssertionError('hash substitution accepted')
finally:(out/'links.json').write_text(original)
checks['changed_clip_hash_refused']=True
wire.refresh()
proc=subprocess.run([sys.executable,str(out/'wire.py'),'assemble'],capture_output=True,text=True)
assert proc.returncode==2 and not (out/'assembly').exists();checks['assembly_exit_2_before_media_output']=proc.stdout.strip()
# All local HTML links, artwork provenance and clip/native references resolve offline.
from html.parser import HTMLParser
from urllib.parse import unquote
class Links(HTMLParser):
 def handle_starttag(self,tag,attrs):
  for k,v in attrs:
   if k in ['href','src']:
    assert (out/unquote(v.split('#')[0])).is_file(),v
Links().feed((out/'index.html').read_text());checks['offline_links_resolve']=True
# Full decoder errors must fail independently of ffprobe's frame inventory.
for r in b['shots']:
 if r['draft']:
  subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(wire.ROOT/r['draft']['path']),'-f','null','-'],check=True)
checks['eight_clips_full_decode']=True
# Exercise probe's rejection of wrong rate, audio and irregular presentation timestamps.
from unittest.mock import patch
base={'streams':[{'codec_type':'video','r_frame_rate':'24/1','avg_frame_rate':'24/1','width':1280,'height':720,'sample_aspect_ratio':'1:1','nb_read_frames':'2','duration':str(2/24)}], 'frames':[{'media_type':'video','best_effort_timestamp_time':'0'},{'media_type':'video','best_effort_timestamp_time':str(1/24)}]}
for bad in ['audio','rate','timestamps','aspect']:
 data=copy.deepcopy(base)
 if bad=='audio':data['streams'].append({'codec_type':'audio'})
 if bad=='rate':data['streams'][0]['avg_frame_rate']='25/1'
 if bad=='timestamps':data['frames'][1]['best_effort_timestamp_time']='0.06'
 if bad=='aspect':data['streams'][0]['height']=721
 with patch.object(wire.subprocess,'check_output',return_value=json.dumps(data).encode()):
  try:wire.probe(b['shots'][0]['draft']['path'])
  except AssertionError:pass
  else:raise AssertionError('probe accepted '+bad)
checks['audio_rate_timestamp_aspect_corruptions_refused']=True
wire.save(out/'checks.json',checks)
print(json.dumps(checks,indent=2))
