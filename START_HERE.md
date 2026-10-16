# Ilan-Anime: start here

This repository contains the Episode 1 production tools, script, art, motion drafts and historical evidence. The full episode is not finished. Use the [searchable episode navigator](production/navigation/index.html) to find each shot's script, selected still, motion file, editable project and review. Open the HTML directly in a browser; no server or account is required.

## Daily use

Run these commands from this folder:

```bash
.venv/bin/python -m studio navigate --probe
.venv/bin/python -m studio workspace
```

The first command rebuilds the navigator and its machine-readable `production/navigation/inventory.json`. It checks source hashes and counts frames in linked motion files. The second opens the native desktop workspace for inspecting scenes and rendering individual drafts. See [workspace instructions](docs/WORKSPACE.md).

Search the navigator by shot ID (`S01-03`), character, action or file state. `present` means bytes exist and match a recorded digest when one was supplied. `hash_mismatch` means the current bytes differ from the indexed version: an old approval does not apply. `unassigned` means no file was linked; `missing` means a linked file is absent. An LFS pointer is a reference to unavailable bytes, not a usable video. File checks never prove artistic quality.

## Folder ownership

| Folder | Put / find here | How to navigate |
|---|---|---|
| `projects/cemi_episode_01/` | Full script timing, shot JSON, project assets and renders | `data/episode.json` defines shot order; `data/shots/` has editable scene specs |
| `episode-01/` | Approved cel workflow, drawings, renderer and versioned takes | Begin with `WORKFLOW.md`; keep the approved baseline intact |
| `production/runs/<run>/` | Task sources, prompts, editable projects, results, reviews | Follow each run's ledger and shot index; reviews refer to exact versions |
| `production/navigation/` | Regenerable cross-folder navigation and file audit | `index.html` for people; `inventory.json` for tools |
| `production/episode-automation-v1/` | Existing persistent video draft queue | `episode.json` records the current stop and pending review |
| `studio/` | Active application and rendering code | `.venv/bin/python -m studio --help` |
| `tests/` | Software regression checks | Test failures do not by themselves indicate bad animation |
| `docs/` | Engine, workflow and setup manuals | [Documentation index](docs/README.md), [detailed repository map](docs/REPOSITORY_MAP.md) |
| `research/` | Reference provenance and rejected experiments | Historical context, not current approval |
| `archive/`, `backups/` | Preserved older workspaces and recovery evidence | Do not use historical paths as the active workspace |

Keep new work under a descriptive run and task, with new take directories. Avoid moving existing media casually: native projects, manifests and reviews contain path references. The navigator organizes access without relocating those dependencies. Existing staged cleanup and local recovered files must be assessed before committing them wholesale.

## Completing a shot and the episode

1. Read the shot script and current scene references; follow the approved cel workflow. The approved opening is 4:3, while the later full-episode data explicitly requests 16:9. Preserve both records and resolve framing for new production before changing the baseline.
2. Create the required successive drawings, clean plates and separate props. A representative still does not cover acting or action.
3. Register cels, set explicit exposures and independent camera movement, render a new take, and inspect contacts, anatomy, occlusion and continuity through the whole shot.
4. Obtain technical review of that exact output; retain repair notes and original editable sources. Update the owning motion index when a replacement has been reviewed, then rebuild the navigator.
5. Produce the scripted dialogue, lip sync, ambience, effects and music. Verify timing and mix before assembly.
6. Assemble contiguous verified shots with exact frame counts, inspect cuts and the full soundtrack, and submit the exact delivery for author review. Do not fill gaps with panned stills or repeated footage.

The existing alternate video coordinator is documented in [episode automation](docs/EPISODE_AUTOMATION.md). Inspect `studio episode status` before any run. It currently has a recovered video awaiting review; restarting blindly can duplicate work. This is separate from the approved cel renderer, not an automatic replacement for it. Paid generation is disabled in `production/policy.json`; no spending or provider change is implied by a render command.

## Git and recovery

This checkout ignores new PNG/JPEG artwork and several native project formats. This delivery explicitly includes the 128 selected shot stills and recovered videos, but does not include all local art. Check `git status --short --ignored`, artifact sizes and selected asset manifests before preparing another asset release. Preserve local originals and historical hashes. Never describe reconstructed media as the original reviewed bytes.

Current delivery evidence is in [the handoff](docs/HANDOFF_2026-10-15.md). Git commits, successful remote pushes, technical checks and final episode approval are separate milestones.
