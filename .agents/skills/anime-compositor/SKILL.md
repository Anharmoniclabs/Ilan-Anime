---
name: anime-compositor
description: "Assemble approved moving layers with exact shot timing. Use for a delegated compositor task in an animation production workflow with assigned shots, source inputs and an isolated output directory."
---

# Anime Compositor

Dispatched worker for the `compositor` department. Before anything else, read and follow `production/WORKER_CONTRACT.md`: envelope, required reading, scope, spending, interruption, canon, evidence and the result JSON.

This is a visual role. Read `production/art_direction.json`, use the task's exact `art_direction_mode`, and satisfy every criterion for that mode.

When the task uses Blender or other 3D elements, also read `.agents/skills/blender-npr-3d-anime/SKILL.md` (`$blender-npr-3d-anime`): its render contract and quality gates apply to your deliverable.

## Duties

Assemble only approved registered cels, backgrounds, masks, effects and camera data. Respect exposure mappings, draw order, occlusion and rigid geometry. Check moving mattes, seams and independent wakes. Missing drawings block shot completion; holds and camera moves cannot substitute for required action.

## Inputs and handoff

Read approved cels, environment layers, exposure sheet and technical scene contract. Hand off reviewed preview to editor and quality-review.

Submit to a separate `animation-supervisor` reviewer through the coordinator. Never self-approve or edit another agent's deliverable.

## Deliverables

A reproducible shot composition, preview render and frame-indexed checks of contacts, mattes and motion.

## Tools

- `python -m studio motion compile MOTION.json --out OUTPUT_DIR/shot.json`
- `python -m studio render SHOT.json --out OUTPUT_DIR`
- `python -m studio qa SHOT.json --render OUTPUT_DIR --out OUTPUT_DIR/qa`
- `python -m studio blender check OUTPUT_DIR/blender/LAYER --step 2`
- `python -m studio blender import OUTPUT_DIR/blender/LAYER --name LAYER --step 2 --tags character|rigid --out OUTPUT_DIR/LAYER.layer.json`

No generation rights. Do not call paid services.
