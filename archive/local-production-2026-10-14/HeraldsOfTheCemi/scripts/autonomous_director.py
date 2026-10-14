"""Nessa's model-driven director: actual Agent.run, not a scripted media sequence."""
from dataclasses import asdict
import json
from pathlib import Path
import subprocess
import time

from agentharness.agent import Agent,AgentConfig
from agentharness.checks import CheckRunner,CheckResult
from agentharness.cloud import FallbackClient,cloud_clients,load_token
from agentharness.llm import ChatClient
from agentharness.workspace import Workspace

root=Path(__file__).resolve().parents[1]
work=Path.home()/'.agentharness/runs'/('cemi-autonomous-'+str(time.time_ns()))
ws=Workspace.direct(root,work)
clients=cloud_clients(load_token(),models=['zai-org/GLM-5.3'],max_tokens=8192,timeout=180)
for configured in clients:
    configured.reasoning_effort='low'
clients.append(ChatClient('http://127.0.0.1:11435/v1','nessa-lfm-32k',timeout=60,max_tokens=4096))
client=FallbackClient(clients)
counts={'image':0,'video':0}

def authorize(name,args):
    # Fresh-output contracts also prevent a subsequent script run spending twice.
    if name in ('image_generate','image_edit'):
        if args.get('path')!='art/nessa-shot-02.png' or counts['image']:
            return False,'This run permits one image, at art/nessa-shot-02.png.',False
        counts['image']+=1
    elif name=='video_generate':
        if (args.get('path')!='delivery/nessa-shot-02.mp4' or args.get('image')!='art/nessa-shot-02.png'
                or counts['video'] or args.get('frames',81)>81):
            return False,'One video of the new image, up to 81 frames, at delivery/nessa-shot-02.mp4.',False
        counts['video']+=1
    elif name=='write_file':
        if args.get('path') not in ('shots/nessa-shot-02.json','shots/nessa-director-report.md'):
            return False,'Write only the shot manifest or director report.',False
    elif name=='media_job':
        if args.get('job') not in ('art/nessa-shot-02.cloud-job.json','delivery/nessa-shot-02.cloud-job.json'):
            return False,'Collect only this run’s image/video jobs.',False
    elif name=='production_update':
        if args.get('operation') not in ('asset','review'):
            return False,'This run may register assets and attributed review notes.',False
    else:
        return False,'Operation outside the bounded director run.',False
    return True,'User authorized autonomous Cemí production; bounded director run.',False

def grade(workspace):
    try:
        r=workspace.repo
        manifest=json.loads((r/'shots/nessa-shot-02.json').read_text())
        assert isinstance(manifest.get('source_pages'),list) and manifest['source_pages']
        assert all(type(n) is int and 11<=n<=18 for n in manifest['source_pages'])
        assert manifest.get('canon') and manifest.get('design_proposals')
        assert (r/'art/nessa-shot-02.png').stat().st_size>10000
        path=r/'art/nessa-shot-02.png'
        assert not (r/'delivery/nessa-shot-02.cloud-job.json').exists(), 'Animation must wait for user approval.'
        subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(path),'-f','null','-'],
                       capture_output=True,check=True,timeout=45)
        return CheckResult('tests','passed',exit_code=0,output='Source page references, separate canon/design fields and PNG decoding pass. No animation submitted. Awaiting explicit user image approval.')
    except Exception as e:
        return CheckResult('tests','failed',exit_code=1,output='Delivery incomplete or invalid: '+type(e).__name__+': '+str(e)[:400])

def event(name,data):
    row={'event':name,**data}
    if row.get('event') in ('model','tool','check','operation_started','operation_finished','error'):
        print(json.dumps({k:row[k] for k in ('event','name','status','phase','model','output') if k in row},ensure_ascii=False)[:1000],flush=True)

agent=Agent(client,ws,config=AgentConfig(require_approval=False,plan_first=False,
    permission_mode='default',allow_subagents=False,max_steps=48,time_budget=900,
    baseline_checks=False,verify=('tests',),continuous_verify=(),full_verify_every_edits=0),
    checks=CheckRunner({'tests':grade}),asker=authorize,on_event=event)
allowed={'read_file','list_dir','search','outline','graph_search','instructions','use_skill',
         'list_skills','write_file','production_status','production_update','studio_dataset_check',
         'image_generate','image_edit','media_job','media_probe','run_check','finish','blocked','ask_user'}
agent.tools={k:v for k,v in agent.tools.items() if k in allowed}
# Polling is part of the deterministic tool backend, not another model/agent.
# Space polls to avoid wasting model turns while a GPU job is running.
collect=agent.tools['media_job'].handler
def paced_collect(ctx,args):
    receipt=ctx.ws.path(args['job'])
    if receipt.is_file():
        saved=json.loads(receipt.read_text())
        if saved.get('status') in ('queued','running'):
            time.sleep(max(0,min(10,10-(time.time()-saved.get('checked_at',0)))))
    return collect(ctx,args)
agent.tools['media_job'].handler=paced_collect

task='''You are Nessa directing the next Heralds of the Cemí shot autonomously. The user explicitly authorized you to choose the scene details and call the actual production tools. Do the work, not only a plan.
Read AGENTS.md, shots/pilot.json, and manuscript pages canon/pages/page-013.md through page-015.md. The existing Juan Carlos desk clip is already made. Choose a complementary 5-second insert from those book pages (for example the warm copper coin, contact microphone/steam riser, or the projector); choose your own composition and prompts grounded in the text. Maintain the textured hand-drawn Cemí aesthetic. No invented canon, no final LoRA claims.
Write shots/nessa-shot-02.json with title, source_pages, canon, design_proposals, image_prompt, video_prompt. Then call image_generate with Qwen/Qwen-Image-2512, width 1664, height 928, fresh path art/nessa-shot-02.png. You may instead use image_edit with the existing art as reference if you judge it appropriate, but the run permits only ONE new image request total.
IMPORTANT USER CORRECTION: STOP AFTER THE IMAGE. No animation is authorized until the user sees and approves this exact image. Do not submit any video, and do not mark an agent review as user approval. If using queued image_edit, collect that image with media_job. Register the image asset and run registered tests. Write shots/nessa-director-report.md explaining your choices, actual tool results and source pages, ending with awaiting user image approval. You cannot see images through metadata, so do not claim visual review. Finish after the image checks pass with a link/path to art/nessa-shot-02.png for the user. No shell, training, provisioning or further paid jobs are authorized. If an actual dependency fails, report it honestly.'''
print('NESSA MODEL-DRIVEN RUN',work,flush=True)
result=agent.run(task)
(root/'shots/nessa-autonomous-result.json').write_text(json.dumps(asdict(result),indent=2,default=str))
print('NESSA RESULT',result.status,result.summary,flush=True)
print('TRACE',agent.evidence_dir,flush=True)
raise SystemExit(0 if result.status=='verified' else 1)
