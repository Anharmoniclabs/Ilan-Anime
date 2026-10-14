from pathlib import Path
import json
from studio.craft import Session
from studio.paths import ROOT
p=Path(__file__).resolve().parent
with Session('filmcraft',ROOT,p/'film-evidence') as fc:
 imported=fc.call('media_import',{'text':str(p/'S01-03-partial-silent.mp4')})
 fc.call('command_run',{'id':'file.newSequence','params':{'name':'S01-03 exploratory partial silent','width':1280,'height':720,'fps':24,'fromItem':imported['items'][0]}})
 fc.call('command_run',{'id':'file.saveAs','params':{'path':str(p/'edit.filmcraft')}})
 timeline=fc.call('sequence_inspect',{})
 (p/'film-timeline.json').write_text(json.dumps(timeline,indent=2))
print('FilmCraft saved')
