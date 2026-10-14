from pathlib import Path
import json,subprocess
from PIL import Image,ImageDraw
from studio.craft import Session
from studio.paths import ROOT
p=Path(__file__).resolve().parent
with Session('filmcraft',ROOT,p/'film-evidence-review') as fc:
 imported=fc.call('media_import',{'text':str(p/'S01-03-three-losses-silent-review.mp4')})
 fc.call('command_run',{'id':'file.newSequence','params':{'name':'S01-03 three losses silent draft','width':1280,'height':720,'fps':24,'fromItem':imported['items'][0]}})
 fc.call('command_run',{'id':'file.saveAs','params':{'path':str(p/'edit-review.filmcraft')}})
 (p/'film-timeline-review.json').write_text(json.dumps(fc.call('sequence_inspect',{}),indent=2))
probe=subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(p/'S01-03-three-losses-silent-review.mp4')])
(p/'probe-review.json').write_bytes(probe)
for page in range(8):
 s=Image.new('RGB',(1280,1176))
 for slot in range(24):
  f=page*24+slot;im=Image.open(p/'decoded-review'/f'{f+1:06}.png').resize((320,180));x=(slot%4)*320;y=(slot//4)*196;s.paste(im,(x,y));ImageDraw.Draw(s).text((x+4,y+181),f'frame {f}',fill='white')
 s.save(p/'review-review'/f'decoded-sequential-{page+1:02}.jpg',quality=93)
for page,frames in enumerate([list(range(111,147,3)),list(range(147,183,3))]):
 s=Image.new('RGB',(1440,1440))
 for slot,f in enumerate(frames):
  # camera varies; crop includes the head through entire approach
  im=Image.open(p/'decoded-review'/f'{f+1:06}.png').crop((160,0,650,470)).resize((480,450));x=slot%3*480;y=slot//3*480;s.paste(im,(x,y));ImageDraw.Draw(s).text((x+5,y+455),f'frame {f}',fill='white')
 s.save(p/'review-review'/f'decoded-head-{page+1}.jpg',quality=94)
print('FilmCraft saved; probe and decoded sheets written')
