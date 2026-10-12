# Studio runtime: running production with Codex

Everything runs through one command: `python -m studio`. Python 3.10+, NumPy, Pillow and FFmpeg are required (`pip install -r requirements.txt`). The agent runner also needs the [Codex CLI](https://learn.chatgpt.com/docs/non-interactive-mode) signed in.

## The production loop

```bash
python -m studio status                                    # what exists, what's paused, what's spent
python -m studio plan production/examples/s01_11_12_pipeline.json   # 27 tasks into ledger run s01-11-12-production
python -m studio run --run s01-11-12-production --dry-run  # what would start
python -m studio run --run s01-11-12-production --max-tasks 4
```

For each ready task the runner:

1. dispatches it in the ledger and writes a checkpoint;
2. starts a **worker**: `codex exec --json --sandbox workspace-write --output-schema … "$anime-<role> …"`. The Codex `thread_id` is recorded as the real host agent id;
3. submits the worker's result (artifacts must be real files in the task's output dir);
4. starts a separate **reviewer** session with the reviewer role from `roles.json`. It inspects the artifacts, runs `studio qa` for renders and returns approve/reject with evidence;
5. records the review. A rejection becomes a revision task (`<id>-r1`, `-r2`) carrying the repair notes; past `max_revisions_per_task` the run pauses for you. An approved revision stands in for the rejected task, so downstream work continues and reads the revision's output;
6. stops at author gates. You record decisions yourself:

```bash
python -m studio approve --run s01-11-12-production s01-11-12-script-timing \
  --decision approve --evidence "Watched the timing table; 24 s, characters on 3s" --i-am-luis
```

If a session fails or the runner is interrupted, the run pauses. Look at the task's output dir, then resume deliberately:

```bash
python production/runtime.py --run s01-11-12-production resume --approval 'APPROVE RESUME s01-11-12-production'
```

## Turning on paid generation

`production/policy.json` ships with generation **off** and caps at **$0**. To enable it:

1. set `generation.enabled` to `true`;
2. set `max_total_usd` and `max_per_task_usd`;
3. fill `image.estimated_usd_per_image` and `voice.estimated_usd_per_1k_chars` from OpenAI's current price page (the runner refuses to spend without them);
4. for voices, map confirmed speakers to built-in voices in `voice.cast` (e.g. `"JC": {"voice": "cedar", "instructions": "25, Bronx, dry humor"}`);
5. export `OPENAI_API_KEY` in the shell that runs `python -m studio run`.

New pipeline tasks for roles with generation rights then get `max_cost_usd` = your per-task cap, and their Codex sessions get network access. Every call is logged to `production/spend_log.jsonl` *before* it is sent. Image requests are reference-image edits: identity comes from the approved drawings attached to each call, and the art-direction rules are prepended to every prompt. Outputs are `exploratory` with a provenance sidecar.

## Picture

| Command | What it does |
|---|---|
| `studio animatic` | Builds runnable specs for all 128 shots (`projects/cemi_episode_01/data/shots/`) and renders the full 18:50 animatic with burn-in. Keyframes are held under the scripted camera move; shots with no art get a slate; title cards, sigil, strobe, lanes, PRESS and era grades come from the FX tokens. |
| `studio render SHOT.json --out x.mp4\|x.mkv\|dir/` | One shot: tagged BT.709 review MP4, lossless FFV1 master, or PNGs. Unready specs need `--draft`. Writes a manifest hashing the spec, every input and the output. |
| `studio queue --out DIR [--shots …]` | Batch render with checkpoints: unchanged shots are skipped; failures are recorded, not retried. |
| `studio assemble --src DIR --out DIR [--audio mix.wav]` | Concatenates shot masters in episode order and verifies 27,120 frames. |
| `studio qa SHOT.json --out DIR [--motion M.json] [--render file]` | Flags boil, locked-region drift, broken contacts, matte halos, freezes and wrong length, with timecodes, a flagged-frame sheet and revision task stubs for the owning role. |

The engine spec format is in [ENGINE.md](ENGINE.md).

## Drawings

| Command | What it does |
|---|---|
| `studio layers split ATLAS --grid 4x2 --out DIR` | Cuts a pose atlas into equal cells. |
| `studio layers matte IN --out OUT [--choke 1]` | Decontaminates edge colors, snaps alpha, reports fringe. |
| `studio layers register CELS… --reference REF --box x,y,w,h --scales 0.97,1,1.03 --out DIR` | Aligns drawings on a locked region (hull, drum, skull). Reports `needs_redraw` when the locked object itself was drawn differently. On the existing Beheto atlas, 2 of 7 poses align and 5 need redraws. |
| `studio motion check M.json` / `compile M.json --out shot.json` | Validates and compiles a motion spec: replacement drawings on the exposure grid, rigid props, parents (passengers ride the hull), FX cycles, contact locks measured on every frame. Scaling or rotating a character drawing is an error. |

