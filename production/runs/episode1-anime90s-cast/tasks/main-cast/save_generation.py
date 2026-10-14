from pathlib import Path
import json, hashlib, shutil, sys
from PIL import Image
out=Path(__file__).resolve().parent
request=json.loads((out/(sys.argv[1]+'.request.json')).read_text())
target=out/(request['name']+'.png')
if target.exists() and target.read_bytes()!=Path(request['generated_path']).read_bytes(): raise SystemExit('Refusing overwrite')
source=Path(request['generated_path'])
shutil.copy2(source,target)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
im=Image.open(target)
record={**request,'file':str(target),'sha256':sha(target),'size':list(im.size),'mode':im.mode,'alpha_extrema':list(im.getchannel('A').getextrema()) if im.mode=='RGBA' else None,'references':{p:sha(Path(p)) for p in request['references']},'status':'exploratory','tool':'built-in image_gen','author_approved':False,'rigged':False}
(out/(request['name']+'.json')).write_text(json.dumps(record,indent=2))
print(json.dumps({'file':str(target),'size':record['size'],'alpha':record['alpha_extrema']}))
