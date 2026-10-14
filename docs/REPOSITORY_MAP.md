# Ilan-Anime repository map

[Home](../README.md) · [Documentation index](README.md) · [Production status](STATUS.md)

Inventory checked against the local checkout on **14 October 2026**, including uncommitted work. The picture-draft implementation and its S01-07 run were being developed during this inventory; check Git status and saved task evidence for subsequent changes. Paths below are relative to the repository root unless stated otherwise. This map covers the working areas and every production run present at that check; individual drawings and frames are indexed by their owning manifests. It does not certify remote upload or creative approval.

## Which source should I use?

| Question | Source of truth / entry point |
|---|---|
| What is the story, action and timing? | [Current script](../projects/cemi_episode_01/data/EPISODE_SCRIPT.md), [episode schedule](../projects/cemi_episode_01/data/episode.json), and subsequent explicit author decisions such as [Amaia's three losses](../production/runs/episode1-full-picture/author-decisions.json) |
| What is the selected artwork for each shot? | [New 1990s shot index](../production/runs/episode1-anime90s-scenes/shot-index.json); `selected-shots/` links to the chosen source revision |
| Which motion clips are in the inspection timeline? | [Explicit clip selection](../production/runs/episode1-full-picture/tasks/episode-wiring/links.json), [timeline](../production/runs/episode1-full-picture/tasks/episode-wiring/timeline.json) and [local browser](../production/runs/episode1-full-picture/tasks/episode-wiring/index.html) |
| Which asset is approved for final use? | Exact version/hash, independent review, author decision and final-use link in the [asset registry](../production/asset-registry.json); see [approval rules](ASSET_PIPELINE.md) |
| What work is blocked? | [Status](STATUS.md), the run's `ledger.json`, task results and reviews; [latest action checkpoint](../production/runs/episode1-action-completion-20261014/checkpoints/progress.json) |
| Where are the earlier art sources? | [Original episode assets](../projects/cemi_episode_01/assets/), [research imports](../research/archive_imports/) and [related workspace archive](../archive/local-production-2026-10-14/) |

A saved ledger state is historical evidence, not proof that a worker process is currently alive. `current`, `selected`, `complete` in a folder name, and `technical-approved` in a draft record do not substitute for the exact author-approval gate.

## Top-level layout

| Path | What it contains / how to use it |
|---|---|
| [README.md](../README.md) | Short entry point and current production summary |
| [AGENTS.md](../AGENTS.md) | Repository instructions for agents; preserve sources, approval boundaries and interruption rules |
| [.agents/skills/](../.agents/skills/) | Coordinator and generated department skills, plus Blender guidance. Department definitions originate in `production/roles.json` |
| [docs/](./) | Maintained guides; [index](README.md) lists every document |
| [projects/cemi_episode_01/](../projects/cemi_episode_01/) | Active episode's script, timing, original asset collections and local rendering examples |
| [production/](../production/) | Runs, task evidence, native sources, browsable packages and production-control code |
| [studio/](../studio/) | Main Python CLI and animation runtime |
| [tests/](../tests/) | Regression tests for the runtime, review gates and integrations |
| [research/](../research/) | Recovered references, original-source provenance and historical experiments |
| [archive/](../archive/) | Preserved related workspaces; separate from the active runtime |
| [backups/](../backups/) | Git-object ZIP recovery volumes; the current set is incomplete |
| [community_arts_npr_scene.py](../community_arts_npr_scene.py) | Standalone Blender community-arts scene builder; a source script, not evidence of a finished shot |
| [requirements.txt](../requirements.txt) | NumPy/Pillow dependencies for the base local renderer |
| [requirements-video.txt](../requirements-video.txt) | Optional HF Space client dependency; no model weights |
| [.gitignore](../.gitignore) | Excludes environments, secrets, model weights, ZIPs by default, selected caches and process logs; explicitly tracked backup ZIPs are exceptions |
| `.git/`, `.venv/`, `.local-setup/` | Local Git metadata, Python environment and setup support. These are not production deliverables; environments/setup are not tracked here |

## Episode source workspace

All paths in this section are under [projects/cemi_episode_01/](../projects/cemi_episode_01/).

| Path | What it is |
|---|---|
| [data/EPISODE_SCRIPT.md](../projects/cemi_episode_01/data/EPISODE_SCRIPT.md) | Current episode script plus visual/sound/FX specifications; historical 4:3 text is overridden by the author's 16:9 direction |
| [data/episode.json](../projects/cemi_episode_01/data/episode.json) | Machine-readable 128-shot body schedule: 27,120 frames at 24 fps |
| [data/exposure_sheet.csv](../projects/cemi_episode_01/data/exposure_sheet.csv) | Spreadsheet-friendly shot timing and action |
| [data/dialogue.json](../projects/cemi_episode_01/data/dialogue.json) | Dialogue worklist; text is not a recorded performance |
| [data/art_inventory.json](../projects/cemi_episode_01/data/art_inventory.json) | Original recovered keyframe names and mappings; newer selected stills have their own production index |
| [data/shots/](../projects/cemi_episode_01/data/shots/) | Original runnable per-shot animatic specs; not the newer motion selection |
| [data/animatic_overrides.json](../projects/cemi_episode_01/data/animatic_overrides.json) | Animatic-specific overrides |
| [data/bell_rig_example.json](../projects/cemi_episode_01/data/bell_rig_example.json) | Runnable layer-transform example using retained source assets |
| [assets/keyframes/](../projects/cemi_episode_01/assets/keyframes/) | Original numbered stills and later candidates. The original recovery covered 64 shots; do not use that number for the newer 128-shot still pass |
| [assets/bg/](../projects/cemi_episode_01/assets/bg/) · [assets/cels/](../projects/cemi_episode_01/assets/cels/) | Clean background plates and extracted transparent cutouts from earlier local tests |
| [assets/audio/](../projects/cemi_episode_01/assets/audio/) | Temporary/generated audio assets and loop material; not a finished episode mix |
| [assets/references/](../projects/cemi_episode_01/assets/references/) · [assets/recovered_2026_10_12/](../projects/cemi_episode_01/assets/recovered_2026_10_12/) | Reference images and separately preserved recovered artwork |
| [assets/replacement_cels/](../projects/cemi_episode_01/assets/replacement_cels/) | Early pose atlases/plate experiments with their own README; not registered final animation |
| [assets/rejected/](../projects/cemi_episode_01/assets/rejected/) | Rejected sources retained for comparison |
| [motion/](../projects/cemi_episode_01/motion/) · [qa/](../projects/cemi_episode_01/qa/) | Motion specification and registration/QA evidence |
| [minimax/](../projects/cemi_episode_01/minimax/) | Earlier per-shot video instructions and manifests |
| [renders/](../projects/cemi_episode_01/renders/) | Rejected mesh-test MP4/WAV files and imported video takes under `minimax/`; see `renders/STATUS.md` |
| [src/compose.py](../projects/cemi_episode_01/src/compose.py) | Compatibility wrapper around `studio.engine` |
| [src/validate.py](../projects/cemi_episode_01/src/validate.py) | Episode structure/completeness validator |
| [src/cel_renderer.py](../projects/cemi_episode_01/src/cel_renderer.py) | Reproducible rejected mesh-rendering experiments |
| [README.md](../projects/cemi_episode_01/README.md) · [requirements.txt](../projects/cemi_episode_01/requirements.txt) | Local usage and dependencies |

## Production shelves and packages

All paths in this section are under [production/](../production/).

| Directory | What it is / where to enter |
|---|---|
| [current/](../production/current/README.md) | Human-readable shortcuts to Amaia's artwork, asset library and puppets, and an earlier opening shot. These point into `cemi-90s-production`, not the full-episode clip selection |
| [runs/](../production/runs/) | Versioned production work, with task outputs, prompts, native files, receipts and reviews; complete run directory below |
| [scene-folders-v1/](../production/scene-folders-v1/) | Original per-shot staging folders: `start/`, `end/`, `references/`, `output/`, prompt/script/settings and missing-art markers |
| [episode-image-pack-v1/](../production/episode-image-pack-v1/index.html) | Earlier portable image browser: 69 starts, 22 ends, 22 complete pairs at packaging time |
| [episode-image-pack-v2/](../production/episode-image-pack-v2/index.html) | Later endpoint package; its [status](../production/episode-image-pack-v2/current-image-status.json) records 32 missing starts, 67 missing ends and 61 pairs. This is a separate endpoint inventory, not the newer selected-still count |
| `episode-image-pack-v1.zip` | Ignored local convenience ZIP. Its preserved split copy is under `archive/local-production-2026-10-14/episode-image-pack-v1.zip.parts/` |
| [picture-drafts/](../production/picture-drafts/) | New drawing-led picture-draft catalog (`catalog.json`); local work in progress, with separate per-shot ledgers |
| [episode-first-pass/](../production/episode-first-pass/) | Earlier opening/ending draft exports and `status.json` |
| [video-library/](../production/video-library/index.html) | Browser of saved local videos with a manifest and `build.py`; includes drafts and experiments, not just selected episode clips |
| [video-jobs/](../production/video-jobs/) · [video-plan.json](../production/video-plan.json) | Saved HF/video bridge job evidence and configuration; no automatic job resubmission |
| [episode-automation-v1/](../production/episode-automation-v1/) | Earlier sequential episode queue state, shot/job records and video links |
| [image-demand/](../production/image-demand/) | Per-shot image request records; related workers have separate `runs/image-*` ledgers |
| [character-completion-episode1/](../production/character-completion-episode1/) | Earlier cast-completion assignments, generation tasks, checkpoint and author-review notes |
| [craft-validation/](../production/craft-validation/) | Engine connection evidence, fixtures, recipe runs and cel-exposure tests; technical validation, not episode footage |
| [comfy/](../production/comfy/) | Optional local ComfyUI client, launcher and sample request |
| [dashboard_assets/](../production/dashboard_assets/) | HTML/JS/CSS for the local production dashboard |
| [examples/](../production/examples/) · [example-task.json](../production/example-task.json) | Example approvals, asset records, task plans and Craft recipe |
| [acceptance/](../production/acceptance/) · [schemas/](../production/schemas/) · [pipeline_templates/](../production/pipeline_templates/) | Review template, JSON schemas and complete-shot stage template |

### Production run directory

Run names identify saved iterations. Review individual task results and exact file hashes before reusing an output. A later run may reuse earlier source files without replacing them.

| Run | Purpose and useful entry points |
|---|---|
| [arthouse-pack-v1](../production/runs/arthouse-pack-v1/) | Screenplay companion, design bible, production guide, boards and native publishing assets. Start at `pack-manifest.json`, `tasks/` and `reviews/` |
| [cemi-90s-production](../production/runs/cemi-90s-production/) | Amaia design/rig iterations, model and expression library, river cast library, modern assets, cast index and early S01-01 native scene. Most `production/current/` shortcuts lead here |
| [episode1-character-generations](../production/runs/episode1-character-generations/) | Earlier age-variant, historical, supporting and ensemble generation assignments; inspect saved ledger/results before reuse |
| [episode1-anime90s-cast](../production/runs/episode1-anime90s-cast/) | New 1990s cast artwork, original prompts, reviews and PDF books. Start at `source-index.json`, `cast-coverage.json` and `COMPLETION.txt` |
| [episode1-anime90s-scenes](../production/runs/episode1-anime90s-scenes/) | Selected representative still for all 128 shots, revisions, prompts and review PDF. Start at `shot-index.json`, `selected-shots/` and `delivery-check.json` |
| [episode1-picture-motion](../production/runs/episode1-picture-motion/) | Full action contracts, water/editorial/graph drafts, revisions and reviews; saved raw Amaia drawings. `tasks/motion-contracts/contracts.json` holds shot requirements; `checkpoints/` preserves recovery evidence |
| [episode1-picture-motion-continuation](../production/runs/episode1-picture-motion-continuation/) | Registration/compositing of saved Amaia drawings; source of the partial S01-03 inspection clip |
| [episode1-full-picture](../production/runs/episode1-full-picture/) | Current offline episode review browser, explicit selected clips, incomplete FilmCraft timeline, author decisions, Amaia breakdowns and coin assets. Start at [episode-wiring](../production/runs/episode1-full-picture/tasks/episode-wiring/README.md) |
| [episode1-native-inserts](../production/runs/episode1-native-inserts/) | Original editable room/filter/coin/blackout insert drafts; later finish run reuses and corrects these sources |
| [episode1-insert-finish](../production/runs/episode1-insert-finish/) | Reviewed finish pass for S03-03, S04-02, S05-13 and S06-03; exact outputs in task delivery records and `reviews/native-inserts/review.json` |
| [episode1-amaia-finish](../production/runs/episode1-amaia-finish/) | S01-03 three-losses revisions and independent rejections. Rejected r2 has not replaced the partial inspection clip |
| [episode1-action-completion-20261014](../production/runs/episode1-action-completion-20261014/) | Saved S01-02 paddle, S01-03 seating and S01-07 writing attempts. `checkpoints/progress.json` records four blocked tasks, two rejections and no newly approved motion shot |
| [image-s01-01-v1](../production/runs/image-s01-01-v1/) | Bounded S01-01 image-demand worker record and output |
| [image-s01-02-v1](../production/runs/image-s01-02-v1/) | Bounded S01-02 image-demand worker record, host bindings and output |
| [picture-draft-s01-07-v1](../production/runs/picture-draft-s01-07-v1/) | New S01-07 specialist picture-draft workflow. `picture-packet.json` binds references, action phases and contact requirements; `handoff-jobs/` and `ledger.json` track staged work. Local work in progress, not a completed shot |
| [pilot-20261012](../production/runs/pilot-20261012/) | Initial production pilot and `HANDOFF.md`; historical starting point |

### Inside a run

| Name, when present | Meaning |
|---|---|
| `ledger.json` | Coordinator-owned task definitions, dependencies, state and approval records |
| `runner_state.json`, `handoffs.json` | Execution checkpoint and host-worker/reviewer bindings; inspect before recovery |
| `*.task.json`, `assignments/` | Task requests and bounded output scopes |
| `tasks/<task>/` | Worker-owned sources and deliverables: drawings, native projects, build scripts, prompts, provenance, renders and `result.json` |
| `reviews/<task>/` | Independent review decisions and supporting evidence |
| `checkpoints/` | Saved progress, omissions, recovery state and inspection exports |
| `native/`, `library/`, `parts/`, `cels/` | Editable sources or separated drawings; retain alongside the native project that references them |
| `frames/`, `thumbs/`, `*-evidence/`, receipts | Render frames, review images and engine-call records. Some are tracked evidence; do not blanket-delete them as caches |
| `.codex/`, process logs/locks | Local runtime output, normally ignored; not final creative deliverables |

## Editable artwork and native project formats

| Format / collection | Application and location |
|---|---|
| `.pcraft`, `.psd` | PhotoCraft layered raster artwork. Amaia sheets/parts and opening scene are in `runs/cemi-90s-production/tasks/`; use [current shortcut guide](../production/current/README.md) |
| `.ecproj` | EffectCraft compositions and puppets. Stored beside each task's source drawings; current selected shot projects are linked from the episode browser |
| `.filmcraft` | FilmCraft shot edits and the full inspection timeline in `runs/episode1-full-picture/tasks/episode-wiring/episode.filmcraft` |
| `.designcraft` | DesignCraft editable cast indexes, production sheets and publishing layouts; see `arthouse-pack-v1` and `cemi-90s-production` task outputs |
| PNG / SVG | Full-canvas drawings, cutouts, references, rigid symbols and vector elements; prompts/manifests distinguish generated sources from derivatives |
| PDF / JPG contact sheets | Review exports and visual indexes; preserve corresponding editable sources |
| MP4 / WAV | Review playback and audio assets. Consult the owning task's review; extension alone says nothing about approval |
| JSON / CSV / Fountain / Markdown | Machine-readable timing, manifests, contracts, review records, screenplay and editable documentation |

Many native files embed absolute media paths. `production/current/` also contains absolute symlinks to this checkout. Opening those files on another machine may require relinking. Use their actual task directories as the portable source location and preserve relative directory structure. The [episode wiring guide](../production/runs/episode1-full-picture/tasks/episode-wiring/README.md) documents rebuilding native references after moving the checkout.

## Runtime and production-control code

| Path | Responsibility |
|---|---|
| [studio/__main__.py](../studio/__main__.py) · [cli.py](../studio/cli.py) · [__init__.py](../studio/__init__.py) | Package/CLI entry points |
| [studio/paths.py](../studio/paths.py) · [scan.py](../studio/scan.py) | Repository paths and inventory/status scanning |
| [studio/runner.py](../studio/runner.py) | Codex worker/reviewer execution and persisted runner state |
| [studio/animatic.py](../studio/animatic.py) · [render.py](../studio/render.py) | Timing previews, shot rendering, queue checkpoints and assembly |
| [studio/engine/](../studio/engine/) | `compositor.py`: layered frame evaluation; `fx.py`: procedural FX; `post.py`: finishing; `io.py`: image/video I/O; `__init__.py`: package exports |
| [studio/layers.py](../studio/layers.py) · [motion.py](../studio/motion.py) | Layer separation/registration and motion/contact specifications |
| [studio/sound.py](../studio/sound.py) · [qa.py](../studio/qa.py) | Dialogue/mouth/mix tools and automated technical review flags |
| [studio/craft.py](../studio/craft.py) | Seven Craft engine adapters, recipes, receipts and drawing-to-native-shot export |
| [studio/blender.py](../studio/blender.py) · [blender_npr_setup.py](../studio/blender_npr_setup.py) | Blender render/import/check integration and in-Blender NPR setup |
| [studio/demand.py](../studio/demand.py) · [reference_lock.py](../studio/reference_lock.py) | On-demand image tasks and exact reference binding |
| [studio/picture.py](../studio/picture.py) | New specialist picture-draft catalog and per-shot handoffs; local implementation work in progress, separate from final-release gates |
| [studio/episode.py](../studio/episode.py) · [video.py](../studio/video.py) | Sequential episode draft orchestration and HF video bridge |
| [studio/generate.py](../studio/generate.py) · [policy.py](../studio/policy.py) | Explicitly gated provider calls, cost policy and receipts |
| [production/runtime.py](../production/runtime.py) | Persistent task ledger and validated state transitions |
| [production/host_handoff.py](../production/host_handoff.py) | Bind ledger aliases to real host workers and reviewers |
| [production/asset_registry.py](../production/asset_registry.py) · [asset-registry.json](../production/asset-registry.json) | Hash-chained asset events, immutable versions and approval/final-use state |
| [production/pipeline.py](../production/pipeline.py) | Shot-stage dependency planning |
| [production/roles.json](../production/roles.json) · [build_skills.py](../production/build_skills.py) | Department definitions and generated role skills; edit definitions, not generated boilerplate |
| [production/art_direction.json](../production/art_direction.json) · [validate_art_direction.py](../production/validate_art_direction.py) | Machine-readable art contract and its checks |
| [production/policy.json](../production/policy.json) | Spending controls; only Luis edits this file |
| [production/art-recovery-2026-10-12.json](../production/art-recovery-2026-10-12.json) | Dated recovery inventory backing the art-recovery document |
| [production/dashboard.py](../production/dashboard.py) | Read-only local status server |
| [production/studio_validate.py](../production/studio_validate.py) | Studio architecture/configuration validation, separate from episode completion |
| [tests/](../tests/) | `test_studio*` covers runtime/Craft/Blender/video; other files cover ledgers, asset gates, art contracts, pipeline, host handoffs, dashboard, ComfyUI, reference locks, image demand and episode automation |

External local dependencies are not bundled: Craft CLI applications, Blender, FFmpeg, Codex and the sibling Nessa transport. See [Craft setup](CRAFT_WORKBENCH.md), [runtime](STUDIO_RUNTIME.md) and [hybrid setup](LOCAL_HYBRID_PRODUCTION.md). A saved validation report describes that test run, not a permanent guarantee that a local tool is installed.

## Research, archives and recovery

| Path | Contents and boundary |
|---|---|
| [research/HISTORY.md](../research/HISTORY.md) | Chronology of original art direction, training proposals, recovery and rejected tests |
| [research/PROVENANCE.json](../research/PROVENANCE.json) | Imported source origins and hashes |
| [research/supplied_references/](../research/supplied_references/) | Supplied style reference, pasted script source and 13 October anime correction |
| [research/animation_audit/](../research/animation_audit/) | Report and decoded-frame sheets explaining rejection of the mesh footage |
| [research/earlier_cemi_pipeline/](../research/earlier_cemi_pipeline/) | Recovered earlier SDXL planning code, character bible, cast/style configuration and art direction; not the active `studio/` runtime |
| [research/archive_imports/river_2026_10_11/](../research/archive_imports/river_2026_10_11/) | Earlier river character sheets, plates, keyframes and a different 90-second proposal |
| [research/archive_imports/training_2026_10_08/](../research/archive_imports/training_2026_10_08/) | Training-pack proposal and preparation examples; not trained weights |
| [archive/local-production-2026-10-14/AnimeMotion/](../archive/local-production-2026-10-14/AnimeMotion/) | Preserved tools, episode-01, river-opening, cel-demo and workspace sources from the related project |
| [archive/local-production-2026-10-14/HeraldsOfTheCemi/](../archive/local-production-2026-10-14/HeraldsOfTheCemi/) | Preserved manuscript/book-production, canon, art, editable models, dataset, training pack, scripts, shots, sources, delivery and production records |
| [archive/local-production-2026-10-14/Artcraft/](../archive/local-production-2026-10-14/Artcraft/) | Preserved installer source; installed application binaries are external |
| [archive/local-production-2026-10-14/manifest.json](../archive/local-production-2026-10-14/manifest.json) | Snapshot file hashes, sizes, symlinks and exclusions |
| [archive/local-production-2026-10-14/episode-image-pack-v1.zip.parts/](../archive/local-production-2026-10-14/episode-image-pack-v1.zip.parts/) | Ordered pieces of the original image-pack ZIP; reconstruct using the archive README and verify its recorded hash |
| [backups/2026-10-14/](../backups/2026-10-14/README.md) | Git-object recovery set for saved commit `a01870d4b0609adb9236d2e9262eac3b23b720dd`. Manifest says `complete: false`: 5 of 299 expected ZIP volumes are present. It cannot currently restore the complete saved project |

The archived workspaces are historical copies, not instructions to work in sibling repositories. Their documents may describe older casts, providers, approval states or absolute paths. Current author corrections and the active episode script take precedence.

## Keeping the map useful

Keep new work in a named run/task directory and add an entry above. Use the owning shot/cast manifest to index individual images; keep revisions and reviews alongside their sources. Update the selected-shot index or explicit motion links only through the documented review workflow. Do not move native media or remove old evidence merely to shorten the tree.

For an exact current tracked-file list, run `git ls-files`. For local work not yet committed, run `git status --short`; for ignored runtime/cache files, run `git status --short --ignored`. These answer different questions from a curated map. Recheck manifests when counts change, and keep local presence, committed state and remote delivery distinct.
