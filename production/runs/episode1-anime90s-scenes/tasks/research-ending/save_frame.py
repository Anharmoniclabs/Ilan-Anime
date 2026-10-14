from pathlib import Path
import json,hashlib,shutil,sys
from PIL import Image
p=Path(__file__).resolve().parent;r=json.load(open(p/(sys.argv[1]+'.request.json')));target=p/(r['shot_id']+'.png')
assert not target.exists(),target
shutil.copy2(r['generated_path'],target)
im=Image.open(target);r.update(path=str(target),sha256=hashlib.sha256(target.read_bytes()).hexdigest(),size=list(im.size),status='generated-story-frame',tool='built-in image_gen',animation=False,author_approved=False)
r['reference_hashes']={x:hashlib.sha256(Path(x).read_bytes()).hexdigest() for x in r['references']};(p/(r['shot_id']+'.json')).write_text(json.dumps(r,indent=2));print(r['shot_id'],im.size)
