# Heralds of the Cemí — local cel-animation workshop

> **Status update:** the author rejected the first motion tests for warping and inadequate acting. This original workflow description is retained, but its positive motion-proof language is superseded by [the audit](../../research/animation_audit/REPORT.md) and [current status](../../docs/STATUS.md). Replacement cel experiments are unapproved.

This is an executable animation workflow built around Luis M. Minier's episode script and existing artwork. It uses Python, Pillow, NumPy and FFmpeg. Rendering needs no video-generation service, account or credits.

**Delivered:** a 24-second motion test for S01-11 → S01-12, a five-second bell test, the renderer, a general layer compositor, reusable transparent cutouts, two clean background plates, 77 existing keyframes, the complete script, and exposure sheets for all 128 shots.

**Production status:** this is a working animation project and motion proof, not the finished episode. Existing keyframes cover 64 of 128 shots. None of the full episode's shots have completed acting, voice and continuity review. The current tests demonstrate moving subjects; they do not replace all the drawings required by the script.

## Watch first

- `renders/Cemi_SC0_Current_Turns_motion_test.mp4`: 24 seconds, 1280×720, 24 fps. Beheto leans into the drum; three independent canoe layers travel through the water; body regions move within the canoes; water and foam have separate timing. Original synthesized temporary sound effects are included.
- `renders/Bell_motion_test.mp4`: five seconds. A cutout bell swings around its upper suspension while the pole and hand remain fixed. The torch has a localized flicker deformation.

These renders keep the camera fixed, making it possible to distinguish subject motion from camera movement. The drum uses localized mesh deformation; the canoes and bell use actual transparent cutout layers. No voices have been generated or recorded.

## Run

Install Python 3.10 or later and FFmpeg. From this folder:

```bash
python -m pip install -r requirements.txt
python src/cel_renderer.py --shot current --width 1280
python src/cel_renderer.py --shot bell --width 1280
python src/validate.py
```

The same source renders a smaller working copy with `--width 640`. Width must be divisible by 16. The default export is 16:9 because the user explicitly requested that format; the attached script originally specifies 4:3.

The general compositor accepts shot-specific replacement drawings and transform keys:

```bash
python src/compose.py data/bell_rig_example.json --out renders/Bell_from_exposure_sheet.mp4
```

`data/shots/` contains a separate JSON file for every scripted shot. Most currently contain only a reference image. Those are marked `unrigged_reference`, and they require explicit `--draft` to export. A reference hold must not be relabeled as completed animation.

## The production workflow

| Stage | Concrete work | Output | Completion check |
|---|---|---|---|
| Script and timing | Preserve shot numbers, action, duration, sound and POV. Split inserts inside their parent shot. | `episode.json`, exposure sheet | 27,120 contiguous body frames; no omitted actions |
| Layout | Check each existing keyframe against the written action, character model and surrounding shots. | Approved layout per shot | Correct cast, staging, props, lighting and camera |
| Background repair | Remove only objects that must move. Reconstruct areas they reveal. Keep foreground occluders separate. | Clean plate plus foreground PNGs | Moving layers expose painted scenery, never duplicate bodies |
| Character separation | Cut torso, head, hair, eyes, mouth, near/far arms, hands, props and clothing into RGBA layers. Extend hidden joint overlap. | Registered character layers | No gaps at elbows, wrists, neck or shoulders |
| Key poses | Draw anticipation, contact, action, overshoot and settle. Generate missing poses against the original model reference, then align and review. | Numbered replacement PNGs | Action reads in silhouettes before adding effects |
| Breakdown drawings | Add deliberate intermediate poses where a mesh would distort anatomy. Use replacement drawings for turns, occlusions and large actions. | Cel banks and exposure assignments | No rubber limbs, sliding grip or face drift |
| Timing | Expose ordinary acting on 3s; showcase action on 2s; use 1s for explicitly scripted impacts. Hold selected drawings intentionally. | Per-layer exposure sheets | Each layer has its own rate; output stays at 24 fps |
| Dialogue | Record exact lines within shot duration. Mark syllable accents and pauses. Assign closed, narrow and open mouth drawings; refine consonants and expression. | Voice WAVs and mouth exposures | Lips stop at pauses; expression matches delivery |
| Effects | Draw small repeatable banks for steam, ribbons, water, shock rings, train light and cloth. Reuse identical sigil geometry. | RGBA effect cels | Effects follow the script rather than adding spectacle |
| Camera and composite | BG → far cels → near cels → effects → foreground → camera. Keep camera timing separate from held drawings. | Shot MP4s | No exposed canvas edges or accidental layer crossings |
| Sound | Place dialogue, local ambience, effects and original music. Reuse the exact eight-second mono loop. | 48 kHz shot mixes | Dialogue intelligible; correct loop duration and channels |
| Editorial | Assemble the exact shot sequence, then the 90-second ending. Add captions from recorded lines. | Review master | Full story, exact cuts, no unfinished reference holds |
| Final review | Inspect moving footage, beginning/middle/end frames, casts, prop contact, names, dialogue and audio peaks. | Final master and source archive | All shots reviewed; no missing art or recordings |

