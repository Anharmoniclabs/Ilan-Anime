"""Explicit user-authorized recovery of saved submissions; no generation."""
import json
from pathlib import Path
from studio.runner import CodexRunner

r = CodexRunner('episode1-picture-motion')
if r.ledger.data['paused']:
    r.ledger.resume('APPROVE RESUME episode1-picture-motion')
for task_id in ('water-motion', 'editorial-motion', 'research-graph'):
    task = r.ledger.data['tasks'][task_id]
    if task['state'] != 'submitted':
        continue
    directory = r.run_dir / 'reviews' / task_id
    prior = directory / 'reviewer.events.jsonl'
    if prior.exists() and prior.stat().st_size:
        raise RuntimeError(f'Inspect existing reviewer events before recovery: {prior}')
    r.state['inflight'][task_id] = {'phase': 'submitted', 'recovery': 'User requested run; saved output inspected; previous reviewer never started.'}
    r._save()
    try:
        r.review(task_id, task['result'])
    except Exception as exc:
        r.ledger.pause(f'{task_id}: review recovery failed: {exc}')
        raise
    r.state['inflight'].pop(task_id, None)
    r._save()
    if r.ledger.data['paused']:
        break
print(json.dumps({'paused': r.ledger.data['paused'], 'tasks': {k: v['state'] for k, v in r.ledger.data['tasks'].items()}}))
