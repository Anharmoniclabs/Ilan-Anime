"""Hand off to the Nessa render stage after the active inventory finishes."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

root=Path(__file__).resolve().parents[1]
deadline=time.monotonic()+7200
print('Full-book image generation authorized by user: use available HF credits. Animation disabled.',flush=True)
while time.monotonic()<deadline:
    state=json.loads((root/'production/full-book.json').read_text())
    phase=state.get('phase')
    if phase=='inventory_complete':
        print('Inventory complete. Starting Nessa render workflow; validated existing units will be reused.',flush=True)
        raise SystemExit(subprocess.call([sys.executable,str(root/'scripts/book_director.py'),'--stage','render'],cwd=root,env=os.environ.copy()))
    if phase=='needs_attention':
        raise SystemExit('Inventory needs attention: '+state.get('error',''))
    time.sleep(10)
raise SystemExit('Inventory wait budget exceeded; no image jobs submitted by this handoff.')
