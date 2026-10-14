"""Export only a ready, reviewed dataset. No cloud provisioning or training."""
import hashlib
import json
from pathlib import Path
import shutil
from agentharness.studio_dataset import audit

root=Path(__file__).resolve().parents[1]
result=audit(root)
print(json.dumps(result,indent=2))
if result['status']!='ready_for_training_setup':raise SystemExit(2)
out=root/'dataset/export'
if out.exists():raise SystemExit('Export exists; preserve it and choose a new version.')
items=json.loads((root/'dataset/manifest.json').read_text())['items']
for i,row in enumerate(items):
    target=out/row['split'];target.mkdir(parents=True,exist_ok=True)
    source=(root/row['image']).resolve()
    image=target/(f'{i:04d}'+source.suffix.lower())
    shutil.copy2(source,image)
    if hashlib.sha256(image.read_bytes()).hexdigest()!=row['sha256']:
        raise SystemExit('Source changed during export; discard this incomplete export after inspection.')
    shutil.copy2(root/row['caption'],target/f'{i:04d}.txt')
(out/'manifest.json').write_text(json.dumps(dict(items=items,audit=result),indent=2))
print('Exported train and validation separately. GPU training still requires a configured environment.')
