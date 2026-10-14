# Episode 1 source workspace

[Repository home](../../README.md) · [Repository map](../../docs/REPOSITORY_MAP.md) · [Current status](../../docs/STATUS.md)

This folder holds the episode's script and timing, original recovered artwork, local rendering examples and early experiments. New production drawings, native projects and reviewed motion drafts live under [production/runs/](../../production/runs/).

**The full episode remains unfinished.** Use the [episode review browser](../../production/runs/episode1-full-picture/tasks/episode-wiring/index.html) for selected motion and the [new shot index](../../production/runs/episode1-anime90s-scenes/shot-index.json) for the 128 representative stills. The original 77 numbered keyframes covered 64 shot IDs; that historical inventory is separate from the newer still pass.

## Script, timing and assets

| Location | What it is |
|---|---|
| [data/EPISODE_SCRIPT.md](data/EPISODE_SCRIPT.md) | Current script, visual/sound bible and action requirements |
| [data/episode.json](data/episode.json) · [data/exposure_sheet.csv](data/exposure_sheet.csv) | 128 body shots, 27,120 contiguous frames, 18:50 at 24 fps |
| [data/dialogue.json](data/dialogue.json) | Dialogue worklist; no completed voice production implied |
| [data/shots/](data/shots/) · [data/animatic_overrides.json](data/animatic_overrides.json) | Runnable animatic specs and overrides; held keyframes, camera moves and missing-art slates are timing references |
| [data/art_inventory.json](data/art_inventory.json) | Recovered image-name/provenance mapping |
| [assets/keyframes/](assets/keyframes/) | Original numbered artwork and candidates |
| [assets/bg/](assets/bg/) · [assets/cels/](assets/cels/) | Clean plates and transparent cutouts from earlier tests |
| [assets/replacement_cels/](assets/replacement_cels/README.md) | Unapproved replacement-pose experiments requiring registration and review |
| [assets/references/](assets/references/) · [assets/recovered_2026_10_12/](assets/recovered_2026_10_12/) · [assets/rejected/](assets/rejected/) | Preserved references, recovered sources and rejected images |
| [assets/audio/](assets/audio/) | Temporary/loop audio material |
| [motion/](motion/) · [qa/](qa/) | Motion specs and registration/QA evidence |
| [minimax/](minimax/) · [renders/minimax/](renders/minimax/) | Earlier service handoff instructions and imported takes |
| [renders/STATUS.md](renders/STATUS.md) | Classification of retained renders |

Output is **16:9 at 24 fps** per the author's correction; the historical script's 4:3 text remains as provenance. The separately planned 1:30 ending does not yet have detailed exposure sheets. Original shot numbers and durations remain binding.

## Run the local compositor

Install the root requirements using Python 3.10+ and put FFmpeg/ffprobe on PATH. From this directory:

```bash
python -m pip install -r requirements.txt
python src/validate.py
python src/compose.py data/bell_rig_example.json --out renders/Bell_from_exposure_sheet.mp4
```

[compose.py](src/compose.py) delegates to the repository's `studio.engine`. The bell example demonstrates layer transforms; its successful export does not establish production-quality action. See the [engine guide](../../docs/ENGINE.md) for the JSON schema and [runtime guide](../../docs/STUDIO_RUNTIME.md) for root-level render, layer, motion, sound and QA commands.

Shot source paths are relative to this episode directory. Use registered full-canvas RGBA drawings or explicitly positioned cutouts, back-to-front layer order, and integer exposure intervals with an inclusive start and exclusive end. Keep original drawings and native projects beside their manifests. The [Craft workbench](../../docs/CRAFT_WORKBENCH.md) documents the editable drawing-to-composition-to-edit handoff.

`python src/validate.py --final` is expected to fail while the episode's animation and dialogue are incomplete. Structural validation alone cannot approve acting or continuity.

## Retained rejected experiments

The author rejected the first mesh tests for warping and inadequate acting. They are preserved for reproducibility:

| File | What it demonstrates / why it is retained |
|---|---|
| [Cemi_SC0_Current_Turns_motion_test.mp4](renders/Cemi_SC0_Current_Turns_motion_test.mp4) | 24-second S01-11/S01-12 test: distorted bodies/props, sliding canoes and inadequate paddle action |
| [Bell_motion_test.mp4](renders/Bell_motion_test.mp4) | Five-second cutout/mesh bell test with an incorrect rigid clapper |
| [src/cel_renderer.py](src/cel_renderer.py) | Deterministic source for reproducing these rejected tests |
| [Frame audit](../../research/animation_audit/REPORT.md) | Decoded-frame evidence and failure analysis |

For comparison only, `python src/cel_renderer.py --shot current --width 1280` and `--shot bell --width 1280` reproduce the old tests and write their render outputs. They are not the current production baseline. Temporary synthesized sound in those tests is not a final mix.

## Where current production continues

Use [STATUS.md](../../docs/STATUS.md) for blockers and [the run directory](../../docs/REPOSITORY_MAP.md#production-run-directory) to find preserved iterations. Current work needs controlled contact-matched action drawings, valid seated layouts, independent review and the remaining shot animation. The [latest action checkpoint](../../production/runs/episode1-action-completion-20261014/checkpoints/progress.json) records the rejected/blocked writing, paddle and Amaia attempts.

The production sequence remains script/timing → layout and model checks → plates and registered layers → key/breakdown drawings → cleanup and painted cels → explicit exposures and effects → compositing → dialogue/sound → editorial and exact-file review. Detailed stage dependencies live in the [shot pipeline guide](../../docs/SHOT_PIPELINE.md); production acceptance lives in the [studio standard](../../docs/STUDIO_STANDARD.md).

Original story and art direction: Luis M. Minier. Inclusion of a source image or experiment does not establish completed animation or canonical continuity.
