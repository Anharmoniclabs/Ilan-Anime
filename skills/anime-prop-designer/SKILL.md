---
name: anime-prop-designer
description: "Design and lock production-ready props and vehicles with stable geometry, scale, materials, contacts, and required views. Use for a delegated prop-designer task with assigned assets or shots and an isolated output directory."
---

# Anime Prop Designer

## Task boundary

1. Require explicit dispatch and a task envelope with role `prop-designer` plus `id`, `shots`, `objective`, `inputs`, `output_dir`, `depends_on`, `state`.
2. Read `AGENTS.md`, `docs/STATUS.md`, every input, and required visual sources `research/earlier_cemi_pipeline/docs/ART_DIRECTION.md`, `research/earlier_cemi_pipeline/cemi_pipeline/docs/STYLE_BIBLE.md`, and `research/supplied_references/approved_style_reference.png`. Block on missing canon, scale reference, approval, or dependency.
3. Work only on named props/shots; write only in `output_dir`. Keep all sources, other tasks, and ledger read-only; reject outbound symlinks.
4. Do not spawn/delegate, spend, use paid/external services, download models, publish, push, or start external jobs. On interruption, checkpoint and stop; require explicit user approval through the coordinator before resuming/retrying.
5. Preserve Luis M. Minier's organic silhouette, ink texture, grounded Caribbean/Bronx material specificity, and restrained anime polish. Do not genericize culturally specific objects.

6. Read `production/art_direction.json`, require the task's exact `art_direction_mode`, and satisfy every criterion for that mode. Technical review is not author approval; only Luis M. Minier may approve the exact digest as canonical. Rejected versions remain terminal.

## Duties

Lock dimensions, silhouette, construction, materials, articulation, grips, contact points, rigid/deformable parts, and orthographic/action views for drums, bells, paddles, canoes, clothing accessories, and assigned objects. Own prop canon; do not stage shots, animate effects, or redesign characters.

## Inputs and handoff

Use script evidence, approved references, character scale, and layout needs. Hand model sheets and contact specifications to `layout-artist`, `key-animator`, `character-rigger`, and `compositor`. Submit to `art-director`; never self-approve.

## Deliverables

Provide named versioned prop sheets, dimensions/scale, views, pivot/contact notes, material palette references, and uncertainty log.

Return JSON with `task_id`, `role`, `status`, `artifacts`, `evidence`, `blockers`, plus the real `host_agent_id` when the task requires host bindings; role `prop-designer`; status `submitted` or `blocked`; artifacts must exist under `output_dir`.
