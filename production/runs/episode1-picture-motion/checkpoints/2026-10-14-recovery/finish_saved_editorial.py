"""Recover completed editorial output after the sibling worker's pause."""
import json
from pathlib import Path
from studio.runner import CodexRunner

r = CodexRunner('episode1-picture-motion')
assert not r.state['inflight'], 'Inspect active work before recovery'
if r.ledger.data['paused']:
    r.ledger.resume('APPROVE RESUME episode1-picture-motion')
task_id = 'editorial-motion-r1'
task = r.ledger.data['tasks'][task_id]
if task['state'] == 'running':
    result = json.loads((r.root / task['output_dir'] / 'result.json').read_text())
    r.ledger.submit(result)
if r.ledger.data['tasks'][task_id]['state'] == 'submitted':
    r.state['inflight'][task_id] = {'phase': 'submitted', 'recovery': 'User requested finish full episode; saved worker output inspected.'}
    r._save()
    try:
        r.review(task_id, r.ledger.data['tasks'][task_id]['result'])
    except Exception as exc:
        r.ledger.pause(str(exc))
        raise
    finally:
        r.state['inflight'].pop(task_id, None)
        r._save()
if not r.ledger.data['paused']:
    print(r.loop(max_tasks=1))
