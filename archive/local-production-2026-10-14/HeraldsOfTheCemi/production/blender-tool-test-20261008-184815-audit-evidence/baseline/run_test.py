import hashlib, json, shutil, sys, time
from pathlib import Path
sys.path.insert(0, '/home/alabs/Projects/NESSA')
from agentharness.agent import Agent, AgentConfig
from agentharness.workspace import Workspace
from agentharness.llm import ToolCall

root=Path(__file__).parent
source=Path('/home/alabs/Downloads/10.png')
(root/'sources').mkdir(exist_ok=True)
shutil.copy2(source,root/'sources/10.png')
assert hashlib.sha256(source.read_bytes()).digest()==hashlib.sha256((root/'sources/10.png').read_bytes()).digest()
class NoModel:
 model='deterministic-tool-test'
 def chat(self,*args,**kwargs): raise RuntimeError('This test does not invoke a model')
agent=Agent(NoModel(),Workspace.direct(root,root.with_name(root.name+'-evidence')),config=AgentConfig(
 require_approval=False,permission_mode='bypass',continuous_verify=(),full_verify_every_edits=0))
args=dict(image='sources/10.png',output_dir='models/character-v1',resolution=128)
start=time.monotonic(); count=0

def execute(name,args):
 global count
 count+=1
 result=agent._execute(ToolCall(str(count),name,args),[name],dedupe=False)
 print(name+': '+result[:1800],flush=True)
 if result.startswith(('ERROR:', 'TIMEOUT')): raise RuntimeError(result)
 # Controller can append a continuous-verification observation.
 return json.JSONDecoder().raw_decode(result)[0]

try:
 result=execute('image_to_blender',args)
 while result['phase']!='complete':
  if time.monotonic()-start>2100: raise TimeoutError('Test deadline; child receipts retained')
  job=execute('mesh_status',dict(job=result['job']))
  if job['status']=='generated': result=execute('image_to_blender',args)
  elif job['status'] in ('failed','timeout'): raise RuntimeError('Worker failed: '+str(job))
  else: time.sleep(10)
 execute('image_to_blender',args) # Idempotent completion and artifact-integrity check.
 report=dict(status='passed',seconds=time.monotonic()-start,source=str(source),
  source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),resolution=128,
  workflow=result,model_directed=False,visual_review='pending')
except Exception as exc:
 report=dict(status='failed',seconds=time.monotonic()-start,error=str(exc),visual_review='pending')
(root/'test-result.json').write_text(json.dumps(report,indent=2))
print('TEST_RESULT '+json.dumps(report),flush=True)
agent.dev.stop_all()
