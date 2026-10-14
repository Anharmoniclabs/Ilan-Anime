from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np,json
p=Path('production/runs/episode1-native-inserts/tasks/room-filters-coin-blackout')
d=p/'S05-13';a=np.array(Image.open(d/'sources/coin-rgba.png').convert('RGBA'));specks=int(((a[:,:,3]>0)&(a[:,:,3]<=1)).sum());a[:,:,3][a[:,:,3]<=1]=0
im=Image.fromarray(a).resize((1280,720),Image.Resampling.LANCZOS);im.save(d/'coin-matte-clean.png')
s=json.load(open(d/'shot.json'));s['layers'][2]['source']=str((d/'coin-matte-clean.png').resolve());(d/'shot.json').write_text(json.dumps(s,indent=2))
r=json.load(open(d/'registration.json'));r['alpha_cleanup']={'removed_alpha_1_pixels':specks,'original_preserved':True,'threshold':'alpha <= 1 set to 0 before resample','new_bbox':im.getchannel('A').getbbox()};r['rest_bottom_y']=im.getchannel('A').getbbox()[3]-1+98;r['opaque_contact_bottom_y']=int(np.where(np.array(im)[:,:,3]>128)[0].max())+98;(d/'registration.json').write_text(json.dumps(r,indent=2))
rec=json.load(open(d/'native-recipe.json'));txt=json.dumps(rec).replace('/coin-rgba.png','/coin-matte-clean.png').replace('"coin-rgba.png"','"coin-matte-clean.png"');(d/'native-matte-recipe.json').write_text(txt)
# Object-shaped masks avoid mismatched rectangular plate patches at endpoints.
d=p/'S04-02';im=Image.open(d/'sources/selected-original.png').convert('RGBA').resize((1280,720),Image.Resampling.LANCZOS)
for name,poly in [('pipe',[(0,457),(88,457),(105,447),(136,444),(165,460),(189,489),(204,530),(213,560),(205,590),(181,620),(145,628),(100,614),(0,614)]),('projector',[(1058,529),(1070,518),(1091,518),(1092,494),(1109,494),(1109,469),(1150,469),(1154,452),(1188,451),(1199,474),(1280,474),(1280,629),(1100,629),(1100,580),(1072,580),(1058,565)])]:
 mask=Image.new('L',(1280,720));ImageDraw.Draw(mask).polygon(poly,fill=255);out=im.copy();out.putalpha(mask);out.save(d/(name+'-masked.png'))
s=json.load(open(d/'shot.json'))
for l in s['layers']:
 for name in ['pipe','projector']:
  if l.get('source','').endswith('/'+name+'.png'):l['source']=str((d/(name+'-masked.png')).resolve())
(d/'shot.json').write_text(json.dumps(s,indent=2));rec=json.dumps(json.load(open(d/'native-recipe.json')))
for name in ['pipe','projector']:rec=rec.replace('/'+name+'.png','/'+name+'-masked.png').replace('"'+name+'.png"','"'+name+'-masked.png"')
(d/'native-matte-recipe.json').write_text(rec)
