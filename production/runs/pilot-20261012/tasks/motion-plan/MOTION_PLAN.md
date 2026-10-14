# S01-11 / S01-12 — provisional full-scene motion plan

Task: `motion-plan` · Role: `animation-supervisor` · Run: `pilot-20261012`.

Text-only submission for a separate episode-director review. Not drawings, registered exposures, animation, footage approval, or authorization to generate/render. Existing rejected footage remains rejected. No source files were changed.

## Evidence and authority

Repository-relative citations below refer to text directly read for this task. The required script was read completely; only the assigned shots and necessary continuity are planned.

- `AGENTS.md`, `README.md` (“Current production rules”): preserve artwork, exact shot IDs, 16:9 / 24 fps; no whole-painting warping or still-image substitution for acting.
- `docs/STATUS.md:19–21,29–43,45–47`: author rejects warped/sliding motion; atlases are exploratory, with unresolved registration/model/matte issues; the full 24-second passage still needs palm placement, weight, paddle drag/lift/recovery, passenger balance, wakes and current turn. Current corrections and script supersede archived staging.
- `research/animation_audit/REPORT.md:5–20`: documented 576-frame test; stretching faces/cloth, flexible drum/hull, pulsing arms, no credible strokes, hull-attached wakes and foreground-water seam. These are the earlier auditor's observations, not a new viewing by this worker.
- `projects/cemi_episode_01/data/EPISODE_SCRIPT.md:376,398–410,438–489`: timecode convention, restrained/moonless scene, canonical canoe occupants, preceding snapped paddle, assigned shot actions and contradictory showcase notes.
- `projects/cemi_episode_01/data/exposure_sheet.csv:14–15` and `data/shots/S01-11.json`, `data/shots/S01-12.json` beneath the same project: corroborate 240 / 336 frames, rate 2, 1280×720 references, rejected motion / unrigged-reference status, and null audio.
- `projects/cemi_episode_01/assets/replacement_cels/README.md`: three unregistered atlases and a clean plate; invariants not consistently guaranteed. Directory listing confirmed these files and the two numbered keyframe PNGs exist; no pixel-quality claim follows from existence.

## Locked container; unresolved source contradictions

All plan ranges below are zero-based half-open `[start,end)`. The last shown frame is `end−1`. Episode timecodes use `mm:ss:ff` at 24 fps.

| Shot | Episode timecode | Episode frames | Local frames | Passage frames | Duration |
|---|---|---|---|---|---|
| S01-11 | 01:32:00 → 01:42:00 | [2208,2448) | [0,240) | [0,240) | 10 s / 240f |
| S01-12 | 01:42:00 → 01:56:00 | [2448,2784) | [0,336) | [240,576) | 14 s / 336f |
| Combined | 01:32:00 → 01:56:00 | [2208,2784) | — | [0,576) | 24 s / 576f |

Conversion: episode frame = shot start + local frame; passage frame = episode frame − 2208. No retiming or added shots.

Production approval decisions, not blockers to completing this text-only proposal:

1. Script lines 453/459, exposure rows and STATUS agree on 24 seconds; SC-0 heading at line 479 says 22 seconds. Keep the corroborated 24-second container pending explicit director resolution; do not silently shorten it.
2. Shot headers specify 2s; SC-0 line 480 specifies characters on 3s and FX on 2s. The proposed scheduling below uses the shot-header 2s grid for primary action and FX, with holds; the reviewer must choose an authoritative exposure policy before drawing assignment. It is not permission to overwrite the 3s note.
3. SC-0's relative events end at inclusive frame 168 (169 displayed frames), with no mapping to the 576-frame span. Literal use would put the foam turn and paddle overrun inside S01-11, despite S01-12's action. Preserve its causal order as reference, not as a complete approved exposure sheet. The remapped ranges below are editorial proposals, not quoted canonical microtiming.
4. SC-0's shorthand “Beheto, hull+Amaia, front canoe” layer grouping must not relocate Amaia into Beheto's canoe. S01-02 line 408 establishes lead Dairon/Yara/Amaia/son, second Beheto, third three children. Scene layout and draw order need review with actual approved artwork.
5. S01-09 line 444 says a paddle snaps but does not identify owner or replacement. The script permits subsequent paddles but no new intact paddle should appear without continuity review. Do not invent a swap or assign the broken paddle to a named person from this text alone.

