# Episode 1 — art-direction recovery

Author correction: the new anime images are moving away from the established artistic voice. Generation is paused. This is a coordinator review, not independent technical approval or author approval.

## What is preserved

All pre-existing artwork and recent studio/Blender work remain unchanged. The baseline has 78 keyframe PNG files, including the byte-identical S09-04/S09-05 pair, and references artwork for 64 of 128 body shots. File coverage is not action coverage or approval.

Only the new **S01-01 paddle candidate** is included in this recovery change. Its subject, moonless river palette and ink treatment are the strongest fit of the new batch. It remains exploratory, with no final-use link. It still needs author review, water-motion review and a separately composited BEFORE caption.

The other new human frames are retained in the originating workspace but withheld from this push and from production inputs:

| Candidates | Decision / refinement |
|---|---|
| S08-03, S08-04 | Hold. JC reads too youthful; broad golden lighting and polished facial treatment need comparison with author identity references. Preserve scaffold geography, not the new face as a design lock. |
| S09-03, S09-04, S09-06 | Hold. Functional compositions, but repeated attractive/smooth face treatment, glossy highlights and shallow-focus polish are moving away from the intended drawing-led finish. Rodríguez is a new interpretation, not an approved model. |
| S10-01 v1 | Withhold: wrong rectangular luggage-like case. Never use upstream. |
| S10-01 v2 | Case corrected to cylindrical conga case, but character identity/build and backward door-entry staging still need review. Correcting one prop does not approve the frame. |
| S10-02 | Hold. Childhood design derived from unapproved adult Manny; do not make that lineage canonical. Recheck pencil contact and age/build against an approved design. |
| S10-03 | Generation interrupted. No confirmed result, no retry, no completion claim. |

## Refined visual contract for the next pass

Mode: STORY_FRAME (or ENVIRONMENT_PLATE for character-free sets).

1. Attach the author's original drawing/model for identity, an author-selected original episode frame for finish, and the relevant set/prop reference. The original pencil identity sources are still absent from this checkout: do not pretend a prose prompt replaces them.
2. Never derive the next character design from an unapproved generated candidate. The recent batch did this; repetition amplified drift.
3. Preserve individual adult facial construction: angular cheek/jaw/nose, uneven brows, tired grounded eyes, deliberate asymmetry. JC is 25, not a teenager. Manny is 6'3", massive through chest/shoulders/hands, with close-cropped hair—not a generic athletic hero. Mikey is male.
4. Use confident variable-width ink and intentional localized hatching. Simpler coherent painted planes should carry shadow, not smooth beauty-rendered faces or a uniform grit overlay.
5. Full color, not monochrome; navy/steel and charcoal shadows with selective motivated amber. Morning is morning; the river is moonless. Do not turn every scene into golden-hour advertising light or add unsupported moonlight.
6. Keep the prose's acting: exhausted counting, guarded humor, reluctant listening, hesitant touch. No stock heroic poses, huge dramatic eyes, arbitrary smiles or spectacle replacing the scripted action.
7. Sakuga describes performance and drawing quality, not permission to replace this artist's faces with a generic anime style.
8. Compose exact typography separately. Blank phone/card surfaces are intentional plates, not completed text assets. A blank plate cannot close a shot that requires readable information.
9. Check hand-object contact, cylindrical drum case, rigid canoe hull, paddle side, and cast placement. Review closeups at native size and compare adjacent shots.
10. Produce one calibration frame for the author before extending a new human design through a sequence. Existing interrupted work stays paused until explicit resume approval.

### Reusable prompt structure

> Preserve the identity and hand-shaped asymmetry of the attached author drawing. Use the attached original episode frame for ink pressure, controlled hatching and finished color planes, not a newly generated face. Depict [exact single scripted beat], at [scripted time/place]. Acting: [specific restrained emotional action]. Keep [named props/contact points] rigid and anatomically coherent. Lighting comes only from [motivated sources]. No generic anime beautification, youthification, uniform orange wash, glossy 3D rendering, extra text, or unsolicited dramatic effects. One individual 16:9 frame. Preserve the negative space needed for separately composited exact text.

## Remaining artwork / refinement queue

These are the baseline's **64 unresolved shot entries**, not a claim that every entry needs a fresh AI illustration. The new paddle is a candidate; held human images do not close gaps. The machine-readable companion lists each exact script action and original timing.

| Shot IDs | Required pass |
|---|---|
| S00-01–02 | Deterministic sigil line draw and exact epigraph typography. Reuse the established emblem; do not redesign it. |
| S01-01 | Review paddle candidate; generate/animate blade entry, pull, lift and travelling rings. Add BEFORE in post. |
| S05-15 | Reuse established room geography. Prepare equipment/lamp shutoff states and fan spin-down; no new room design. |
| S08-02 | Iris/sigil alignment graphic and exact Aperture wording, not a fresh decorative logo. |
| S08-03–04 | Repair JC identity and morning grade before worker dialogue and walk-away frames. |
| S09-03,04,06 | Lock Rodríguez to author design; correct JC. Rent-math overlay belongs to S09-04; the duplicate map PNG does not satisfy it. |
| S10-01–05 | Lock adult/child Manny; conga case, two coffees, backward entry, palm contact, café acting and Yari phone insert. Separate childhood and adult vignettes rather than one collage. |
| S11-01–06 | Exact email graphics; restrained JC reaction; pocket heat/steamer pitch; phone refusal; Manny conversation. The sleeve-grab memory in S11-05 needs its own insert. |
| S12-01–11 | Matched café/1973 set pair, mic/ear contact, Rodríguez's mustached father, teenage record buyer, Anthony Vale and notebook, milk spill/return, café rhythm, map card. No melting furniture as a substitute for a designed era transition. |
| S13-01–12 | Modern library and matched 1934 room; food/text inserts; cemí views and coin comparison; young JC/Abuela; historical readers as separate staged groups. S13-10 contains several actions and needs multiple individual drawings. |
| S14-01–11 | Sofía identity lock and restrained acting; exact research UI/tree; Adrian Vale and notebook; control café insert; school classroom/teacher/observer/father/Mamá sequence; young male Mikey and stairwell. Split S14-08's multiple locations/actions into individual frames. |
| S15-01–09 | Route graphic; bodega exterior/speaker; stable domino-player designs and anger/exhaustion poses; red-brown energy drain; JC reaction; third-floor window; timed black. PRESS is a directed style change, not random face deformation. |
| ED (outside 128 body shots) | Coin-turn views, map/card stages, exact credits and closing sigil. Existing art can supply selected paintings. Credits' scripted still pans do not justify replacing body-shot acting with pans. |

Also refine S01-03's missing empty-seat ghosts without changing the canoe passenger assignments. Existing frames require continuity and text review; filenames alone are not approval.

## MiniMax handoff constraints

Do not send held designs into MiniMax. Use only author-approved first frames, one coherent action per clip, original shot IDs and 24 fps timeline. An end frame must be a compatible intended endpoint, not the next unrelated shot. Split long dialogue and multi-location beats into coverage; do not ask one generation to invent a whole scene. Keep exact Spanish dialogue, titles, signage and plot-critical phone/email text in controlled postproduction. Inspect faces/hands/props across the whole returned clip. On quota, network or generation interruption, pause for the author; do not auto-retry or switch providers.

No new video, independent approval, author approval, or completed episode is claimed by this pass.
