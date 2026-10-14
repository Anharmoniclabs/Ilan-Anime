"""One bounded, resumable Nessa production: Qwen reference art -> Wan real motion.

Run with --stage image, video or all. No training or new GPU rental is performed.
"""
import argparse
import json
from pathlib import Path
import time
from agentharness.agent import Agent,AgentConfig
from agentharness.cloud import cloud_clients,load_token
from agentharness.llm import ToolCall
from agentharness.workspace import Workspace

root=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--stage',choices=['image','video'],default='image')
a=p.parse_args()
shot=json.loads((root/'shots/pilot.json').read_text())
ws=Workspace.direct(root,Path.home()/'.agentharness/runs'/('cemi-pilot-'+str(time.time_ns())))
agent=Agent(cloud_clients(load_token())[0],ws,config=AgentConfig(require_approval=False,permission_mode='bypass'))
agent.task='Execute the authorized book-grounded Cemi pilot, within one image and one video submission. Resume existing jobs.'
def call(name,**args):
    out=agent._execute(ToolCall(name,name,args),[name],dedupe=False)
    print(out,flush=True)
    if out.startswith(('ERROR:','TIMEOUT')):raise SystemExit(1)
    return out
def stage(name,path,**args):
    receipt=Path(path).with_suffix('.cloud-job.json')
    if not (root/receipt).exists():call(name,path=path,**args)
    deadline=time.monotonic()+1200
    while time.monotonic()<deadline:
        call('media_job',job=str(receipt))
        record=json.loads((root/receipt).read_text())
        if record['status']=='generated':
            call('production_update',operation='asset',data=dict(id=shot['id']+'-'+name,path=path,role=name))
            return
        if record['status'] not in ('queued','running'):raise SystemExit('Job needs inspection; no retry.')
        time.sleep(10)
    raise SystemExit('Wait budget reached; run the same command to resume without submitting again.')
call('production_update',operation='brief',data=dict(project='Heralds of the Cemí',
    source='sources/Heralds_of_the_Cemi.pdf',pilot=shot['id'],source_pages=shot['source_pages'],
    stage='reference art and real I2V pilot',lora='not trained; insufficient approved dataset',
    requested_backend='RunPod / Qwen / Wan-Animate',active_backend='HF / Qwen-Edit-2509 / Wan-I2V-A14B'))
if a.stage in ('image','all'):
    if shot.get('image_strategy','').startswith('text-to-image'):
        if not (root/shot['image_path']).exists():
            call('image_generate',path=shot['image_path'],prompt=shot['image_prompt'],
                 model=shot['image_model'],width=1664,height=928,seed=shot['seed'])
        call('production_update',operation='asset',data=dict(id=shot['id']+'-image',path=shot['image_path'],role='keyframe'))
    else:
        stage('image_edit',shot['image_path'],prompt=shot['image_prompt'],images=shot['reference_images'],seed=shot['seed'])
if a.stage in ('video','all'):
    if not (root/shot['image_path']).is_file():raise SystemExit('Generate the keyframe first.')
    stage('video_generate',shot['video_path'],prompt=shot['video_prompt'],image=shot['image_path'],
          seed=shot['seed'],frames=shot['frames'],resolution=shot['resolution'])
print('Requested stages completed. Inspect visual continuity and acting; technical success is not aesthetic approval.')
