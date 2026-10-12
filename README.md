# AnimeStudio — Heralds of the Cemí

Animation production workspace for **Luis M. Minier's Heralds of the Cemí**. This repository collects the recovered art direction, research, character references, episode script, generated artwork, local compositing code, experiments, and their review history.

**Status: work in progress. The full episode is not animated. The first mesh-animation tests were rejected by the author for warping and dull movement.** They remain here as documented experiments, not finished footage. New replacement-cel sheets are exploratory and have not yet been registered, composited or approved.

## Start here

| Need | File or directory |
|---|---|
| Current decisions and unfinished work | [Production status](docs/STATUS.md) |
| Full production workflow | [Episode workflow](projects/cemi_episode_01/README.md) |
| Research and decisions from the beginning | [Research history](research/HISTORY.md) |
| Author-derived art direction | [Art direction](research/earlier_cemi_pipeline/docs/ART_DIRECTION.md) |
| Complete episode script and visual/sound bible | [Episode 1: 3:07](projects/cemi_episode_01/data/EPISODE_SCRIPT.md) |
| All 128 shots and exact timing | [Episode JSON](projects/cemi_episode_01/data/episode.json) · [Exposure sheet](projects/cemi_episode_01/data/exposure_sheet.csv) |
| Shot templates | [Per-shot JSON files](projects/cemi_episode_01/data/shots/) |
| 77 numbered keyframes | [Artwork](projects/cemi_episode_01/assets/keyframes/) |
| Earlier character sheets and scene pack | [River asset pack](research/archive_imports/river_2026_10_11/Cemi-River-Scene/) |
| New pose sheets, not production-approved | [Replacement cel experiments](projects/cemi_episode_01/assets/replacement_cels/) |
| Local layer/replacement-cel compositor | [compose.py](projects/cemi_episode_01/src/compose.py) |
| Rejected mesh renderer, for reproduction only | [cel_renderer.py](projects/cemi_episode_01/src/cel_renderer.py) |
| Why the first renders failed | [Frame audit](research/animation_audit/REPORT.md) |
| Earlier SDXL pipeline and character bible | [Recovered source snapshot](research/earlier_cemi_pipeline/) |
| Earlier Qwen/style training proposal | [Training kit](research/archive_imports/training_2026_10_08/cemi_training_pack/) |
| Import origins and hashes | [Provenance](research/PROVENANCE.json) |

## Run the local compositor

Python 3.10+ and FFmpeg are required. The local renderer does not call a video-generation service.

```bash
cd projects/cemi_episode_01
python -m pip install -r requirements.txt
python src/validate.py
python src/compose.py data/bell_rig_example.json --out renders/Bell_from_exposure_sheet.mp4
```

The bell example demonstrates layer transforms; its motion quality is not production-approved. To reproduce the **rejected** tests for comparison only:

```bash
python src/cel_renderer.py --shot current --width 1280
python src/cel_renderer.py --shot bell --width 1280
```

`python src/validate.py --final` must fail while shots and dialogue are unfinished. Technical validation passing does not establish visual quality.

## Current production rules

- Author's original drawings and subsequent explicit corrections define identity and style.
- Preserve the finished hand-inked Cemí look, navy/steel shadows and amber light; lighting must still follow the actual scene. BEFORE is moonless.
- Current output is **16:9 at 24 fps**. The supplied script's original 4:3 specification is retained as historical text, not silently rewritten.
- Ordinary drawings are exposed on 3s; showcase action uses 2s, with isolated 1-frame impacts when scripted.
- Animate actual action with replacement poses and correctly separated rigid layers. Do not use face/body warps, image-wide ripple displacement or a camera move as a substitute for acting.
- Keep the exact shot numbers, durations, narrative actions, cast, prop contact and POV. Inserts stay within their parent shot.
- Unfinished/rejected assets must remain clearly marked. A keyframe is not an animated shot; an atlas is not a registered cel sequence.

## Contents and ownership

The script body is 18:50 / 27,120 frames, with a separately planned 1:30 ending. Existing numbered art covers 64 of 128 body shots, with some shots only partially covered. No voice performances or final episode mix are included. The older 90-second river plan has different staging and is archived as an earlier proposal.

Source-repository and archive imports preserve their original documentation, including proposals that were never implemented. See the history and status documents before following old recommendations. No model weights, trained LoRA, credentials, service tokens, or licensed commercial music are included.

Story and art direction: **Luis M. Minier**. No new license grant is added by this consolidation; original notices remain with imported material.