## Staging and acting locks

Keep the three canoes in established single file and retain screen direction from the approved adjacent boards. Exact bank side, paddle side, camera axis and visible occlusion are not established by this text-only inspection; lock them from approved layout before production. Do not mirror an atlas to solve a paddle-side mismatch.

The lead canoe retains Dairon paddling, Yara's cloth-wrapped cemí against her chest, and Amaia supporting her sleeping son (under two); Beheto and his drum remain in the second; the three children remain in the third. Only script-established/approved visible paddlers receive stroke animation; do not add anonymous paddlers. Counterbalance is modest, separate from the large communal turn in S01-14. The son's spoken line remains in S01-13; add no speech or wake-up here.

Moonless blue-black/mangrove green-black; blue light belongs to the children. Root-vein gold is low-opacity scripted FX, not a new warm key light. Water does not part or rise. No smears, impact flash, boom, giant magic wave or ornamental camera orbit.

## S01-11: palms → weight → hull → water → roots

Canonical evidence: script lines 453–457. CU Beheto → WS; both palms on drum, body weight transfers, sound travels through hull/water/roots. A low skin-and-wood note without attack. All subranges and drawing counts here are proposals.

| Local range | Episode range | Keys / breakdowns / exposure | Full-scene action and contacts |
|---|---|---|---|
| [0,12) | 01:32:00–01:32:12 | Keys 0 hover, 6 near-contact, 8 both palms landed; 2s, contact cel held [8,12) | Short downward hand arcs, decelerating into skin. Separate tiny skin ripple cels beneath each palm; no hit accent. Drum shell/rim unchanged. |
| [12,48) | 01:32:12–01:34:00 | Torso keys 12,24,36,46; curved-arc breakdowns 18,30,40; 2s between approved keys | Lean from hips with weight going through wrists. Fingers/palm heels remain drum-local locked from frame 8; shoulders advance, elbows fold. Preserve head volume and neck connection. One outward wood-grain pulse proposed [24,60), never flex the hull. |
| [48,96) | 01:34:00–01:36:00 | Weighted pose held; small shoulder/breath cels; ring FX on 2s | Deep note sustains. Subtle drawn ring leaves hull into water; amplitude stays on water-only layer. Root-vein sequence begins away from camera [72,120), one root at a time at low opacity. Boats travel continuously; no cutout sliding over baked wake fragments. |
| [96,144) | 01:36:00–01:38:00 | Proposed internal CU→WS cut at 96; no new shot ID. Wide replacement view needed; 2s action | Show causal path reaching roots while palm contact remains. Beheto's loaded torso settles through two diminishing arcs. Other occupants make small independent balance adjustments; Dairon's established stroke continues. |
| [144,192) | 01:38:00–01:40:00 | Settle key 144, breath compression 168, recovery 190; secondary cels on 2s/holds | Hands remain planted, drum fixed between knees. Breath is restrained, not a whole-face/body pulse. Hulls remain rigid with small common boat motion; seated pelvis/feet retain local supports. |
| [192,240) | 01:40:00–01:42:00 | Load-bearing pose holds, independent cloth/water progress; outgoing wide state at 238 | Let the note/roots diminish without replaying the pulse. Continue real travel and current texture. Preserve baseline foam direction into next shot so its 90° turn is measurable. No second palm landing or unrelated action to fill time. |

Do not interpret every held body drawing as a held full frame: wakes, water, other visible characters and relevant secondary action remain separately timed. The long pressure sustain must read as effort; if it fails at playback, request revised acting/exposures, not mesh deformation.

## S01-12: current turns → boats overrun blades → lift / recover

Canonical evidence: script lines 459–462. WS → MS paddles. Foam turns 90°; boats move only a little faster than paddles; blades drag and lift; water hiss rises. All detailed timing below is proposed. Do not steal the S01-13 dialogue or S01-14 full-body turn/camera roll.

