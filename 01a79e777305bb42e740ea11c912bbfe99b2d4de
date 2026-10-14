import json, hashlib, shutil
from pathlib import Path
from studio.craft import ROOT, Session
OUT=ROOT/'production/runs/cemi-90s-production/tasks/river-character-library'
SRC=ROOT/'research/archive_imports/river_2026_10_11/Cemi-River-Scene/01-Characters'
def write(path,obj): path.write_text(json.dumps(obj,indent=2)+'\n')
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
notes=[
('Amaias son','Short dark wavy curls, round toddler face, white sleeveless tunic and shorts; standing front, side, back; seated reach; three bust expressions including asleep.','S01-02, S01-13, S01-14','Sleeping fullbody supported against Amaia ribs; closed-eye registered speech mouth set; body contact and turn counterbalance.'),
('Dairon','Lean muscular adult, long dark tied curls, pale one-shoulder cloth, russet wrap, barefoot; wooden paddle and seated power-stroke pose.','S01-02, S01-08, S01-09, S01-12, S01-14','Seated reach/plant/pull/lift/recovery drawings using fixed paddle shaft and grips; bow-turn bracing; hair and cloth reversal.'),
('Yara','Broad adult woman, long thick single braid, white sleeveless top, ochre wrap, barefoot; cradled round cloth bundle and seated protective pose.','S01-02, S01-09, S01-14','Seated torso-turn and counterbalance with rigid cloth-wrapped cemi, accurate finger overlap; braid and skirt overlap surfaces.'),
('Beheto','Older angular man, gray swept-back tied hair, hollow cheek planes, pale wrap top, charcoal wrap, rope-tensioned drum; seated palms contact pose.','S01-02, S01-11, S01-12, S01-14','Registered hover/contact/weight press/settle drawing sequence on fixed drum; breathing torso; seated anatomy and hidden hand/drum contact surfaces.'),
('Seven-year-old girl','Long dark curls with half-up braid, blue sleeveless tied dress, barefoot; worried brows, kneeling outstretched hand, three expressive busts.','S01-02, S01-04, S01-06, S01-08, S01-14','Seated forearm lift, bankward lean, fever insert, confident water-facing speech mouth set; fullbody turn with fixed contact.'),
('Nine-year-old boy','Short dense dark curls, red rough tunic, pale sash and knee shorts; seated bent knee and three worried/speech/downcast busts.','S01-02, S01-04, S01-06, S01-10, S01-14','Seated forearm lift and bankward lean; bell-facing head tilt and registered speech mouths; fever insert and turn counterbalance.'),
('Third lit child proposal','Smaller child, soft short dark hair, faded green tunic and pale shorts, bare feet; seated knees hugged; open-mouth and downcast busts.','S01-02, S01-04, S01-06, S01-14','Identity and age remain proposal; seated arm lift from knee-hug pose, bankward lean, fever insert and turn counterbalance.'),
('Background survivor 1','Older broad woman, gray temples and low bun, muted purple top, blue wrap with gray sash, paddle; seated stroke and three busts.','S01-02, S01-09, S01-12, S01-14','Current-script canoe assignment needed before layout; registered seated stroke phases, stable paddle grip, cloth reversal and counterbalance.'),
('Background survivor 2','Young lean man, short wavy dark hair, blue tunic, pale sash and tan knee trousers, paddle; kneeling stroke and expressive busts.','S01-02, S01-09, S01-12, S01-14','Current-script canoe assignment needed before layout; seated or kneeling stroke phases with fixed shaft and hands; bracing and reverse wind.'),
('Background survivor 3','Broad stocky man, jaw-length straight dark hair, ochre tunic and blue knee trousers, paddle; seated rowing pose and three busts.','S01-02, S01-09, S01-12, S01-14','Current-script canoe assignment needed before layout; seated stroke cycle, stable blade proportions and hand grip; heavy-body turn response.'),
('Bell-bearing soldier','Bearded adult with steel brimmed helmet, metal cuirass, quilted brown sleeves, dark breeches and boots; pole-mounted brass bell and braced lifting pose.','S01-05, S01-06','Pole lift/ring/recover drawings with separate rigid bell, suspension and free clapper; hand/pole contact; helmet and armor occlusion surfaces.'),
('Ledger keeper','Middle-aged receding wavy hair, short beard, pale collar, dark pleated coat with puff sleeves, belt inkpot, fitted trousers and shoes; stump-seated writing pose.','S01-07, S01-14','Writing hand and quill/page-contact registered sequence; finish-line and book-close sequence; separate stump, ledger, quill and inkpot. Do not identify with thin man or Vale.')]
rows=[]
for source, note in zip(sorted(SRC.glob('*.png'))[1:],notes):
 slug=source.stem.lower(); dest=OUT/slug; dest.mkdir(exist_ok=True)
 snapshot=dest/'source.png'; shutil.copy2(source,snapshot)
 row={'id':slug,'name':note[0],'status':'exploratory','kind':'editable-reference-library','source':str(source.relative_to(ROOT)),'source_sha256':sha(source),'snapshot':'source.png','identity_observations':note[1],'script_shots':note[2].split(', '),'missing_art':note[3], 'directly_viewed':True,'source_approval':'not established by this task','rig_status':'not built','registration_status':'not registered','motion_status':'not tested','native':'../native/'+slug+'.pcraft','layer_design':['Archived source - unchanged pixels','Editable full-sheet reference - unchanged duplicate'],'separated_parts':False,'separation_decision':'Opaque painted backgrounds, pose-specific overlaps and missing hidden surfaces prevent honest production-part separation. Retain full reference views for new drawings; no automatic matte or cutout claimed.'}
 write(dest/'reference.json',row); rows.append(row)
steps=[]
for row in rows:
 slug=row['id']; base='${OUT}/'+slug
 steps += [
 {'app':'photocraft','tool':'doc_open','arguments':{'path':str((OUT/slug/'source.png').relative_to(ROOT))}},
 {'app':'photocraft','tool':'command_run','arguments':{'id':'layer.setProps','params':{'name':'Archived source — identity unapproved','locked':False}}},
 {'app':'photocraft','tool':'command_run','arguments':{'id':'layer.duplicate','params':{}}},
 {'app':'photocraft','tool':'command_run','arguments':{'id':'layer.setProps','params':{'name':'Editable reference sheet — not rig parts','locked':False}}},
 {'app':'photocraft','tool':'doc_save','arguments':{'path':base+'.pcraft'}},
 {'app':'photocraft','tool':'doc_export','arguments':{'path':base+'.png'}},
 {'app':'photocraft','tool':'command_run','arguments':{'id':'file.close','params':{}}}]
write(OUT/'recipe.json',{'description':'Native editable reference packaging only; unchanged source images. Not completed rigs or new character artwork.','outputs':[r['id']+'.pcraft' for r in rows],'steps':steps})
write(OUT/'library-manifest.json',{'task_id':'river-character-library','status':'exploratory','characters':rows,'source_precedence':['current author corrections in production/art_direction.json','current EPISODE_SCRIPT.md','approved identity references when supplied','archived river proposal sheets'],'limitations':['Original author pencil portraits are unavailable in these assigned inputs; no identity approval inferred.','Historical archive canoe placements are not promoted over the current script.','All 12 sheets are opaque multiview references; no alpha atlas, registered joints or motion validation exists.','Source views include fullbody, expressions and one action; these do not form completed action cycles.']})
print('recipe and twelve reference manifests written')
