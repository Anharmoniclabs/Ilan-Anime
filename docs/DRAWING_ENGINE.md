# Drawing engine — engineering and developer manual

[Home](../README.md) · [Engineer manual](ENGINEER_MANUAL.md) · [Documentation index](README.md) · [Status](STATUS.md)

Written 16 October 2026 on branch `feature/reference-drawing-engine`. This document explains why the drawing engine exists, the build methodology, every route a drawing can take through it, the code module by module, the data formats, the measured results, and what is still missing. It describes engineering capability. Nothing here is author approval of any artwork.

## Contents

1. [Why this exists](#1-why-this-exists)
2. [Architecture decision](#2-architecture-decision)
3. [Build methodology](#3-build-methodology)
4. [The four drawing routes](#4-the-four-drawing-routes)
5. [Module guide](#5-module-guide)
6. [Data formats](#6-data-formats)
7. [Command reference](#7-command-reference)
8. [Measured results](#8-measured-results)
9. [Provenance and approval](#9-provenance-and-approval)
10. [Engineering team (Claude subagents)](#10-engineering-team-claude-subagents)
11. [Testing](#11-testing)
12. [Extending the engine](#12-extending-the-engine)
13. [Known gaps and next work](#13-known-gaps-and-next-work)

---

## 1. Why this exists

Episode 1 has 128 shots (27,120 frames, 18:50 at 24 fps). Every shot has one selected still. Only the 35-second approved opening (5 shots) has the multiple drawings that animation needs. Real acting needs **new drawings**, not camera moves over stills (forbidden by [AGENTS.md](../AGENTS.md)).

Two experiments defined the problem:

| Experiment | Result | Lesson |
|---|---|---|
| `studio/agent.py paint_new` — Qwen picks 5 numbers for a hardcoded paddle | Integrated, but the paddle looked artificial next to the painted river | Numbers into a template are not drawing |
| `studio/artist.py` — Qwen 1.5B writes raw Bézier coordinates for a portrait | `DRAW-take-001` truncated JSON; `DRAW-take-002` rendered **one brown square** (`SHAPES: 1`) | A 1.5B text model cannot draw. Valid JSON is not art |

## 2. Architecture decision

Four approaches were compared:

| | Approach | Fidelity | Editable | Laptop cost | Verdict |
|---|---|---|---|---|---|
| A | Qwen writes every coordinate | Fails (one square) | Yes | Low | Rejected as an art engine |
| B | Extract geometry, color and ink from approved art | Very high | Yes | Very low | Foundation |
| C | B + model-chosen *bounded* edits + procedural construction | High for same-view changes | Yes | Low | Built |
| D | Learned image model (FLUX.2 Klein) for new views/poses | High, some identity drift | No (flat raster) | ~23 min/image on CPU | Optional backend, key poses only |

**Chosen: B + C, with D as an optional plug-in.** Rule of thumb:

- If the drawing already exists → **reconstruct** it (route 1).
- If it's the same view with a changed expression → **construct** it procedurally (route 2), directed by Qwen (route 3).
- If it's a new angle or pose that no source shows → **generate** it with FLUX (route 4), then reconstruct the result into layers.

Qwen is the assistant director. It chooses from menus and never emits geometry.

## 3. Build methodology

1. **Audit before building.** Every subsystem first checks for existing code. `studio/scan.py` already did ink and fill extraction; `studio/layers.py` already split atlases. Both are reused, not rewritten.
2. **Vertical slices.** Each milestone runs real approved art end to end and stops for review: paddle reconstruction → Amaia expressions V1/V2/V3 → Qwen direction → S01-01 recovery → FLUX benchmark.
3. **Measure, then look.** Every take gets numbers (color error, edge F1, timing, RAM) **and** a contact sheet inspected by eye. When they disagree, the eye wins and the failure is written down. For example, V1 faces passed validation but showed identity drift, so V1 was rejected.
4. **New take directory per run.** Nothing overwrites a source or an earlier take. Each take has a `take.json` with source digests, authorship and `approved: false`.
5. **Bounded models.** One Ollama model at a time, strict schemas, bounded retries, receipts, no repair of truncated output.
6. **Honest labels.** Every feature in a result is tagged `source`, `source-warped`, `procedural` or `model`.

## 4. The four drawing routes

```
                      approved art (digest-locked)
                                 │
      ┌──────────────────────────┼──────────────────────────────┐
      ▼                          ▼                              ▼
 ROUTE 1 reconstruct      identity model (landmarks,     ROUTE 4 FLUX generate
 reference.extract        palette) per character+view    flux.generate (-r ref)
      │                          │                              │ flat raster,
      │                  ROUTE 2 construct                       │ model-generated
      │                  face.construct / face.compose           │
      │                          ▲                              ▼
      │                  ROUTE 3 direct                   back into ROUTE 1
      │                  model.plan_expression            for editable layers
      │                  (Qwen: menu choices only)
      ▼                          ▼
 editable layers:  flats (vector) · shade (multiply) · ink (vector) · matte
      │
      ▼
 review.plausibility gate  →  independent review  →  AUTHOR approves exact digest
      │
      ▼
 existing pipeline: exposure sheet → episode-01/episode.py or studio compositor
 → Craft native projects → FFmpeg → QA
```

### Route 1 — Reconstruct (`reference.py`)

Approved cel → `scan.scan_image` (ink mask, Zhang-Suen thinning, skeleton tracing, RDP simplification; k-means fills in Lab color space, island merge, contour polygons) → four layers:

| Layer | What | Why |
|---|---|---|
| `flats` | vector fill polygons | recolorable cel paint |
| `shade` | grayscale multiply (source ÷ flats, 128 = neutral) | keeps the painted grain that flats can't hold; survives recoloring |
| `ink` | vector variable-width strokes | line weight follows the original ink |
| `matte` | source alpha | the cel edge is the artist's edge |

The vector-only rebuild is measured separately from the layered rebuild, so the editability cost is visible.

### Route 2 — Construct (`face.py`, `render.py`, `schema.py`)

An **identity model** stores one character view's measured landmarks (eye corners, lids, iris centers, brow arcs, mouth corners/lips, chin) and a palette sampled from source pixels. Expressions are bounded parameter sets (`brow_raise`, `brow_inner`, `lid_open`, `gaze_x/y`, `pupil`, `mouth_open`, `mouth_width`, `mouth_corner`). All offsets are measured in units of the character's own interocular distance, so features move together and keep her proportions.

`face.compose` builds one face:

1. `erase_features`: inpaints the original brows, eyes and mouth (OpenCV Navier-Stokes), kept inside the face so hair isn't smeared, then restores skin grain from a clean cheek patch.
2. Brows and closed lips: **source-warped**. The artist's own pixels are bent along the new curve (`warp_feature`), with alpha keyed on darkness and, for lips, on color difference from skin.
3. Eyes and open mouths: **procedural**. New tapered Bézier ink and clipped fills (lids, lash flick, crease, iris, iris shadow, pupil, highlight, mouth interior, teeth, lower lip).
4. `render.render`: supersampled 4×, Lanczos down, per-primitive clip masks. `render.to_svg` writes the same polygons.

### Route 3 — Direct (`model.py`)

Qwen 2.5 Coder 1.5B reads one action line and returns exactly `{"expression", "intensity", "gaze"}` from fixed menus. `validate_plan` rejects extra keys, unknown names and out-of-range numbers. Bad replies get at most 2 retries, then a loud failure. Each call writes `plan-receipt.json` (prompt, raw replies, seconds per attempt). `plan_to_expression` scales the named expression from neutral by intensity and adds gaze.

### Route 4 — Generate (`flux.py`)

FLUX.2 Klein 4B (Q4 GGUF) runs through the stable-diffusion.cpp CPU binary, conditioned on an approved reference image with `-r`. It's the only route that can make a genuinely new angle. Its output is one flat, `model-generated` raster: run it through route 1 to get layers, then through review. One run at a time (lock file), hard timeout, and no retry. A timeout is recorded as `unknown`.

## 5. Module guide

| File | Lines (approx.) | Responsibility | Depends on |
|---|---|---|---|
| `studio/drawing/__init__.py` | 6 | Package docstring | — |
| `studio/drawing/schema.py` | 140 | Drawing IR + identity validation: dotted lowercase IDs (no spaces, no duplicates), finite bounded coordinates, connected cubic segments, closed fills, width profiles, clip references, provenance enum, resource limits (2,000 primitives, 400 segments each, 40,000 total) | — |
| `studio/drawing/render.py` | 80 | Cubic sampling, tapered stroke outlines, clipped fill rendering, SVG | numpy, Pillow |
| `studio/drawing/reference.py` | 170 | Route 1: extract, build layers, composite, measure (color error, p95, alpha IoU, edge F1 at 2 px), contact sheets | `studio.scan`, OpenCV |
| `studio/drawing/face.py` | 370 | Route 2: expressions, construct, feature mask, erase, warp_feature, compose | schema, render, OpenCV |
| `studio/drawing/model.py` | 120 | Route 3: Ollama chat, plan validation, retries, receipts, intensity scaling | face, Ollama HTTP |
| `studio/drawing/flux.py` | 130 | Route 4: doctor, bounded command builder, locked single run with receipt | sd-cli binary |
| `studio/drawing/review.py` | 50 | Structural gate: occupancy ≥ 2 %, enough regions/colors. Fails the one-square benchmark | OpenCV |
| `studio/drawing/__main__.py` | 120 | CLI | all |

Reused, unchanged: `studio/scan.py` (extraction), `studio/layers.py` (atlas split), `episode-01/episode.py` (approved renderer), `studio/paths.py` (atomic JSON, SHA-256). Preserved, untouched: `studio/agent.py`, `studio/artist.py` (local experimental files; backups in `backups/local-2026-10-16-pre-drawing/`).

## 6. Data formats

**Drawing IR** (`*.drawing.json`):

```json
{"version": 1, "canvas": [1024, 1536], "character": "amaia", "view": "front",
 "expression": {"brow_raise": 0.7, "...": 0},
 "primitives": [
   {"id": "face.eye.l.white", "kind": "fill", "provenance": "procedural", "color": "#e3d7cc",
    "opacity": 1.0, "curve": [[[x,y],[x,y],[x,y],[x,y]], ...]},
   {"id": "face.eye.l.iris", "kind": "fill", "clip": "face.eye.l.white", "...": "..."},
   {"id": "face.eye.l.lash", "kind": "stroke", "width": [5.6, 8.7, 6.2, 2.5], "...": "..."}
 ]}
```

Curves are lists of cubic segments; each segment starts where the previous one ended. A stroke's `width` profile is interpolated along its length (taper). `clip` names an earlier fill.

**Identity model** (`production/engineering/canon/<character>-<view>.identity.json`): `character`, `view`, `canvas`, `source`, `source_sha256`, `status` (`candidate` | `author-approved`), `landmarks` (name → [x, y] in source pixels), `palette` (role → `#rrggbb`), `skin_patch`, `provenance`. The Amaia front model is a **candidate**: its source is an exploratory generated master, and its landmarks were annotated by hand by the engineer.

**Take record** (`production/engineering/drawing-takes/<TAKE>/take.json`): take ID, kind (`reconstruction` | `procedural-new-drawing` | `model-generated` | `recovery`), source digests, output digests, per-feature authorship, inspected evidence, gaps, `status`, `approved: false`.

## 7. Command reference

```bash
# Route 1: approved cel -> editable layers + metrics
.venv/bin/python -m studio.drawing extract episode-01/assets/cels/paddle-sheet.png --out production/engineering/drawing-takes/MY-TAKE

# Route 2: draw expressions from an identity model
.venv/bin/python -m studio.drawing face --identity production/engineering/canon/amaia-front.identity.json \
    --expression neutral fear sorrow --out production/engineering/drawing-takes/MY-FACE-TAKE

# Route 3: Qwen directs the face from a script line (Ollama must be running)
.venv/bin/python -m studio.drawing plan "Amaia turns toward the riverbank in fear" \
    --identity production/engineering/canon/amaia-front.identity.json --out production/engineering/drawing-takes/MY-PLAN

# Route 4: optional FLUX backend (about 23 min per image on the i3 laptop)
.venv/bin/python -m studio.drawing flux --doctor
.venv/bin/python -m studio.drawing flux --reference REF.png --prompt "..." --out production/engineering/drawing-takes/MY-FLUX

# Structural gate (exit 1 on failure)
.venv/bin/python -m studio.drawing gate path/to/preview.png

# Recover an approved opening shot from its preserved recipe
cd episode-01 && ../.venv/bin/python episode.py render --shots S01-01 --output build/take-NN-recovery
```

Every command refuses a non-empty output directory. Note that `episode.py validate` also regenerates `build/take-01/review.html` (observed to be byte-identical).

**Setup:** `opencv-python-headless` is in `requirements.txt` (installed with `uv pip install --python .venv/bin/python opencv-python-headless`; this upgraded numpy 1.26 → 2.4 and the full suite still passed). FLUX files live outside the repo; see the `flux.py` docstring. Override the location with `ILAN_FLUX_ROOT`.

## 8. Measured results

All runs were on the HP 14 laptop: i3-1115G4, 4 threads, 12 GB RAM, Intel UHD graphics, CachyOS.

| Take | Route | Result |
|---|---|---|
| `PADDLE-REF-take-001` | 1 | 8 approved paddle cels, ~0.2 s each. Layered: mean color error 1.5–5.1/255, edge F1 0.96–0.99. Vector-only: 2.8–8.9/255, F1 0.88–0.96. Layered alpha IoU = 1.0 **by construction** (the matte is the source alpha) |
| `AMAIA-FACE-take-001` | 2 | V1, **rejected by the engineer**: generic eyes, flat bar brows, wrong iris color, lost lips, erase smudges |
| `AMAIA-FACE-take-002` | 2 | V2: source-warped brows, correct iris color; 6 expressions, ~1.4 s each, peak RSS 0.5 GB |
| `AMAIA-QWEN-take-001/002` | 3 | Qwen valid on the 1st attempt 8/8, ~2 s per line. V3 gaze rule fixed "turns toward" (gaze left) |
| `S01-01-RECOVERY-take-001` | recovery | Approved plan re-rendered: 1440×1080, 24 fps, 144 frames, 33 s. **Byte-identical** to `take-03-restored/S01-01.mp4` |
| `FLUX-BENCH-take-001` | 4 | Genuine three-quarter fear view. Sampling 1,202 s (4 × ~300 s), generation 1,356 s, 83.6 min wall including first load under memory pressure, peak RSS 4.5 GB, no out-of-memory. Identity drift: softer jaw, rounder eyes, hair tie moved |

Images and videos live on the drive, not in git (see [ENGINEER_MANUAL §2](ENGINEER_MANUAL.md#2-what-lives-in-git-vs-the-drive)). The `take.json` records and their digests are what git carries.

## 9. Provenance and approval

| Tag | Meaning | Counts as new drawing? |
|---|---|---|
| `source` | Approved pixels or vectors extracted unchanged | No (reconstruction) |
| `source-warped` | Artist pixels bent along a new curve | No (transformation) |
| `procedural` | New geometry built by engine code | **Yes** |
| `model` / `model-generated` | Chosen or generated by Qwen or FLUX | Qwen: parameters only; FLUX: yes, but a flat raster |

Passing `review.plausibility`, schema validation or tests is **necessary, not sufficient**. Only Luis M. Minier approves art, by exact SHA-256, through the existing [art acceptance](ART_ACCEPTANCE.md) and [asset pipeline](ASSET_PIPELINE.md) gates. Any change to a file invalidates its approval.

## 10. Engineering team (Claude subagents)

`.claude/agents/` defines seven engineering delegates for building the studio. They are separate from the 30 production departments in `.agents/skills/` (unchanged). Each has exclusive file ownership:

| Agent | Owns |
|---|---|
| repo-forensics | `production/engineering/forensics/**` (read-only audits) |
| art-canon | `production/engineering/canon/**` |
| drawing-core | `schema.py`, `validate`, `render.py`, `reference.py` + their tests |
| local-models | `model.py`, `test_drawing_model.py` |
| animation-cels | `pose.py`, `exposure.py` (not yet written) |
| craft-integration | `pipeline.py` (not yet written) |
| independent-qa | `review.py`, regression tests, `production/engineering/qa/**` |

So far the lead engineer wrote all of this code directly; **no subagent has been spawned yet**, so independent QA review of this branch is still outstanding.

## 11. Testing

```bash
.venv/bin/python -m unittest tests.test_drawing_reference tests.test_drawing_engine -v
.venv/bin/python -m unittest discover -s tests      # full suite
```

The 20 drawing tests cover: round-trip layers and metrics; SVG well-formedness and source digest; recoloring keeps grain; the one-square benchmark and the real `DRAW-take-002` preview both **fail** the gate; an approved paddle cel passes; schema rejection of space-in-ID, NaN, unbounded coordinates, bad provenance or color, broken segment chains, open fills, unknown clips, duplicates and resource limits; identity status gate; distinct expressions with fear raising the brows and opening the eyes; bounded expression parameters; plan validation, truncated-JSON retries ending in a failure receipt, recovery on retry, intensity scaling; the FLUX command bounds and its refusal without a backend; `--help` for every CLI command.

Tests check engineering contracts, not art quality.

## 12. Extending the engine

- **New character or view:** create `<character>-<view>.identity.json` from an approved source (landmarks + sampled palette), validate it with `schema.validate_identity`, and keep `status: candidate` until the author approves. A different head angle is a **separate identity model**; never interpolate between views whose topology differs.
- **New expression:** add an entry to `face.EXPRESSIONS` using only the bounded parameters. Qwen picks it up automatically from the menu.
- **New feature type** (hands, hair masses): add a constructor that emits IR primitives with dotted IDs (`hand.r.finger.index.tip`), reuse `render`, and add tests asserting the geometric behavior.
- **New model:** pass `model=` to `plan_expression`. Keep the reply schema closed.

## 13. Known gaps and next work

1. Face: frown creases and under-eye lines are not reconstructed; a faint temple patch remains; front view only.
2. Vector-only extraction turns white water spray into dark ink specks (an `ink_mask` misclassification). Keep water raster until this is fixed.
3. Not built yet: `pose.py` (body poses, correspondences, in-betweens), `exposure.py`, `pipeline.py` (Craft round-trip of drawing takes).
4. FLUX: ~23 min per image on this laptop, so key poses only. Its output needs identity correction and layer extraction. A GPU host (seconds per image) is needed for volume.
5. Coverage: 5 of 128 shots have real animation (the approved opening). The remaining shots need key drawings (FLUX or an artist) before routes 1–3 can animate them.
6. The approved `take-02` media are LFS pointers. Restored real copies are in `episode-01/build/take-03-restored/`, and the approved plans re-render byte-identically.
