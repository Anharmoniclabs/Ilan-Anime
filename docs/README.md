# Documentation index

[Repository home](../README.md) · [Repository map](REPOSITORY_MAP.md) · [Current status](STATUS.md)

Start with the map to locate files, then use the guide for the work you are doing. Status describes saved production evidence; workflow documentation describes capabilities, not completion of the episode.

## Navigation and production decisions

| Document | Purpose |
|---|---|
| [Engineer manual](ENGINEER_MANUAL.md) | Full top-to-bottom guide: story, code, data formats, workflow, duplication audit |
| [Repository map](REPOSITORY_MAP.md) | Paths and responsibilities for assets, code, production runs, archives and backups |
| [Status](STATUS.md) | Current picture coverage, blockers, rejected approaches and dated progress history |
| [Episode workspace](../projects/cemi_episode_01/README.md) | Script/timing sources, original assets and local compositor commands |
| [Production workspace](../production/README.md) | Department roles, ledgers, task boundaries and reviewer handoffs |
| [Current asset shortcuts](../production/current/README.md) | Amaia library and opening-scene shortcuts, original source locations and portability |
| [Research history](../research/HISTORY.md) | Earlier decisions and imports; historical proposals remain historical |
| [Art recovery, 12 October](ART_RECOVERY_2026-10-12.md) | Dated source-recovery inventory; not the latest selected-shot inventory |

## Runtime and making shots

| Guide | Purpose |
|---|---|
| [Studio runtime](STUDIO_RUNTIME.md) | `python -m studio`, workers, rendering, QA, motion, sound and generation controls |
| [Drawing engine](DRAWING_ENGINE.md) | Reconstruct, construct, Qwen-directed and FLUX drawing routes; build methodology, code, commands, measured results |
| [Craft workbench](CRAFT_WORKBENCH.md) | Seven local editing engines, native projects, recipes, receipts and cel exposures |
| [Engine](ENGINE.md) | Shot JSON, layers, compositing, FX and post-processing |
| [Shot pipeline](SHOT_PIPELINE.md) | Stage dependencies from source drawings through final review |
| [Image demand](IMAGE_DEMAND.md) | One-shot image requests, source reuse and independent review |
| [Local hybrid production](LOCAL_HYBRID_PRODUCTION.md) | Local agent, HF video and Blender handoffs and their limits |
| [Episode automation](EPISODE_AUTOMATION.md) | Sequential draft queue, checkpoints and independent motion review |
| [ComfyUI setup](COMFY_LOCAL.md) | Optional local drawing backend, configuration and recovery |
| [Blender NPR skill](../.agents/skills/blender-npr-3d-anime/SKILL.md) | Blender workflow and the 3D-to-2D art contract |

## Review, assets and operations

| Guide | Purpose |
|---|---|
| [Studio standard](STUDIO_STANDARD.md) | Release criteria and the distinction between technical and creative approval |
| [Art acceptance](ART_ACCEPTANCE.md) | Art-direction checks and structured review reports |
| [Asset pipeline](ASSET_PIPELINE.md) | Immutable versions, provenance, approval digests and final-use links |
| [Host handoff](HOST_HANDOFF.md) | Real worker/reviewer identities and interruption recovery |
| [Dashboard](DASHBOARD.md) | Local read-only status UI |
| [Worker contract](../production/WORKER_CONTRACT.md) | Shared scope, tools, deliverables and approval rules |
| [Archive guide](../archive/local-production-2026-10-14/README.md) | Preserved related workspaces and split image-pack ZIP |
| [Backup guide](../backups/2026-10-14/README.md) | Incomplete Git-object volume set, integrity manifest and restore procedure |

## Maintaining these documents

When adding a new production run, add its purpose and entry points to [the map](REPOSITORY_MAP.md). Put coverage changes and exact evidence links in [STATUS.md](STATUS.md), with a date. Keep detailed command contracts in their existing workflow guides and link them from here. Preserve dated reviews and imported documentation; mark superseded statements instead of turning old evidence into new approval.

Before sharing a documentation change, run `git diff --check` and verify relative links against the checkout. Check `git status --short` to distinguish documentation edits from ongoing production work. Local files and commits do not establish remote delivery.
