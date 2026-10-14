# S01-07 continuity register — submitted draft

This is a script-supervision handoff, not new animation, a technical motion approval, or author approval. No story or shot-duration change is proposed.

| Continuity item | Required behavior | Evidence / disposition |
|---|---|---|
| Shot / duration | S01-07, 168 frames at 24 fps; episode interval [1416,1584), 00:59:00–01:06:00 | `projects/cemi_episode_01/data/episode.json`, S01-07 object (lines 111–120); `EPISODE_SCRIPT.md` lines 432–436 agree. |
| Frame / aspect | 16:9, character drawings on 3s, 56 three-frame slots | Current user/project direction overrides historical 4:3. Exact artwork is 1672×941, approximately 16:9; layout must preserve proportions and choose an intentional crop to exact delivery aspect, not stretch it. |
| Character | First Counter, a second man on the bank, seated on a stump | Script line 433. This shot adds no canoes or second visible man. “Second man” identifies him relative to preceding soldier action. |
| Identity | Source cap, short beard, brown outer clothes, light collar/cuffs, adult build | Directly viewed exact provisional S01-07 PNG. It is not an author-approved model. S12 thin man and S14 Vale are visual rhymes, not permission to merge identities. Script line 436 and cast note line 121. |
| Gaze | Eyes remain down; he never looks at canoes | Script line 433. The medium shot must establish this; close-up must not imply an off-screen turn or changed head pose. |
| Weight / support | Seat on stump; open ledger on knee; opposite hand supports ledger edge | Script plus directly viewed frame. Maintain seat, knee, supporting-hand and book contacts, even while wrist and writing arm articulate. |
| Action order | One line, then another below it | Script line 433. Two newly written lines must be legible as separate actions with a connected lift/return/landing. No page turn, glance, third line or invented spoken line. |
| Quill / hand | Writing hand screen-left in source; grip/nib/feather stay coherent | Direct inspection. Do not mirror the hand or make feather/shaft deform to reach a new nib location. |
| Camera | Low-angle medium shot with pen/page close-up insert, fixed framing | Script lines 432,434. Proposed cut at local frame18 is production blocking for director review; the script does not prescribe its exact frame. |
| Setting / lighting | Dark mangrove bank, stump, warm localized light and dark roots | Exact source shows a visible flame/torch at far left. Keep holder/roots rigid and animate flame/light separately. |
| Sound / dialogue | Silent picture now; no dialogue assigned here | Script line435 reserves exaggerated pen scratches for later sound work. Preserve contact frame cues; do not add a silent talking performance. |
| Adjacent continuity | Before: three children lift blue vapor (S01-06); after: girl speaks and Dairon turns bow (S01-08) | Script lines427–442. Bank cutaway must remain geographically independent of canoe action; no change to adjacent timing. |

## Contradiction log and dispositions

1. **No shot timing contradiction.** Script, episode JSON and current picture packet agree on 168 frames / 24fps / [1416,1584). Arithmetic in `draft-timing.json` is machine-checked. Older unresolved S01-11/12 issues do not alter this shot.
2. **Packet equal-quarter phases are proposals, not author timing.** Its own `allocation_status` calls them proposed blocking. This handoff proposes [0,18) setup, [18,63) first line, [63,90) return/landing, [90,141) second line, [141,156) finish, [156,168) punctuation hold. This retains all script actions and duration, shortens the long return, and makes the authorized close-up available while writing actually happens. Episode-director review must accept or revise this allocation; no new author approval is asserted.
3. **Packet camera wording versus FIX_HOLD.** “Follows authored action phase framing” is treated as view selection, not a tracking move. The script explicitly calls FIX_HOLD, so both proposed views are locked. No pan/zoom substitutes for writing.
4. **Selected-moment text says offscreen torch; actual reference contains a visible torch.** Preserve actual supplied staging unless layout proposes a reviewed crop. The script requests lantern-type cel shading, not a compulsory lantern prop swap. No additional light source or prop redesign is introduced.
5. **Old broad comic-style direction versus latest 1990s anime correction.** `production/art_direction.json` latest author style correction supersedes its older generic graphic-novel wording. Retain current supplied anime source appearance; this script task does not approve character design or repaint style.
6. **Prior outputs are rejected/exploratory.** The independent writing review F1–F4 rejects long active holds, disconnected return, polygon seams/lower-line contact and mechanical ink. The later 36-cell report documents only 4px/6px net registered nib advance, disconnected landing and feather contamination. These are diagnostic sources, never an accepted drawing bank. No video was inspected in this task; review findings are attributed to the saved reviewer/report.

## Change impact and unresolved work

No change to story, dialogue, cast, episode frame count, neighboring cuts, budget or sound scope. Within-shot allocation and proposed insert cut need the designated episode-director's technical draft review. Layout must establish measurable paper bounds, exact nib coordinates, clean cuff-root registration and usable CU geometry before key/breakdown production. This task intentionally does not invent those unmeasured coordinates.

Actual controlled writing drawings are still missing. Source inspection and frame arithmetic do not establish motion. The drawing and motion dependencies do not block submission of this bounded script-supervision task; they do block downstream animation completion. Final identity/canonical approval remains separate.

## Inspection and provenance

Directly viewed `production/runs/episode1-anime90s-scenes/tasks/opening/generated/S01-07.png` at its native source size (1672×941). Observed down gaze, seated weight, open ledger, writing grip/nib, supporting hand, visible left torch, dark mangrove roots. Read the current script, matching episode object, picture packet, art-direction contract, prior review and revision report, AGENTS, worker/role contracts, README, status and animation audit. Did not inspect rejected videos, new motion, sound or native projects in this script task. `draft-timing.json` preserves SHA256 citations for all assigned inputs and the exact generated 56-slot exposure proposal.
