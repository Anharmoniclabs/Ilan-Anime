from pathlib import Path
import shutil,json
from studio.craft import Session
out=Path('production/native-character-art-v1').resolve()
shutil.copy2('/tmp/codex-clipboard-UsRbGb.png',out/'ART-DIRECTION.png')
with Session('vectorcraft',Path.cwd(),out/'trace-receipts') as s:
 s.connection.server.timeout=300
 def cmd(c,**p):
  r=s.call('run_command',{'command':c,'params':p});print(c,str(r)[:450],flush=True);return r
 cmd('file.new',name='Cemi - supplied art direction - editable trace',width=1672,height=941,units='Pixels')
 r=cmd('file.place',path=str(out/'ART-DIRECTION.png'),rect=[0,0,1672,941],link=False)
 print('PLACED',r,flush=True)
 r=cmd('imageTrace.makeAndExpand',params={'mode':'color','colors':256,'paths':95,'corners':85,'noise':1,'method':'abutting','ignoreWhite':False})
 s.call('save_file',{'path':str(out/'Cemi-editable-trace.vectorcraft')})
 s.call('export',{'path':str(out/'Cemi-editable-trace.svg'),'format':'svg'})
 s.call('export',{'path':str(out/'Cemi-editable-trace.png'),'format':'png'})
 tree=s.call('inspect_document',{});(out/'trace-tree.json').write_text(json.dumps(tree,indent=2))
 print('SAVED',flush=True)
