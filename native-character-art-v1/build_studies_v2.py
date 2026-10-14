from pathlib import Path
import xml.etree.ElementTree as ET
import re,json
from studio.craft import Session
out=Path('production/native-character-art-v1').resolve();ns='http://www.w3.org/2000/svg';ET.register_namespace('',ns)
root=ET.parse(out/'Cemi-editable-trace.svg').getroot()
paths=[]
for el in root.iter('{'+ns+'}path'):
 nums=[float(v) for v in re.findall(r'-?\d+(?:\.\d+)?',el.get('d',''))]
 if len(nums)<4:continue
 xs=nums[0::2];ys=nums[1::2];paths.append((el,(min(xs),min(ys),max(xs),max(ys))))
studies=[
 ('center-character',(413,78,1210,680),'M 583 680 L 567 604 L 581 550 L 572 521 C 549 526 543 538 529 537 L 507 523 L 484 528 L 465 514 L 443 539 L 430 529 L 443 489 L 451 456 L 472 437 L 479 405 L 499 399 L 529 426 L 556 439 L 578 430 L 583 376 L 608 316 L 627 284 L 620 262 L 610 241 L 600 222 L 608 198 L 600 182 L 606 162 L 620 148 L 627 120 L 649 119 L 661 97 L 688 101 L 711 83 L 734 94 L 758 84 L 780 96 L 807 92 L 819 112 L 842 123 L 853 149 L 842 177 L 850 201 C 891 207 928 233 956 278 C 1023 285 1080 331 1105 413 L 1114 444 L 1100 475 L 1118 496 L 1146 487 Q 1165 481 1164 498 L 1139 528 L 1151 542 L 1187 547 Q 1205 554 1190 568 L 1150 568 L 1151 586 L 1178 609 Q 1186 626 1167 624 L 1131 606 L 1108 586 L 1073 589 L 1034 611 L 969 627 Q 931 629 937 610 L 975 574 L 977 565 L 941 585 L 891 595 L 908 646 L 957 680 Z'),
 ('elder-character',(112,42,637,645),'M 139 489 L 151 448 L 158 407 L 167 375 L 169 352 L 183 339 L 190 283 L 206 229 L 229 215 L 246 231 L 267 230 L 286 258 L 313 279 L 345 281 L 348 262 L 310 222 L 300 192 L 289 174 L 292 147 L 305 116 L 316 88 L 340 59 L 382 46 L 425 53 L 459 81 L 477 112 L 493 160 L 525 177 L 556 184 L 576 212 L 592 247 L 624 271 L 635 302 L 609 311 L 589 349 L 576 384 L 552 405 L 530 418 L 508 397 L 487 393 L 471 418 L 452 433 L 433 454 L 420 501 L 437 548 L 454 558 L 477 558 L 525 544 L 569 529 L 553 590 L 537 642 L 219 642 L 209 581 L 190 558 L 168 543 L 146 522 Z'),
 ('right-character',(990,30,1557,660),'M 1001 275 C 1051 258 1091 265 1143 237 L 1173 218 L 1165 185 L 1141 166 L 1144 138 L 1155 108 L 1186 76 L 1223 48 L 1268 31 L 1300 35 L 1320 51 L 1321 70 L 1333 94 L 1332 111 L 1343 130 L 1334 150 L 1335 176 L 1315 199 L 1306 227 L 1287 254 L 1283 276 L 1314 299 L 1367 345 L 1385 331 L 1397 299 L 1412 280 L 1427 282 L 1438 304 L 1445 318 L 1436 333 L 1430 315 L 1418 305 L 1415 335 L 1436 350 L 1461 361 L 1473 391 L 1468 411 L 1453 397 L 1442 376 L 1426 371 L 1452 423 L 1473 433 L 1490 454 L 1512 470 L 1531 479 L 1547 506 L 1543 527 L 1523 544 L 1512 581 L 1460 610 L 1423 638 L 1208 660 L 1222 595 L 1215 550 L 1185 506 L 1159 476 L 1154 435 L 1114 391 L 1087 336 L 1046 300 Z')]
manifest=[]
for name,box,mask in studies:
 svg=ET.Element('{'+ns+'}svg',{'width':'1672','height':'941','viewBox':'0 0 1672 941'})
 g=ET.SubElement(svg,'{'+ns+'}g',{'id':'trace-art','data-name':'Native detailed trace - editable color paths'})
 n=0
 for el,b in paths:
  if b[2]>=box[0] and b[0]<=box[2] and b[3]>=box[1] and b[1]<=box[3]:g.append(el);n+=1
 inp=out/(name+'-vector-source.svg');ET.ElementTree(svg).write(inp,encoding='utf-8',xml_declaration=True)
 with Session('vectorcraft',Path.cwd(),out/(name+'-receipts-v2')) as s:
  s.connection.server.timeout=300
  def cmd(c,**p):return s.call('run_command',{'command':c,'params':p})
  s.call('open_file',{'path':str(inp)})
  s.call('save_file',{'path':str(out/(name+'-import.vectorcraft'))})
  doc=json.loads((out/(name+'-import.vectorcraft')).read_text())['document']
  art=doc['layers'][0]['kind']['children'][0]['id']
  cmd('object.setProps',id=art,name='Editable color paths - traced from supplied poster')
  cut=s.call('draw_path',{'d':mask,'fill':'#ffffff','stroke':'none'})
  print(name,'mask',cut,flush=True)
  cmd('select.set',ids=[art,cut['id']]);clip=cmd('object.clippingMask.make')['id']
  cmd('object.setProps',id=clip,name='Visible character study - editable silhouette mask')
  cmd('artboard.setProps',index=0,x=box[0],y=box[1],width=box[2]-box[0],height=box[3]-box[1],name=name)
  cmd('document.setup',backgroundContents='transparent')
  # Reference is embedded but hidden; it never supplies pixels to the exported study.
  ref=cmd('layer.new',name='REFERENCE - original direction - hidden and locked')['id']
  cmd('file.place',path=str(out/'ART-DIRECTION.png'),rect=[0,0,1672,941],link=False)
  cmd('layer.setProps',id=ref,visible=False,locked=True)
  cmd('select.none')
  s.call('save_file',{'path':str(out/(name+'.vectorcraft'))})
  s.call('export',{'path':str(out/(name+'.png')),'format':'png'})
  s.call('export',{'path':str(out/(name+'.svg')),'format':'svg'})
  manifest.append({'name':name,'trace_paths':n,'method':'VectorCraft trace expanded to paths; native hand-authored silhouette mask','status':'exploratory; not a clean redraw or rig'})
  print(name,n,'saved',flush=True)
(out/'studies.json').write_text(json.dumps(manifest,indent=2))
