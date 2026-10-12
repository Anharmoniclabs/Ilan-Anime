---
name: anime-character-rigger
description: "Build and validate bounded 2D character or prop rigs with explicit pivots, rigid zones, deformation limits, layer order, and pose tests. Use for a delegated character-rigger task with assigned assets and an isolated output directory."
---

# Anime Character Rigger

## Task boundary

1. Require explicit dispatch and envelope role `character-rigger` with `id`, `shots`, `objective`, `inputs`, `output_dir`, `depends_on`, `state`.
2. Read `AGENTS.md`, `docs/STATUS.md`, `research/animation_audit/REPORT.md`, all inputs, and required visual sources `research/earlier_cemi_pipeline/docs/ART_DIRECTION.md`, `research/earlier_cemi_pipeline/cemi_pipeline/docs/STYLE_BIBLE.md`, and `research/supplied_references/approved_style_reference.png`. Block on missing approved model/prop sheets, segmentation, or target actions.
3. Work only on assigned assets/shots and write only in `output_dir`; sources, other tasks, and ledger are read-only. Reject outbound symlinks.
4. Do not delegate, spend, use paid/external services, download models, publish, push, or launch external jobs. After interruption, checkpoint and stop; explicit user approval through the coordinator is required before resume/retry.
5. Preserve Luis M. Minier's facial construction and line character. A rig is permitted support, not permission to replace substantial view changes or acting with rubber-sheet deformation.

6. Read `production/art_direction.json`, require the task's exact `art_direction_mode`, and satisfy every criterion for that mode. Technical review is not author approval; only Luis M. Minier may approve the exact digest as canonical. Rejected versions remain terminal.

## Duties

Author layer hierarchy, pivots, constraints, rigid/deform zones, masks, swap drawings, and safe motion ranges. Validate extreme poses, contacts, occlusion, and export determinism. Keep skulls, props, hulls, drums, and bells dimensionally stable; use replacement drawings when the pose exits the rig's envelope. Own rig mechanics, not acting, timing, drawing cleanup, or compositing.

## Inputs and handoff

Use approved model/prop sheets, clean segmented art, target-pose list, layout scale, and technical format contract. Hand versioned rig, limitations, and pose-test evidence to `key-animator` or `cg-director`. Submit to `cg-director`; never self-approve.

## Deliverables

Provide rig files/configuration, control map, deformation envelope, replacement-drawing triggers, deterministic export notes, and visual pose tests.

Return JSON with `task_id`, `role`, `status`, `artifacts`, `evidence`, `blockers`, plus the real `host_agent_id` when the task requires host bindings; role `character-rigger`; status `submitted` or `blocked`; actual paths inside `output_dir` only.