| Local range | Episode range | Keys / breakdowns / exposure | Full-scene action and contacts |
|---|---|---|---|
| [0,48) | 01:42:00–01:44:00 | WS current keys 0/12/24/36/46: foam orientation 0/15/45/75/90°; intermediate drawn FX on 2s | Track the same foam/leaf landmarks through the arc; do not rotate the entire water painting. Canoes yaw only a few degrees in response, with perspective replacement drawings if needed; no rubber hull/shear. |
| [48,96) | 01:44:00–01:46:00 | Overrun key 48, reaction 60, maximum trailing blade 94; 2s | Increase hull travel relative to blade/water landmarks modestly. Dairon's hands stay on fixed shaft grip points; wrists/elbows/torso react to drag, blade trails. Yara secures cemí; Amaia tightens supported cradle without waking son; children make small delayed braces. Beheto keeps weight/contact. |
| [96,144) | 01:46:00–01:48:00 | Proposed MS paddles cut at 96; blade exit 108, lifted key 120, drip release 126/134; 2s | Blade rises in a clear scoop arc, wrist rotates rigid shaft/blade as one object. Waterline occlusion changes at exit. Detached droplets fall independently and rings remain water-local as canoe advances. |
| [144,216) | 01:48:00–01:51:00 | Recovery apex 156, reach 180, near-water 204, soft entry 214; 2s | Low forward recovery arc driven by arms and shoulder, no paddle teleport or switched side. Slow spacing approaching entry; clear clearance from hull, passenger silhouettes and wrapped cemí. Passengers settle with one damped correction, not synchronized bobbing. |
| [216,288) | 01:51:00–01:54:00 | Entry completed 216; restrained pull 228/246; drag 258; lift 276; drip 284; 2s | A second, reduced stroke demonstrates continuing faster current: body/shaft articulation, water anchoring during pull then trail, release and independent wake. Reuse only validated matching drawings, never an unregistered eight-pose loop. |
| [288,336) | 01:54:00–01:56:00 | Recovery 288–318; readable outgoing loaded/settled pose 318–336 with living water and cloth | Maintain new flow direction and continuity into S01-13. Small hair/cloth reversal lags current by a few exposures; do not flip hair geometry. No S01-14 12° camera roll. Optional Amaia reaction framing requires director approval and must not replace requested paddle coverage. |

Water/hiss rises across the turn and overrun, with no newly invented boom or dialogue. Audio cue placements above are proposed sync targets only; no sound was recorded, synthesized or listened to.

## Independent layers, arcs and locks

| Layer group | Required separation / motion rule | Registration / contact check |
|---|---|---|
| Water, foam, leaves, wake, drip rings | Water-plane trajectories independent of hull; wake emitted then left behind/advected; no baked water in canoe alpha | Identify persistent water landmarks; wake must move relative to hull after release |
| Each rigid hull | Rigid object with locked rim/bow/stern geometry; new views drawn for meaningful yaw | Compare lengths/widths in same view; no stretch or squash to fake yaw |
| Beheto body/head/hands | Coherent replacement poses, head/skull stable; hands overlap drum correctly; individual eyelid/breath only when justified | Two palm contact markers fixed in drum space; elbow arc absorbs torso shift; drum supported by knees |
| Drum shell/rim and skin response | Rigid shell/rim separate from local tiny skin ripple | Palms never slide/fuse into rim; skin effect never displaces hands or shell |
| Dairon and paddle | Shaft+blade rigid; both grip points constant along shaft; articulated arm and torso replacements | Grips do not change hand or side; blade submersion/exit respects waterline; no disconnected hand |
| Lead passengers | Yara arms/cemí/cloth; Amaia arms/son; support points fixed to canoe and body | Cemí never floats; son stays cradled/asleep; no hands pass through objects |
| Three children | Separate reaction offsets, stable age/identity and seated support; forearm blue/glow as separate FX | No shared pulsing cutout or new bankward pull invented here |
| Roots / foreground | Solid root art plus accurate object-only occlusion matte, separate low-opacity gold vein cels | No retained foreground water wedge or seam; layered occlusion agrees at first/mid/last and crossings |
| Hair / cloth / wind | Short delayed arcs with damped settle; replacement drawings for reversal | Do not deform faces, body, hull or wrapped prop to animate cloth |
| Camera | Proposed coverage cuts inside parent shots; any approved camera transform applied independently | Camera movement cannot supply missing acting; no silent reframing that hides contacts |