This is a practical digital implementation of the timing and layered drawing approach specified in the user's script. It is not a claim that a flattened painting contains unseen poses. Large gestures and turns still need new drawings.

## General compositor format

All source paths are relative to this project folder. PNGs should be full-canvas RGBA for easy registration, or smaller cutouts with explicit placement. Layers are listed from back to front.

```json
{
  "id": "example",
  "size": [1280, 720],
  "frames": 144,
  "status": "animation_ready",
  "layers": [
    {"name": "bg", "source": "assets/bg/painted.png", "fit_canvas": true, "rate": 1},
    {
      "name": "body",
      "sequence": ["assets/cels/body_01.png", "assets/cels/body_02.png"],
      "loop": false,
      "rate": 3,
      "keys": [
        {"frame": 0, "x": 0, "y": 0, "ease": "smooth"},
        {"frame": 72, "x": 8, "y": 3}
      ]
    },
    {
      "name": "mouth",
      "source": "assets/cels/mouth_closed.png",
      "rate": 3,
      "exposures": [
        {"start": 24, "end": 30, "source": "assets/cels/mouth_open.png"}
      ]
    }
  ],
  "camera": [{"frame": 0, "scale": 1.04}, {"frame": 143, "scale": 1.08}],
  "audio": "assets/audio/recorded_shot_mix.wav"
}
```

The example above documents the schema; its illustration filenames are illustrative. The runnable bell example uses real files included in this archive.

Transform keys support `x`, `y`, `scale`, `angle`, `opacity`; easing supports linear, smooth and hold. `sequence` cycles numbered drawings; `exposures` assign a specific cel to an explicit frame interval. Intervals use an inclusive start and exclusive end. The renderer is deterministic for a given integer frame and unchanged assets.

## Current tests and limits

- Motion proof: S01-11 uses 240 frames and S01-12 uses 336, totaling 576 frames / 24 seconds.
- Ordinary bell movement is held on 3s; the two showcase shots are held on 2s.
- The bell and canoe cutouts are stored under `assets/cels/` for reuse in other compositors.
- Backgrounds were produced with the built-in image tool solely to reconstruct scenery hidden behind moving objects. Animation and sound were rendered locally.
- The camera does not move in these tests. No camera zoom is being counted as character acting.
- The tests use restrained mesh acting. They still need redraws for palm placement, more developed paddle drag/lift, and the scripted close-to-wide camera coverage.
- The supplied S01-12 painting includes additional adults in the following canoes compared with the script's staging. This test preserves the source painting to test motion; the layout needs correction before final production.
- Earlier art also needs the documented bow-POV repair in S01-09, young JC's visible dirty fingernails, and full pipe-to-roof coverage for Chismosa. Those repairs are not silently marked complete.
- No full PRESS, era-transition, crowd acting, lip-sync or final film-post implementation is claimed. The general compositor can host their replacement cels; those assets and shot-specific timing still need production.
- Temporary sound is synthesized water, low skin/wood resonance, and a short inharmonic bell approximation. It is not a finished sound mix or a live recording.

## Full episode tracking

`data/episode.json` is the machine-readable schedule. `data/exposure_sheet.csv` is a spreadsheet-friendly shot list with exact action text. `data/art_inventory.json` maps renamed files to the original generated filenames.

The episode body is 18:50. The ending described in the script adds 1:30, giving 20:20 before any separately added material. The ending does not yet have detailed exposure sheets.

`python src/validate.py --final` deliberately returns a failing status while animation and voices are incomplete. This prevents the current project from being mistaken for a finished episode. It does not require a paid service or external approval.

## Next production order

1. Correct river layout continuity, add true replacement poses, and complete the cold open's remaining actions and voices.
2. Build the ballroom showcase, including the dancers' loss of rhythm, color drain, and lingering light after projector loss.
3. Establish PRESS with the childhood classroom, then apply it to the bodega.
4. Produce the café and library Echo sequences.
5. Finish the dialogue, UI, morning, research and ending shots.
6. Mix recorded dialogue and original music; assemble and review the complete episode.

Original story and supplied artwork direction: Luis M. Minier. Existing keyframes are retained as supplied; their inclusion is not a claim of completed animation or canonical continuity.
