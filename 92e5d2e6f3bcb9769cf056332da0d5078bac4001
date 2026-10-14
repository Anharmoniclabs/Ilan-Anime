# Arthouse production guide — Heralds of the Cemí

This is a working production pack, not a finished episode. All new designs and staging remain exploratory. The author is Luis M. Minier. Operate from the Ilan-Anime repository with its existing `.venv/bin/python -m studio` tools; save native projects and receipts under the assigned task output, with a fresh take name for revisions.

## What this pack commissions

The written department supplies a full 128-shot Episode 1 screenplay companion, detailed 15-shot BEFORE shooting script, machine-readable storyboard beats, full-cast character bible and cast inventory. The visual department supplies the separate exploratory S01 board book, Amaia/Dairon model sheets and layered digital character setup. The coordinator packages actual delivered assets and identifies partial work. A written character entry is not a delivered model sheet; a storyboard panel is not a cel sequence; a puppet setup is not final character animation.

Episode body: 27,120 frames, 18:50. S01: 3,024 frames, 2:06, absolute range [216,3240). ED is separately planned at 2,160 frames / 1:30. Output is 1280×720, 16:9, 24 fps. Frame intervals are zero-based with exclusive end frames. Shots retain S01-01 through S01-15 even when inserts require multiple panels.

## Working day: script to editable shot

1. **Script supervisor and director:** compare `storyboard-beats.json` to episode.json before drawing. Lock existing durations, cast geography, prop handling and exact supplied dialogue. Resolve final exposure questions in `CONTINUITY_DECISIONS.md`; keep unresolved proposals labeled. Read the Fountain companion as source adaptation, not as final recording copy where source VO remains paraphrased.
2. **Layout and boards:** draw readable 16:9 compositions from the shot beats, with editorial shot ID/timecode/action caption outside each image. Plan the river axis and three-canoe spacing before close-ups. For S01-11 Beheto is in the second canoe, never transplanted into the lead hull. Draw the board's moment; do not fill a board with every moment of the shot.
3. **PhotoCraft:** develop sketches, clean ink, paint flats/shadow planes, and preserve full-canvas separate character/background/FX layers. Save a native document and export transparent full-canvas PNGs. A PNG sheet must be split and registered before it can be an exposure sequence. Existing rejected mesh tests are for diagnosis only.
4. **VectorCraft:** build clean reusable sigil paths, typography, layout geometry and rigid prop guides. Save editable vectors as well as rendered exports. A vector puppet is useful for controls and replacement posing; do not replace the series’ hand-inked character finish with generic glossy geometry.
5. **LightCraft:** review source exposure/color and reference grading without destructive edits to originals. Keep neutral skin color reference apart from BEFORE’s blue-black lighting. Preserve the source snapshot and save adjustments as a separate development project. Never let a global tint change the character’s pigment.
6. **Pose/registration department:** produce actual contact and recovery drawings. Use existing `studio layers register` and `studio motion check` workflows with stable skull, wrist, drum, hull and paddle landmarks. Inspect mattes on light and dark backgrounds; no water scraps may remain attached to hull cutouts. Require new drawings where anatomy or grip geometry changes.
7. **EffectCraft:** compose independently usable backgrounds, characters, rigid objects and FX, saving a native composition. For a simple ordered cel track plus optional static background, `studio craft cels` accepts an explicit exposure manifest. Complex moving layers/cameras require the multilayer studio spec or custom EffectCraft recipe. Every exposure count is integer; sum equals shot duration before export.
8. **FilmCraft:** import reviewed preview or image sequence into a matching 24 fps edit, preserve exact shot boundaries, save native timeline and relinkable media. An animatic may establish timing while drawings are incomplete, but must carry an animatic status. Sound is a separate handoff: `craft cels` does not supply voices, foley or a mix.
9. **DesignCraft and PdfCraft:** lay out editable board/model books with source/status captions, then inspect exported PDF page count, crops, text and image placement. Do not crop hands, shoes, critical props or model views merely to fit a page. Production labels belong in layout, not generated scene art.
10. **Independent review and author:** submit artifacts with hashes and source/inspection evidence. Separate technical validity, visible creative quality and author approval. The coordinator alone records ledger state. Canonical identity/asset promotion requires both independent technical review and Luis’s approval of the exact file digest.

## Executable handoff shapes

Consult `docs/CRAFT_WORKBENCH.md` for the live command contract. Discover schemas rather than guessing engine tool arguments:

