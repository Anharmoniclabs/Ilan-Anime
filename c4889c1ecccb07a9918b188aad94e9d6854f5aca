"""One authorized FLUX preview through Nessa's HF tool and operation receipts."""
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path.home() / 'Projects/NESSA'))
from agentharness.agent import Agent, AgentConfig
from agentharness.cloud import cloud_clients, load_token
from agentharness.llm import ToolCall
from agentharness.workspace import Workspace

root = Path(__file__).resolve().parents[1]
path = 'art/ch01-jerome-0307-flux-v1.png'
receipt = (root / path).with_suffix('.generation.json')
if receipt.exists():
    record = json.loads(receipt.read_text())
    if record.get('status') != 'generated':
        raise SystemExit('Existing request needs inspection; no automatic retry.')
    print('Already generated:', root / path)
    raise SystemExit(0)

source = json.loads((root / 'art/ch01-jerome-0307-v2.generation.json').read_text())
ws = Workspace.direct(root, Path.home() / '.agentharness/runs' / ('cemi-flux-' + str(time.time_ns())))
agent = Agent(cloud_clients(load_token())[0], ws,
              config=AgentConfig(require_approval=False, permission_mode='bypass'))
agent.task = 'User authorized replacing the desk image with FLUX through Hugging Face. One still only.'
def call(name, **args):
    result = agent._execute(ToolCall(name, name, args), [name], dedupe=False)
    print(result, flush=True)
    if result.startswith(('ERROR:', 'TIMEOUT')):
        raise SystemExit(1)
    return result

call('image_generate', prompt=source['parameters']['prompt'], path=path,
     model='black-forest-labs/FLUX.1-dev', width=1664, height=928, seed=3072026)
if not (root / path).is_file():
    raise SystemExit('No image delivered; inspect operation receipt.')
call('production_update', operation='asset', data={
    'id':'ch01-jerome-0307-flux-v1', 'path':path, 'role':'keyframe',
    'notes':'FLUX.1-dev through Hugging Face. Reuses existing desk-shot prompt; awaiting user review. No animation.'})
print('Evidence:', agent.evidence_dir)