## 3D in Blender (NPR)

Rules live in the `$blender-npr-3d-anime` skill (`.agents/skills/blender-npr-3d-anime/SKILL.md`); the cg-director, rigger, effects, layout, background, prop, compositor, supervisor and QA roles are pointed at it. Use 3D for what drawings keep getting wrong: rigid props (hulls, drum, paddles, bell and a separate clapper), multiplane/perspective blocking, camera moves over sets, crowd banks and water effects. Characters only after Luis settles the character-style question.

| Command | What it does |
|---|---|
| `studio blender render SCENE.blend --out DIR --frames 0-239 --step 2 --layers hull,drum,beheto` | Runs Blender headless with `studio/blender_npr_setup.py`: EEVEE, Standard view, 24 fps, canvas size, motion blur off, transparent film, Z + Cryptomatte passes, Stepped modifiers on animated objects (not the camera or objects with `npr_smooth`), and one PNG layer per collection with every other collection held out. Writes `blender_render.json` listing what was applied and what this Blender version lacks. Needs Blender 4.2+ on PATH or `BLENDER_BIN`. |
| `studio blender check DIR/LAYER --step 2` | Fails when the picture changes off the step grid, the "moving on 1s = looks 3D" failure. |
| `studio blender import DIR/LAYER --name hull --step 2 --tags rigid --out hull.layer.json` | Turns the sequence into an engine layer; identical frames collapse into holds. Layers are `screen_space` when Blender owned the camera (`--camera engine` otherwise); never let both cameras move. `studio qa` flags imported layers that change off their drawing rate. |

### Reference-locked 2D to Blender

The no-paid-service `reference-lock` workflow treats a supplied JPG/PNG as
canonical artwork. By default it copies and hashes the source and builds one
approved backplate; it does not infer hidden geometry. Install the existing
requirements, then run from the repository root:

```bash
python -m studio reference-lock init --image /path/to/storefront.png --out /path/to/storefront-scene --camera orthographic
python -m studio reference-lock validate /path/to/storefront-scene/manifest.json
python -m studio reference-lock blender-script /path/to/storefront-scene/manifest.json --out /path/to/storefront-scene/reference_lock.py
blender -b --python /path/to/storefront-scene/reference_lock.py
```

The final command saves an editable `reference_lock.blend` next to the script.
`--camera perspective` selects a calibrated perspective camera; optional
`--width W --height H` must preserve the source aspect ratio. The default
`camera_locked` result is visually faithful only from that fixed reference
camera and is not full 3D reconstruction.

For a 2.5D parallax shot, author and register separate same-size layer images
and masks (for example, distinct foreground, window, reflection, and rain
passes), copy them under the output `assets/` directory, add their relative
paths, SHA-256 digests, unique ascending back-to-front depths, parallax values,
mode, and approval state to `manifest.json`. Change `workflow` to `2.5d` and
the camera to `{"mode": "perspective", "locked": false}`; validate again and
generate the Blender script. Use `sha256sum assets/layer.png assets/mask.png`
to record asset digests; every mask must match its image dimensions. Depth
cards are explicit image planes only.
`mesh` layers require a user-authored `.blend` asset and object name (`mesh`,
`mesh_sha256`, `mesh_object`); no geometry is inferred from the reference.
Before approval, compare a source-camera render against the original at source
dimensions. A single view cannot supply exact hidden sides or arbitrary new
angles; those require authored meshes. New or generated assets remain
exploratory until technical review and Luis's approval of the exact file.

## Sound

| Command | What it does |
|---|---|
| `studio sound lines --out projects/cemi_episode_01/data/dialogue.json` | The voice worklist: 85 quoted lines with shot, timing ceiling and a speaker guess. Speakers stay `speaker_inferred` until the script supervisor confirms them; TTS refuses unconfirmed lines. |
| `studio sound mouth TAKE.wav --rate 3 --out mouth.json` | Closed/narrow/open mouth exposures from a recorded take; lips close on pauses. |
| `studio sound mix MIX.json --out mix.wav` | Places stems at frame offsets with gain/pan, normalizes loudness, reports LUFS and true peak. |

## What this does not do

It can't make a drawing good. It keeps references attached, keeps rigid props rigid, measures drift and contacts, and routes every result through an independent reviewer and then you. Music for the diegetic cues (1957 ballroom, 1973 records, merengue) has to be composed or licensed; the API doesn't write it.
