# Heralds of the Cemí — episode production

**Workflow approved and locked:** [production rules](WORKFLOW.md). The reproducible reference is preserved in `approved-workflow-v1/`; future production uses new assets and takes.

The first production batch covers **00:00–00:35**, five shots at **1440×1080, 4:3, 24 fps**. It is a silent motion draft, not the completed 18:50 episode.

[Watch the assembled opening](build/take-02/opening-assembly.mp4) · [Review all shots and their status](build/take-02/review.html)

## This batch

- S00-01: a provisional gold sigil draws onto the navy title field.
- S00-02: the Spanish epigraph and English translation dissolve in.
- S01-01: eight transparent paddle drawings play over a separately moving painted water surface.
- S01-02: eight fleet drawings animate a paddle cycle; the fleet travels independently of the camera, with gentle heave. The moonless background is a new version of the supplied river plate. Placement was lowered after the first composite put the rear canoe across the roots.
- S01-03: six Amaia/son drawings provide counting mouth shapes, a blink and a downward glance. The child remains asleep.

The fleet has a 48-frame cycle. Cel holds are explicit; camera positions advance every output frame. This is local cel compositing with supplied/generated drawings. It does not run a local video diffusion model or synthesize new drawings automatically.

## Build and extend

Run commands from this directory. Requires Python 3 and FFmpeg with librsvg and libx264; no Python packages or API keys.

```bash
python episode.py validate
python -m unittest test_episode.py
python episode.py render --shots S01-02 --output build/new-take --width 1440
python episode.py assemble --shots S00-01 S00-02 S01-01 S01-02 S01-03 --output build/take-02
```

`data/shots.source.json` and `data/script.md` are unchanged copies of the Downloads files. `data/shots.json` is the validated working import. Its effect tokens are recovered from the script using balanced parentheses so internal semicolons do not split arguments.

`data/render-plans.json` binds shots to actual assets and animation tracks. Each layer supplies a PNG, a transparent cel sheet with a grid, or a list of full-frame transparent PNGs. Exposures are `[drawing_index, held_frames]`; non-looping tracks must match the shot duration. Use versioned asset filenames when changing drawings. New takes preserve older renders. Existing renders with changed plans or dimensions are rejected.

Coordinates in layer `x` and `y` are fractions of the output frame. Width is a fraction of output width and aspect ratio is preserved. Camera offsets are output pixels. For cel sheets, cells currently use square registration; full-width fleet cels use an explicitly sized canvas with aspect-preserving fitting. `keep_in_frame` checks horizontal placement of protected layers. It does not automatically detect physical collisions with painted scenery: those still need visual review.

Rendering verifies frame count and frame rate, writes first/middle/last snapshots, and records the plan and outstanding limitations. Assembly requires contiguous, actually rendered shots. It will not fill missing shots with stills or reused footage. `review.html` and `status.json` track all 128 shots.

## Still in production

- The remaining 123 shots, including the rest of the river opening.
- Dialogue, ambience, foley and music; current videos contain no audio.
- The five separate depth plates requested for the wide river shot; currently there is a painted background and a fleet layer.
- Disappearing-seat inserts and the exact push-in specified for Amaia's shot.
- Scanned grain plates and the final analog finishing pass.
- Final resolution mastering. The current 1440×1080 files are working renders, not native 4K artwork.

The source script's S01-03 description mentions the old man's wife among disappearing seats, but the manuscript says she was not with them. Keep fourteen departing and eleven remaining; do not add another death. The accepted fleet seats Amaia and her son in the rear canoe, whereas the new script appears to place them in the lead. This draft preserves the accepted asset's seating.

Artwork was generated with the built-in imagegen tool using the supplied character sheets and river background. Exact prompts are saved in [generation-prompts.json](data/generation-prompts.json) and [fleet-generation-prompts.json](data/fleet-generation-prompts.json). All consumed artwork is copied into `assets/`.
