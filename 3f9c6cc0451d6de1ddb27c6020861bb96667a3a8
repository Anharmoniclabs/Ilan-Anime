from pathlib import Path
import json,subprocess,shutil,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[5]))
from studio.craft import Session,ROOT
from studio.paths import write_json
out=Path(__file__).resolve().parent
native=out/'native-r1'
frames=out/'frames';frames.mkdir(exist_ok=True)
with Session('effectcraft',ROOT,out/'render-evidence') as s:
 s.call('open_project',{'path':str(native/'shot.ecproj')})
 write_json(out/'native-inspection.json',s.call('get_project',{}))
 for f in range(0,384,3):
  p=frames/f'{f:06d}.png'
  s.call('render_frame',{'time':f/24,'path':str(p),'inline':False,'max_side':0})
  for n in [1,2]:shutil.copyfile(p,frames/f'{f+n:06d}.png')
  if f%48==0:print('Rendered',f,flush=True)
subprocess.run(['ffmpeg','-v','error','-n','-framerate','24','-i',str(frames/'%06d.png'),'-frames:v','384','-an','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-colorspace','bt709','-color_primaries','bt709','-color_trc','bt709',str(out/'preview.mp4')],check=True)
with Session('filmcraft',ROOT,out/'film-evidence') as s:
 r=s.call('media_import',{'text':str(out/'preview.mp4')})
 s.call('command_run',{'id':'file.newSequence','params':{'name':'S14-03 r1 / silent','width':1280,'height':720,'fps':24,'fromItem':r['items'][0]}})
 s.call('command_run',{'id':'file.saveAs','params':{'path':str(out/'edit.filmcraft')}})
 write_json(out/'timeline.json',s.call('sequence_inspect',{}))
print('Saved native picture and editorial timeline.',flush=True)
