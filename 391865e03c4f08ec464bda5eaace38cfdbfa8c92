from pathlib import Path
from PIL import Image
import numpy as np,json,hashlib
p=Path(__file__).resolve().parent
def ar(f):return np.asarray(Image.open(f).convert('RGB')).astype(int)
def sj(n,v):(p/n).write_text(json.dumps(v,indent=2)+'\n')
reopen={str(f):int(np.abs(ar(p/'native-review'/f'{f:06}.png')-ar(p/'reopen-review'/f'reopened-{f}.png')).max()) for f in [0,108,191]}
unchanged=[f for f in range(192) if np.array_equal(ar(p/'native-review'/f'{f:06}.png'),ar(p/'native-final'/f'{f:06}.png'))]
timeline=json.load(open(p/'action-timeline.json'))
for e in timeline['exposures']:
 if e['drawing']=='head-down':e['source']='cels/head-down-refined.png'
sj('action-timeline-review.json',timeline)
motion=json.load(open(p/'motion.json'))
for pose in motion['elements'][1]['poses']:
 pose['drawing']=pose['drawing'].replace('/head-down.png','/head-down-refined.png')
sj('motion-review.json',motion)
base=ar(p/'sources/rest.png');a=ar(p/'cels/head-down-refined-native.png')
metrics={k:int(np.abs(a[y:Y,x:X]-base[y:Y,x:X]).max()) for k,(x,y,X,Y) in {'body':(280,520,820,730),'child':(520,360,755,620),'hull':(900,700,1600,930),'shoulder':(278,395,355,490)}.items()}
# Loss-specific isolated head areas; camera held until after all fades.
roi=[(643,258,723,337),(815,270,914,367),(1044,310,1144,393)]
fades=[]
for region,beat in zip(roi,timeline['apparitions']):
 x,y,X,Y=region;arr=[];ref=ar(p/'native-review/000108.png')[y:Y,x:X]
 for f in [beat['start'],(beat['start']+beat['end'])//2,beat['end']]:
  arr.append({'frame':f,'mean_abs_delta_from_empty':float(np.abs(ar(p/'native-review'/f'{f:06}.png')[y:Y,x:X]-ref).mean())})
 fades.append(arr)
source_integrity=[{'path':r['path'],'unchanged':hashlib.sha256(Path(r['path']).read_bytes()).hexdigest()==r['sha256']} for r in json.load(open(p/'source-hashes.json'))]
result={'reopened_pixel_max':reopen,'frames_identical_to_preceding_inspected_take':unchanged,'changed_frames':[f for f in range(192) if f not in unchanged],'refined_head_contact_pixel_max':metrics,'fades_roi':fades,'source_integrity':source_integrity,'cadence_all_exposures_on_threes':all(e['start']%3==0 and (e['end_exclusive']-e['start'])%3==0 for e in timeline['exposures'])}
sj('verification.json',result)
assert all(v==0 for v in reopen.values())
assert all(v==0 for v in metrics.values())
assert all(r['unchanged'] for r in source_integrity)
assert len(unchanged)==180
print(json.dumps({k:v for k,v in result.items() if k!='frames_identical_to_preceding_inspected_take'},indent=2))