Spacing: close spacing near palm contact and loaded hold; wider torso spacing mid-lean; ease out into pressure without rebound hit. Paddle pull must respond to resistance, then accelerate briefly at release and ease over recovery apex. Passenger recovery trails canoe change rather than anticipating it. No arbitrary pixel amplitudes are approved without layout scale and visual review.

## Existing versus needed drawings

All asset paths here are under `projects/cemi_episode_01/`. Existing means file/metadata evidence only, not usable or approved.

| Existing source | What it supplies now | Still required |
|---|---|---|
| `assets/keyframes/S01-11.png` | Named static reference; shot JSON calls it `reference_only` / `unrigged_reference` | Approved CU and WS layout; coherent hover/contact/lean/settle replacements; registered head/hand/drum landmarks; proper mattes |
| `assets/keyframes/S01-12.png` | Named static reference; same unrigged/rejected status | Three-canoe wide and paddle MS layouts; fixed rigid hulls; complete stroke/overrun/lift/recovery drawings and passenger acting |
| `assets/replacement_cels/beheto_eight_poses.png` | Exploratory hover/contact/press/settle atlas | Inspect each pose; repair identity, drum registration and alpha; create missing breakdowns and any new view; register individually before assigning exposures |
| `assets/replacement_cels/lead_canoe_eight_poses.png` | Exploratory stroke atlas | Reject/repair varying hull and paddle side; isolate approved rigid hull, create correct drag/exit/return/entry and grip continuity; retain correct occupants |
| `assets/replacement_cels/children_six_poses_unapproved.png` | Exploratory look/turn/brace atlas | Check age/identity, alpha, canonical third canoe; draw subtle balanced reactions in approved layout, not automatic atlas replay |
| `assets/replacement_cels/drum_clean_plate.png` | Empty canoe/environment source | Check perspective and occlusion against approved source; clean independently masked water/foreground; not a character animation asset |
| Audit-described cutouts/clean plates/rejected MP4s | Reproducibility and defect evidence only | No production reuse without fresh matte/rigidity review; actual new animation and sound remain outstanding |

Additional needed assets: water-only clean plate, accurate foreground/root masks, stable three-hull views, palm-skin ripple, one wood pulse, subtle water ring, sequential root-vein drawings, foam/leaf 90° path cels, travelling wakes, entry/exit splashes and droplets, hair/cloth reversal drawings and wide/MS replacement viewpoints. Their availability/approval is not established by the task inputs. A clean still plate cannot cover these gaps.

At a 2s scheduling grid there are 120 S01-11 and 168 S01-12 exposure slots per continuously changing layer, not 288 promised unique drawings. Holds/reuse reduce unique art only after contact and action review. An eight-pose atlas does not establish any specific slot as covered. Resolve 2s/3s conflict before budgeting final drawings or delegating inbetweens.

## Handoff and review gates

Coordinator → separate episode-director: resolve the five source/layout decisions above, inspect these proposed beats for pacing and continuity, and choose exposure cadence. If approved as a plan, key-animator next needs approved character/prop/layout references and exact contact keys; inbetweener must wait for supervisor-approved keys and spacing. No authorization for those tasks is implied by this document.

Future animation review must view continuous playback and frame-step contacts; compare first/middle/last and all cuts. Specific targets: S01-11 f6–12 palm landing, f12–48 lean, f48–120 water/root propagation; S01-12 f0–48 foam orientation, f48–108 drag/exit, f108–144 drip, f144–216 recovery/entry, f216–288 repeated stroke. Review entire [0,576) for living scene coverage, not just these samples. Verify all three canoes, occupant identities, sleeping son, grip points, hull/drum rigidity, independent wakes, accurate foreground matte, no warps, and meaningful motion beyond camera transforms. Missing views/drawings or disputed cadence block production approval.

## Inspection statement and task status

Directly inspected: local text sources listed above, task envelope, role instructions, directory/file listings, and this written plan. Directly viewed source images, decoded frames, video playback: none. Audio listened to: none. No render, image generation, media decode, paid action, external call, nested delegation, source edit, or publish performed.

The required text-only planning task is complete and ready for independent review (`submitted`), with no task-completion blockers. The explicitly listed timing, layout, asset and performance-review gates still block any claim of approved production animation. This worker does not self-approve.
