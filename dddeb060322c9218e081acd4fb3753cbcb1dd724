from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image
R=Path.cwd(); O=Path(__file__).resolve().parent; P=R/'production/runs/episode1-native-inserts/tasks/room-filters-coin-blackout'; D=O/'S05-13'
def dump(p,v): p.write_text(json.dumps(v,indent=2)+'\n')
def ref(p):
 p=Path(p); return {'path':str(p.relative_to(R)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
old=json.loads((P/'S05-13/shot.json').read_text()); new=json.loads((D/'shot.json').read_text())
assert [l['keys'] for l in old['layers']]==[l['keys'] for l in new['layers']]
for a,b in zip(old['layers'],new['layers']):
 assert {k:v for k,v in a.items() if k!='source'}=={k:v for k,v in b.items() if k!='source'}
 if 'coin' not in a['name']: assert Path(a['source']).read_bytes()==Path(b['source']).read_bytes()
assert np.array_equal(np.array(Image.open(D/'coin-shared-engraved.png'))[:,:,3],np.array(Image.open(P/'S05-13/coin-matte-clean.png'))[:,:,3])
frames=[np.array(Image.open(D/f'native-frames/frame-{i:04d}.png').convert('RGB')) for i in range(96)]
assert all(np.array_equal(frames[19],frames[i]) for i in range(19,96))
assert (frames[17]==255).all()
mask=np.ones((720,1280),bool); mask[370:555,480:770]=False
assert all(np.array_equal(frames[0][mask],frames[i][mask]) for i in range(96) if i!=17)
tracking=[]
# Interior engraving template excludes edges, contact shadow and travelling glint.
base=frames[0][420:485,560:695].astype(float)
for i in [1,15,16,18,19,95]:
 candidates=[]
 for dy in range(-14,3):
  for dx in range(-3,4):
   err=np.mean((frames[i][420+dy:485+dy,560+dx:695+dx].astype(float)-base)**2); candidates.append((float(err),dx,dy))
 err,dx,dy=min(candidates); tracking.append({'frame':i,'dx':dx,'dy':dy,'mse':err})
expected={1:(2,0),15:(0,-12),16:(0,-9),18:(0,-1),19:(0,0),95:(0,0)}
assert all((t['dx'],t['dy'])==expected[t['frame']] for t in tracking)
dump(O/'preservation-checks.json',{'all_original_layer_keys_and_exposures_equal':True,'noncoin_layers_byte_identical':True,'coin_alpha_exact_prior_silhouette':True,'background_outside_coin_region_static_except_flash':True,'flash17_all_white':True,'settle19_through95_pixel_identical':True,'native_template_tracking':tracking,'render_reopen':'render-saved/status.json confirms saved native project reopened and all 96 frames rendered'})
shots=[]
for shot,n,clip,native,start in [('S03-03',288,'review.mp4','native',3792),('S04-02',144,'review-matte.mp4','native-matte',6192),('S05-13',96,'review.mp4','native',8712),('S06-03',144,'review.mp4','native',9648)]:
 root=D if shot=='S05-13' else P/shot
 record={'shot':shot,'status':'submitted','author_approved':False,'frames':n,'fps':24,'width':1280,'height':720,'audio':False,'episode_start_frame':start,'episode_end_exclusive':start+n,'clip':ref(root/clip),'native_project':ref(root/native/'shot.ecproj'),'shot_spec':ref(root/'shot.json'),'disposition':'repaired coin derivative' if shot=='S05-13' else 'reuse existing preserved output; no creative change','source_layers':[ref(l['source']) for l in json.loads((root/'shot.json').read_text())['layers'] if 'source' in l]}
 (O/shot).mkdir(exist_ok=True); dump(O/shot/'delivery.json',record); shots.append(record)
dump(O/'delivery.json',{'task_id':'native-inserts','status':'submitted','review_scope':'four preserved source clips plus repaired coin; final selection uses repaired coin','shots':shots,'source_clip_checks':'video-checks.json','independent_review_required':True,'author_playback_approval':'separate downstream gate'})
dump(O/'shot-native-index.json',{'shots':shots,'reproduction':{'build':'build.py','native_recipe':'S05-13/native-recipe.json','saved_project_render_recipe':'S05-13/render-saved-recipe.json','frames':'S05-13/native-frames','encode':'ffmpeg -framerate 24 -i native-frames/frame-%04d.png -frames:v 96 -c:v libx264 -crf 16 -pix_fmt yuv420p -an review.mp4'}})
# Correct future standalone recipe output paths; preserve original failed receipt.
p=D/'native-recipe.json'; p.write_text(p.read_text().replace('${OUT}/frames/frame-','${OUT}/frame-'))
p=O/'build.py'; p.write_text(p.read_text().replace('${OUT}/frames/frame-','${OUT}/frame-'))
inputs=[R/'production/runs/episode1-full-picture/coin-assets/coin-unengraved-rgba.png',R/'production/runs/episode1-picture-motion/tasks/editorial-motion-r1/shared-sigil.json',R/'production/runs/episode1-picture-motion/tasks/editorial-motion-r1/shared-sigil.svg',P/'S05-13/native-matte/shot.ecproj',P/'S05-13/shot.json']
dump(O/'hashes.json',{'inputs':[ref(p) for p in inputs],'deliverables':[ref(p) for p in O.rglob('*') if p.is_file() and not any(x in p.parts for x in ['.codex','evidence']) and p.name not in ['hashes.json','result.json']]})
