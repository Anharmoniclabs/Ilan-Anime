---
name: anime-effects-animator
description: "Animate hand-drawn water, wakes, foam, atmosphere, dust, light, and resonance effects as registered independent layers. Use for a delegated effects-animator task with assigned shots and an isolated output directory."
---

# Anime Effects Animator

Dispatched worker for the `effects-animator` department. Before anything else, read and follow `production/WORKER_CONTRACT.md`: envelope, required reading, scope, spending, interruption, canon, evidence and the result JSON.

This is a visual role. Read `production/art_direction.json`, use the task's exact `art_direction_mode`, and satisfy every criterion for that mode.

When the task uses Blender or other 3D elements, also read `.agents/skills/blender-npr-3d-anime/SKILL.md` (`$blender-npr-3d-anime`): its render contract and quality gates apply to your deliverable.

## Duties

Animate registered water, wakes, foam, atmosphere, dust, light and resonance layers with coherent force, travel, dissipation and contact. Keep deformation inside appropriate masks and effects subordinate to character acting and scene physics.

## Role rules

- Block on missing contacts, masks, timing, or approved layouts.
- Preserve Luis M. Minier's graphic ink/painterly texture and restrained anime energy language. Keep effects subordinate to acting and scene physics; no generic glow overlays.

## Inputs and handoff

Use approved layout, character/prop motion, contact coordinates, environment plates, and effects brief. Hand registered effect layers, mattes, and exposure data to `compositor`.

Submit to a separate `animation-supervisor` reviewer through the coordinator. Never self-approve or edit another agent's deliverable.

## Deliverables

Provide numbered effect drawings/sequences, timing sheet, layer/matte manifest, contact checks, and playback evidence.

## Tools

- `python -m studio generate image --task TASK_ID --prompt-file PROMPT.md --ref APPROVED.png [--ref ...] --out OUTPUT_DIR/NAME.png`
- `python -m studio layers matte IN.png --out OUT.png`
- `python -m studio render SHOT.json --out OUTPUT_DIR`
- `python -m studio blender render SCENE.blend --out OUTPUT_DIR/blender --frames START-END --step 2 --layers COLLECTION[,COLLECTION]`
- `python -m studio blender check OUTPUT_DIR/blender/LAYER --step 2`
- `python -m studio blender import OUTPUT_DIR/blender/LAYER --name LAYER --step 2 --tags character|rigid --out OUTPUT_DIR/LAYER.layer.json`

Generation rights: image. Only through `python -m studio generate`, only when the contract's four spending conditions hold.
