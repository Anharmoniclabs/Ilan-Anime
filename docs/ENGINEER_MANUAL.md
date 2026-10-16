# Heralds of the Cemí — Engineer Manual

Full-repo explainer for engineers: what the project is, how the code works, where every kind of file lives, how to run and extend it, and which folders are source versus derived. Written 15 October 2026. For day-to-day status see [STATUS.md](STATUS.md); for the file-by-file inventory see [REPOSITORY_MAP.md](REPOSITORY_MAP.md).

## Contents

1. [The project](#1-the-project)
2. [What lives in git vs. the drive](#2-what-lives-in-git-vs-the-drive)
3. [Repository layout](#3-repository-layout)
4. [Setup and testing](#4-setup-and-testing)
5. [Architecture](#5-architecture)
6. [Code guide](#6-code-guide)
7. [Data formats](#7-data-formats)
8. [The approved animation workflow](#8-the-approved-animation-workflow)
9. [Production control: ledger, roles, gates, assets](#9-production-control-ledger-roles-gates-assets)
10. [Why media is duplicated and how it was deduplicated](#10-why-media-is-duplicated-and-how-it-was-deduplicated)
11. [Command cookbook](#11-command-cookbook)
12. [Status and known gaps](#12-status-and-known-gaps)
13. [Rules to respect](#13-rules-to-respect)
14. [Drawing engine](#14-drawing-engine)

---

## 1. The project

**Heralds of the Cemí** is a hand-drawn-look, 1990s vintage cel-anime episode (about 18:50, 128 shots, 27,120 body frames at 24 fps). The repo holds both the **story and art sources** and the **production software** that plans, renders, reviews and assembles it.

**Story.** A moonless night before the first bell, in a Taíno / Santo Domingo setting. Amaia travels by river with about fourteen others in three dugout canoes: Dairon (lead paddler), Yara (carrying the sacred cemí), Beheto (drummer, whose whistling breath keeps a 2-second tempo) and three children with blue breath-marks. The arc turns on Amaia's exactly three losses (two drowned at the channel, one old man who asked for water). Theme line: "They count. We remember." Period music cues (1957 ballroom, 1973 merengue) and river ambience carry the sound design.

**Episode structure.**

| Block | Shots | Content |
|---|---|---|
| Title | S00-01, S00-02 | Sigil, epigraph |
| Opening river | S01-01 … | Paddle action, canoe fleet, Amaia |
| Body | S02 – S06 and beyond | Development, 5-depth plates, inserts |

The canonical script is [projects/cemi_episode_01/data/EPISODE_SCRIPT.md](../projects/cemi_episode_01/data/EPISODE_SCRIPT.md); the machine schedule is [episode.json](../projects/cemi_episode_01/data/episode.json). Author decisions in later runs (for example the three-losses decision) override older script text.

**Approved reference.** The 35 s opening assembly (5 shots, 840 frames, 1440×1080, silent) was approved on 2026-10-11 and is the motion/style reference for all new work. Its workflow is locked in [episode-01/WORKFLOW.md](../episode-01/WORKFLOW.md).

## 2. What lives in git vs. the drive

| In git (GitHub) | On the drive only (Google Drive + local disk) |
|---|---|
| `studio/` engine and CLI | Images (png/jpg/webp), video, audio |
| `production/*.py`, JSON contracts, roles, schemas | Image packs, scene folders, archives, cel demos |
| `tests/`, `docs/`, `.agents/skills/` | `production/runs/*/tasks/` worker output |
| Script, shot specs, episode schedule (`projects/*/data`) | `episode-01/build/` renders, `approved-workflow-v1/` media |
| `episode-01/*.py` | PDF/PSD/zip, Craft project files |

[.gitignore](../.gitignore) encodes this split. If a media folder is missing locally, restore it from the drive to the same relative path; manifests refer to paths, not to git.

## 3. Repository layout

| Path | Purpose | Source of truth? |
|---|---|---|
| `studio/` | Python package: CLI (`python -m studio`), compositor engine, renderers, QA, sound, generation, Blender/Craft/video bridges | Yes (execution) |
| `studio/engine/` | `compositor.py` (layer compositor), `fx.py` (effects and generators), `post.py` (grade/film transfer), `io.py` (loading/encoding) | Yes |
| `production/` | Ledger runtime, pipeline builder, asset registry, dashboard, workspace, roles/policy/art-direction contracts | Yes (work state) |
| `production/runs/<run>/` | One production run: `ledger.json`, `handoffs.json`, `reviews/`, `checkpoints/`, `tasks/` | Ledger = yes; `tasks/` = evidence |
| `production/schemas/`, `pipeline_templates/`, `examples/` | JSON schemas, the 27-stage pipeline template, documentation examples | Yes / examples only |
| `projects/cemi_episode_01/data/` | Script, `episode.json`, `exposure_sheet.csv`, per-shot `shots/*.json` | Yes (story and timing) |
| `projects/cemi_episode_01/assets/` | Original and recovered art (keyframes, backgrounds, scene references) | Source art (drive) |
| `episode-01/` | Approved cel workflow: `episode.py` renderer, `render_new_scene_preview.py`, `test_episode.py`, `WORKFLOW.md`, builds and approved baseline | Locked baseline |
| `production/scene-folders-v1/`, `episode-image-pack-v1/v2/` | Early per-shot staging and image packs | Historical, derived |
| `production/picture-drafts/`, `craft-*`, `restored-motion-*` | Picture-draft catalog and Craft-engine experiments | Work in progress |
| `research/` | Provenance, history, imports, audits | Historical |
| `archive/local-production-2026-10-14/` | Preserved related workspaces | Backup only |
| `native-character-art-v1/`, `episode1-anime90s-cast/`, `cel-demo/` | Character-art studies, cast sheet, cel experiments | Reference |
| `.agents/skills/` | 30 department skills + Blender NPR skill, generated from `production/roles.json` | Generated; do not hand-edit |
| `docs/` | Maintained guides (this file is the entry point) | Yes |

## 4. Setup and testing

Requirements: Python 3.10+, NumPy and Pillow, FFmpeg (libx264, librsvg). Optional: Blender 4.2+ (3D NPR), Codex CLI signed in (agent runner), Hugging Face video bridge ([requirements-video.txt](../requirements-video.txt)).

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m unittest discover -s tests -v
```

Test modules (all under `tests/`): `test_studio` (compositor, queue), `test_production_runtime` (ledger), `test_pipeline`, `test_asset_registry`, `test_runner_contracts`, `test_dashboard`, `test_episode_automation`, `test_art_direction`, `test_studio_craft`, `test_studio_blender`, `test_studio_video`, `test_studio_validate`, `test_reference_lock`, `test_image_demand`, `test_host_handoff`, `test_picture`, `test_navigate`, `test_workspace`, `test_comfy_local`. The cel workflow has its own `episode-01/test_episode.py`.

## 5. Architecture

```
 script + episode.json ──► shot specs (shots/*.json)
                                  │
 art (drive) ──► registered cels ─┤
                                  ▼
             studio.engine.Compositor  ──►  frames  ──►  FFmpeg  ──►  shot master
                                                                        │
                    studio assemble  ◄───────────────────────────────────┘
                          │
                          ▼
                    episode picture  (+ sound mix, later)

 Control plane (parallel):
   roles.json ─► pipeline.py (27-stage DAG) ─► Ledger (runs/*/ledger.json)
        ─► CodexRunner: worker session ─► artifacts ─► independent reviewer
        ─► technical gate ─► author gate (Luis only) ─► asset registry state
```

Two planes:

- **Render plane**: deterministic. Given a shot spec and its source images, the compositor always produces the same frames. A manifest (`fingerprint`, input hashes, output SHA-256) is written next to each render.
- **Control plane**: ledger-driven. Work is tasks in a hash-chained event log; creators and reviewers must be different agents; the author gate cannot be satisfied by software.

## 6. Code guide

### 6.1 `studio/` (CLI and engine)

| Module | Role |
|---|---|
| `__main__.py`, `cli.py` | `python -m studio <command>`; `cli.py` dispatches all subcommands |
| `paths.py`, `policy.py` | Repo path resolution; spend/generation policy loading |
| `render.py` | Render one shot spec to mp4/mkv/PNG frames; `queue` (checkpointed batch, resumable) and `assemble` (concatenate masters, verify frame count) |
| `animatic.py` | Builds all shot specs from `episode.json` and renders the burn-in timing animatic |
| `engine/compositor.py` | `Compositor(spec, base, quality, scale)`; `draw(frame)` returns a PIL image. Layers have exposures, `rate`, camera keys, `parallax`, `parent`, blend modes and tags |
| `engine/fx.py` | Effects and generators: sigil, tracked text, slate, speed lines, glow, transmitted light, heat shimmer |
| `engine/post.py` | Grades (`present`, `before`, `1934`, `1957`, `1973`, `flashback`, …), grain, weave, halation, vignette, "press" state |
| `engine/io.py` | Image loading and video encoding helpers |
| `layers.py` | `split` atlas into cells, `matte` edge decontamination, `register` alignment on locked regions |
| `motion.py` | Motion spec validation (`check`) and compilation to shot spec (`compile`): exposures, contacts, rigid props |
| `qa.py` | Automated flags: boil, locked-region drift, broken contacts, matte halos, freezes, wrong length |
| `sound.py` | `lines` (dialogue worklist), `mouth` (mouth exposures), `mix` (stem placement, loudness) |
| `generate.py` | Opt-in image/voice generation, gated by policy and budget |
| `runner.py` | `CodexRunner`: dispatches ready tasks to Codex workers and independent reviewers |
| `reference_lock.py` | Binds shots to locked reference images |
| `scan.py`, `navigate.py` | Drawing scan to editable ink strokes + cel fills (reused by `drawing/`); searchable shot navigator and local-media audit |
| `drawing/` | Reference-grounded drawing engine: reconstruct, construct, Qwen-direct, optional FLUX; see [DRAWING_ENGINE.md](DRAWING_ENGINE.md) |
| `episode.py` | Persistent episode draft queue (init, run, status, assemble, recover-clip) |
| `picture.py` | Specialist picture-draft catalog (plan, start, status, handoff) |
| `demand.py` | On-demand image workflow (ensure, need, work, collect, status, video) |
| `video.py` | Hugging Face video bridge (prepare, submit, import, plan, doctor) |
| `craft.py` | Adapters for the seven Craft engines (doctor, tools, run, cels) |
| `blender.py`, `blender_npr_setup.py` | Headless NPR Blender render, step-grid check, import as engine layers |

### 6.2 `production/` (control plane)

| Module | Role |
|---|---|
| `runtime.py` | `Ledger`: single-writer, hash-chained task state (`added → ready → running → submitted → approved/rejected`). Methods `initialize`, `add`, `ready`, `dispatch`, `submit`, `technical_review`, `author_review`; also a CLI (`pause`, `resume`, …) |
| `pipeline.py` | `build_pipeline(spec, template, roles, repo)`: expands a shot spec into the 27-stage task DAG from `pipeline_templates/`. Never generates art or bypasses gates |
| `asset_registry.py` | `AssetRegistry`: append-only hash-chained asset lifecycle (see 9.3) |
| `build_skills.py` | Regenerates `.agents/skills/*/SKILL.md` from `roles.json` |
| `host_handoff.py` | Records real host agent IDs vs. ledger aliases (creator ≠ reviewer proof) |
| `studio_validate.py`, `validate_art_direction.py` | Validation of studio data and the art-direction contract |
| `dashboard.py` | Read-only local status server |
| `workspace.py`, `desktop_workspace.py` | Native desktop scene workspace (`python -m studio workspace`) |
| `craft_finish_20261015.py` | One-off Craft finishing script (dated, not general) |
| `roles.json`, `policy.json`, `art_direction.json` | Contracts (see section 7) |
| `WORKER_CONTRACT.md` | What every worker must return |

### 6.3 `episode-01/` (approved cel renderer)

`episode.py` composites transparent cel layers over painted backgrounds with explicit `[drawing, hold]` exposures and independent camera motion, then encodes with FFmpeg. `render_new_scene_preview.py` previews new scene references. `test_episode.py` guards the workflow. Binding data lives in `episode-01/data/` (render plans, generation prompts).

## 7. Data formats

| File | Key fields |
|---|---|
| `episode.json` | `fps, width, height, body_frames, shots[{id, script, start_frame, frames, keyframes, status, animation_status, voice_status}]` |
| `shots/<ID>.json` | `id, size, frames, status, background, layers[], camera[], shake[], post{}`; layer: `source / sequence / exposures / generator`, `rate`, `keys`, `pivot`, `parallax`, `parent`, `blend`, `effects`, `tags` |
| render manifest | `shot, output, mode, quality, frames, size, fingerprint, inputs, output_sha256, engine, seconds, truth` |
| `runs/<run>/ledger.json` | `version, run, paused, pause_reason, tasks{}, events[]` (events are append-only and hash-chained) |
| `runs/<run>/handoffs.json` | `bindings{task: {creator{ledger_alias, host, host_agent_id, role}, reviewer{…}}}` |
| `asset-registry.json` | Events: `asset_id, version, path, sha256, kind, mode, shots, provenance, continuity, states, technical_approvals, author_approvals, final_use_links` |
| `roles.json` | Per role: `skill, title, description, reviewer, visual, generate[], duties, rules, handoff, deliverables, tools, extra_skills` |
| `policy.json` | `generation{enabled, provider, max_total_usd, max_per_task_usd, image, voice}`, `codex{binary, sandbox, network_for_generation}`, `revisions{…}` |
| `art_direction.json` | `contract_id, version, source_precedence, global_rules, criteria, modes` (CHARACTER_ASSET, ENVIRONMENT_PLATE, STORY_FRAME, EDITORIAL_MOODBOARD) |

## 8. The approved animation workflow

Locked 2026-10-11 ([episode-01/WORKFLOW.md](../episode-01/WORKFLOW.md), [AGENTS.md](../AGENTS.md)):

- 1990s cel look: flat two-tone shading, painted backgrounds, deliberate holds, restrained acting.
- **4:3, 24 fps, working size 1440×1080.** Uniform character scaling; never silently change style, format or method.
- Transparent character/prop cels over backgrounds; sprite sheets are sources only.
- Explicit exposures (for example the approved fleet: 8 drawings, 48-frame cycle, holds 9,3,6,3,6,3,9,9).
- Camera and background move **every frame**, independent of drawing holds; water is its own layer.
- Moonless river light: navy/steel, charcoal shadows, amber rim.

Repeatable steps: (1) read shot script, camera, duration; (2) inspect references and generate backgrounds, poses, in-betweens; (3) reject extra limbs, proportion drift, clipped paddles, opaque backgrounds, registration drift; (4) copy chosen art into versioned assets and save prompts; (5) bind assets and exposures in the render plan; (6) composite; (7) inspect first/middle/last frames and action changes; (8) check frame counts and run tests, assemble only shots that exist; (9) update review page and status honestly.

Never overwrite `approved-workflow-v1/` or `build/take-02`; new takes get new directories. Never pad unfinished shots with still pans or repeated footage.

## 9. Production control: ledger, roles, gates, assets

### 9.1 Roles
Thirty department roles (director, producer, episode-director, script-supervisor, storyboard, layout-artist, character-designer, animation-supervisor, key-animator, inbetweener, cleanup-artist, ink-paint-artist, color-designer, background-painter, prop-designer, character-rigger, effects-animator, compositor, sound-director, sfx-artist, dialogue-editor, mix-engineer, music-composer, quality-review, cg-director, art-director, pipeline-td, asset-manager, voice-performer, editor). Edit `production/roles.json`, then run `python production/build_skills.py`.

### 9.2 Gates
- **Technical gate**: an independent reviewer (different agent and role) approves or rejects with evidence. A rejection creates a revision task (`-r1`, `-r2`) up to the policy limit.
- **Author gate**: only the author may approve (`studio approve … --i-am-luis`), bound to the exact artifact path and SHA-256. A technical approval never substitutes for it.

### 9.3 Asset lifecycle
`exploratory → submitted → technical-approved → author-approved → canonical` (or `rejected`, terminal). Final-use links (`link-final`) are only allowed from approved versions. `asset_registry.py verify --check-files` re-hashes files.

### 9.4 Running a shot through the pipeline
`studio plan SPEC.json --run NAME` → `studio next --run NAME` → `studio run --run NAME [--parallel N]` → gates → `studio assemble`.

## 10. Why media is duplicated and how it was deduplicated

An audit of 18,299 media files found **2,449 groups of byte-identical files, about 5.5 GB wasted**. Causes:

1. **Run-to-run copying (about 3.8 GB).** Every Codex task writes its inputs and outputs under its own `production/runs/<run>/tasks/<task>/`. Continuation runs (`…-continuation`, `…-restore-inserts`, `…-finish`) re-copy the same references and previous drawings so tasks are self-contained.
2. **Parallel staging trees.** `episode-image-pack-v1`, `episode-image-pack-v2`, `scene-folders-v1` and `projects/cemi_episode_01/assets` hold overlapping copies of the same keyframes and scene references.
3. **Archive and import copies.** `archive/local-production-2026-10-14`, `research/archive_imports` and `cel-demo/*` re-store art from earlier workspaces.
4. **Baselines.** `episode-01/approved-workflow-v1` and `episode-01/assets` intentionally mirror approved art.
5. **Zip bundles.** `production/episode-image-pack-v1.zip` duplicates the image-pack folder.

**Action taken (2026-10-15):** every byte-identical copy was replaced by a **hardlink** to one canonical copy (`tools/hardlink_dedupe.py`): 9,129 files, 5.47 GB freed, no path changed, so every manifest still resolves. Python caches were removed, and `.git` shrank from 8 GB to under 600 MB (an aborted media-staging attempt had filled the LFS cache). `tools/dup_report.py` reproduces the audit.

**Caveats.** Hardlinked files share content: editing one in place edits all. Save edits as new files (this is already the repo rule). Hardlinks only work within one filesystem, and Google Drive uploads/restores will recreate full copies — re-run the dedupe script after restoring.

**Policy going forward.** Prefer referencing an asset by path or by registry `asset_id`/SHA-256 instead of copying it into a new task folder; keep one canonical asset and let manifests point to it.

## 11. Command cookbook

```bash
.venv/bin/python -m studio status                         # episode, runs, registry, spend
.venv/bin/python -m studio navigate --probe               # rebuild shot navigator
.venv/bin/python -m studio render SHOT.json --out X.mp4 --draft
.venv/bin/python -m studio animatic --out DIR --scale 0.5
.venv/bin/python -m studio queue --out DIR --mode review --workers 2
.venv/bin/python -m studio assemble --src DIR --out DIR
.venv/bin/python -m studio qa SHOT.json --render X.mp4 --out DIR
.venv/bin/python -m studio motion check M.json
.venv/bin/python -m studio layers register CELS... --reference REF --box x,y,w,h --out DIR
.venv/bin/python -m studio sound mix MIX.json --out mix.wav
.venv/bin/python -m studio plan SPEC.json --run NAME
.venv/bin/python -m studio run --run NAME --parallel 2 [--dry-run]
.venv/bin/python -m studio approve --run NAME TASK --decision approve --evidence "..." --i-am-luis
.venv/bin/python -m studio generate image --run RUN --task TASK --prompt-file P.md --ref A.png --out OUT.png --dry-run
.venv/bin/python -m studio craft doctor
.venv/bin/python -m studio blender render SCENE.blend --out DIR --frames 1-48 --step 2
.venv/bin/python production/dashboard.py                  # read-only status server
.venv/bin/python production/asset_registry.py verify --check-files
```

## 12. Status and known gaps

- Approved animation: only the 35 s opening (S00-01 … S01-03). About 10 shots have technically approved motion drafts; most of the 128 slots are empty.
- Sound is excluded from the current silent picture workflow.
- Blocked: S01-07 writing (pose jumps, matte seams), S01-02 canoes (grip and paddle geometry), S01-03 Amaia (scale/seating, contacts).
- Open author decisions: S01-11/12 timing conflicts (24 s vs 22 s, 2s vs 3s exposure policy, frame mapping), canonical keyframes, original pencil portraits as identity source, spending/provider changes.
- Technical approval is not author approval; nothing here is a finished episode.
- Drawing engine (16 Oct 2026, branch `feature/reference-drawing-engine`): reconstruction, front-view Amaia expressions, Qwen expression planning and a FLUX.2 Klein CPU backend (~23 min/image) exist. Body poses, in-betweens and Craft round-trips of drawing takes are not built yet. See [DRAWING_ENGINE.md §13](DRAWING_ENGINE.md#13-known-gaps-and-next-work).

Always check the newest run `ledger.json` and [STATUS.md](STATUS.md) before trusting this section.

## 13. Rules to respect

- Keep approved references and earlier takes intact; new work gets new filenames and directories.
- Do not substitute another style, format or animation method.
- Do not claim completion for unfinished shots; report progress accurately.
- Respect generation policy and budget (`production/policy.json`); only the author approves final use.
- Do not hand-edit generated files (`.agents/skills`, ledgers, registry); use the tools.
- Absolute paths in `production/current/` links are machine-specific.

## 14. Drawing engine

`studio/drawing/` makes the drawings that animation needs. It has four routes: **reconstruct** approved cels into editable layers (flats, shade, ink, matte) via `scan.py`; **construct** same-view changes such as facial expressions from a per-character identity model; let **Qwen direct** them by choosing only from fixed menus; and optionally **generate** new angles with FLUX.2 Klein through stable-diffusion.cpp. Every feature is tagged `source`, `source-warped`, `procedural` or `model`, and only the author approves art. Run `python -m studio.drawing --help`.

Full engineering and developer manual: [DRAWING_ENGINE.md](DRAWING_ENGINE.md). It covers the architecture decision, build methodology, routes, modules, data formats, commands, measured results, the engineering subagents in `.claude/agents/`, tests and gaps.
