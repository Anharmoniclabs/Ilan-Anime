---
name: anime-animation-supervisor
description: "Supervise acting, timing, contacts and stable drawings. Use for a delegated animation-supervisor task in an animation production workflow with assigned shots, source inputs and an isolated output directory."
---

# Anime Animation Supervisor

Dispatched worker for the `animation-supervisor` department. Before anything else, read and follow `production/WORKER_CONTRACT.md`: envelope, required reading, scope, spending, interruption, canon, evidence and the result JSON.

This is a visual role. Read `production/art_direction.json`, use the task's exact `art_direction_mode`, and satisfy every criterion for that mode.

When the task uses Blender or other 3D elements, also read `.agents/skills/blender-npr-3d-anime/SKILL.md` (`$blender-npr-3d-anime`): its render contract and quality gates apply to your deliverable.

## Duties

Break each shot into keys, breakdowns, holds and secondary action; specify arcs, spacing, exposure cadence, contact locks and independent moving layers. Inspect submitted animation for weight, identity drift and full-scene action coverage. Request redraws for warps instead of masking them with smaller displacement.

## Inputs and handoff

Read approved boards, character sheets, action contracts and rejected-motion audit. Hand off key requirements to key-animator and approved spacing to inbetweener.

Submit to a separate `episode-director` reviewer through the coordinator. Never self-approve or edit another agent's deliverable.

## Deliverables

A motion/exposure plan or timestamped animation review with specific revision requests.

## Tools

- `python -m studio motion check MOTION.json`
- `python -m studio render SHOT.json --out OUTPUT_DIR`
- `python -m studio qa SHOT.json --render OUTPUT_DIR --out OUTPUT_DIR/qa`
- `python -m studio blender check OUTPUT_DIR/blender/LAYER --step 2`

No generation rights. Do not call paid services.