```bash
.venv/bin/python -m studio craft doctor --out ASSIGNED_OUTPUT/doctor-take-01
.venv/bin/python -m studio craft tools photocraft --query layer --out ASSIGNED_OUTPUT/photo-schema-01
.venv/bin/python -m studio craft run ASSIGNED_OUTPUT/recipe.json --out ASSIGNED_OUTPUT/native-take-01
```

`ASSIGNED_OUTPUT` is a documentation placeholder for the dispatched worker’s actual directory. A recipe contains ordered `{app, tool, arguments}` steps. Use `${ROOT}` and `${OUT}` expansion as documented. Save native files explicitly before the engine process exits. Engine receipts prove executed calls and exported files; they do not approve the art.

The following is a **shape example**, not an authorized final timing solution for S01-11:

```json
{
  "shot": "S01-11",
  "width": 1280,
  "height": 720,
  "fps": 24,
  "background": "background.png",
  "exposures": [
    {"path": "contact.png", "frames": 2},
    {"path": "weight.png", "frames": 2}
  ]
}
```

Four frames above do not satisfy the 240-frame shot. Build the complete approved exposure list first, with no automatic stretching. `studio craft cels` then snapshots/hashes the drawings and saves `shot.ecproj`, PNG frames, `preview.mp4`, `edit.filmcraft` and `studio-shot.json`. Keep the whole folder together: projects reference media, and moves require relinking. The manifest supports one ordered cel track; retain complex layer movement in the multilayer compositor.

## Puppet handoff contract

A usable digital character setup includes visible layered artwork, neutral view and working pivot/anchor map, named parts, draw order, full-canvas PNG exports, and an editable native/vector source. Required controls are head/body root, hand contacts, eye/brow/mouth replacements and separate hair/cloth. Register drawings to the same origin. Record which motions were actually exercised and viewed. Do not claim completed turnarounds from mirroring an asymmetric outfit, or walking/paddling from sliding an intact cutout.

S01 contact requirements: son remains supported against Amaia; Yara encloses the wrapped cemí; Beheto’s palms stay on rigid drum skin through weight transfer; Dairon’s two hands grip one rigid paddle; bell clapper swings independently. Hulls, faces and fingers do not warp with water. Substantial action uses replacement drawings. Root, foam and wake FX travel separately and respond to the scripted current turn.

## Sound and editorial locks

Extract the supplied dialogue as written; do not fill manuscript-only VO summaries with invented narration. Record original performers or authorized synthetic voices without real-person imitation. Disclose AI voices in credits when used. This pack contains no recordings. Preserve the one sample-identical 8.000-second loop: 192 frames, 384,000 samples at 48 kHz. Train/steamer A4 and scripted pitch sag are explicit cues. BEFORE’s bell is dry brass, the drum note low skin-and-wood with no explosive attack. Commercial music titles in the source are references, not licensed delivery music.

Record spoken duration against the locked shot before lip-sync. Preserve breaths and silence. If a line does not fit, propose an author-reviewed dialogue/edit change rather than accelerating a performance. S01-15’s bridge to S03 must account for intervening S02 title. ED’s final black needs the duration decision logged separately.

## Review gates and known limits

- **Continuity:** exact frame total, cast/prop arrangement, no unapproved year or identity reveal; screenplay quotations checked against source.
- **Design:** missing original pencil portraits prevent canonical likeness approval. Existing archival sheets remain exploratory. Review facial landmarks, costume seams, scale, pigment and expression consistency.
- **Layout:** composition/action path and river axis legible; no incidental cropping. Boards can pass as boards while motion is absent.
- **Animation:** registered drawings, stable props/contact, meaningful weight/arc/secondary motion; watch complete real-time playback plus first/contact/last and intermediate frames. Successful decoding is insufficient.
- **Compositing:** alpha edges, occlusion, water seams, rigid layer separation, correct scene light and PRESS state where needed. Camera pans are not acting.
- **Sound/edit:** exact dialogue performances, intelligibility, sample-identical loop, shot length and sync, source/licensing records. Do not mark missing voices complete.
- **Delivery:** native project reopens with media, PNG/MP4/PDF inspected, receipts and digest recorded, technical reviewer independent, exact author approval before canonical promotion.

Read `docs/STATUS.md`, `research/animation_audit/REPORT.md`, `production/art_direction.json` and `production/WORKER_CONTRACT.md` with this guide. No dependencies, downloads, paid generation or external jobs are required by the writing pack. Interrupted or uncertain engine results are checkpointed and stopped for coordinator recovery; no automatic retries or provider changes.
