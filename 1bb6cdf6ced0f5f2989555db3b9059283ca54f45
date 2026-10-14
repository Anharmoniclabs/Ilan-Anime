from pathlib import Path
from PIL import Image
import json,numpy as np
P=Path(__file__).resolve().parent; O=P.parent/'three-losses'
def ar(p):return np.asarray(Image.open(p).convert('RGB')).astype(int)
v=json.loads((P/'verification.json').read_text());t=json.loads((P/'action-timeline.json').read_text())
v.pop('protected_living_and_front_hull_max_delta')
v['protected_living_and_front_hull_against_unmodified_acting_cels']={}
for f in [0,24,42,57,75,90,108]:
 e=next(e for e in t['exposures'] if e['start']<=f<e['end_exclusive']);a=ar(P/'native'/f'{f:06}.png');b=ar(P/e['source'])
 v['protected_living_and_front_hull_against_unmodified_acting_cels'][str(f)]={'living_left_680px':int(np.abs(a[:650,:680]-b[:650,:680]).max()),'front_hull_below_680px':int(np.abs(a[680:]-b[680:]).max())}
v['contact_comparison_note']='Prior rejected render contained ghosts in the left rectangle, so protection is compared against the unmodified acting cel, not the rejected ghost composite.'
(P/'verification.json').write_text(json.dumps(v,indent=2))
m=json.loads((O/'motion-review.json').read_text().replace(str(O),str(P)))
# stable reference retained solely for inherited contact checks
import shutil
shutil.copy2(O/'layers/stable-plate.png',P/'layers/stable-plate.png')
(P/'motion.json').write_text(json.dumps(m,indent=2))
base=Image.open(P/'sources/rest.png').convert('RGBA')
for name in ['woman','young-man','elder']:base=Image.alpha_composite(base,Image.open(P/'layers'/f'{name}-occluded-native.png'))
base.save(P/'review/opaque-registration-diagnostic.png')
print(json.dumps(v['protected_living_and_front_hull_against_unmodified_acting_cels'],indent=2))
