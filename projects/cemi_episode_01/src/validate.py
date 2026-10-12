"""Validate the episode schedule and production state; --final is a release gate."""
from pathlib import Path
import argparse,json,wave,hashlib
ROOT=Path(__file__).resolve().parents[1]
def check(final=False):
    episode=json.loads((ROOT/'data/episode.json').read_text());shots=episode['shots'];cursor=0;errors=[]
    for s in shots:
        if s['start_frame']!=cursor:errors.append(f"{s['id']}: timeline gap")
        cursor=s['end_frame']
        if s['frames']!=s['end_frame']-s['start_frame']:errors.append(f"{s['id']}: frame count")
        for p in s['keyframes']:
            if not (ROOT/p).is_file():errors.append(f'{p}: missing file')
        if final and s['animation_status']!='approved':errors.append(f"{s['id']}: animation not approved")
        if final and s['voice_status'] not in ['approved','no_dialogue']:errors.append(f"{s['id']}: audio not approved")
    if cursor!=27120:errors.append('Body must be 27120 frames')
    with wave.open(str(ROOT/'assets/audio/loop_8s_48000.wav')) as w:
        if (w.getnframes(),w.getframerate(),w.getnchannels())!=(384000,48000,1):errors.append('Loop has wrong length/rate/channels')
    report={'body_frames':cursor,'body_duration_seconds':cursor/24,'shots':len(shots),'shots_with_keyframes':sum(bool(s['keyframes']) for s in shots),'shots_missing_keyframes':[s['id'] for s in shots if not s['keyframes']],'approved_animated_shots':sum(s['animation_status']=='approved' for s in shots),'final_episode_ready':False,'validation_mode':'final' if final else 'project','errors':errors}
    (ROOT/'qa'/('final_gate.json' if final else 'project_validation.json')).write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2));return bool(errors)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--final',action='store_true');a=p.parse_args();raise SystemExit(check(a.final))
