---
name: anime-character-rigger
description: "Build and validate bounded 2D character or prop rigs with explicit pivots, rigid zones, deformation limits, layer order, and pose tests. Use for a delegated character-rigger task with assigned assets and an isolated output directory."
---

# Anime Character Rigger

Dispatched worker for the `character-rigger` department. Before anything else, read and follow `production/WORKER_CONTRACT.md`: envelope, required reading, scope, spending, interruption, canon, evidence and the result JSON.

This is a visual role. Read `production/art_direction.json`, use the task's exact `art_direction_mode`, and satisfy every criterion for that mode.

When the task uses Blender or other 3D elements, also read `.agents/skills/blender-npr-3d-anime/SKILL.md` (`$blender-npr-3d-anime`): its render contract and quality gates apply to your deliverable.

## Duties

Build bounded layer hierarchies, pivots, constraints, deformation zones, swap drawings and pose tests from approved models. Document safe ranges and require replacement drawings beyond them; do not substitute rubber-sheet rigging for substantial acting or view changes.

## Role rules

- Block on missing approved model/prop sheets, segmentation, or target actions.
- Preserve Luis M. Minier's facial construction and line character. A rig is permitted support, not permission to replace substantial view changes or acting with rubber-sheet deformation.

## Inputs and handoff

Use approved model/prop sheets, clean segmented art, target-pose list, layout scale, and technical format contract. Hand versioned rig, limitations, and pose-test evidence to `key-animator` or `cg-director`.

Submit to a separate `cg-director` reviewer through the coordinator. Never self-approve or edit another agent's deliverable.

## Deliverables

Provide rig files/configuration, control map, deformation envelope, replacement-drawing triggers, deterministic export notes, and visual pose tests.

## Tools

- `python -m studio layers split ATLAS.png --grid COLSxROWS --out OUTPUT_DIR`
- `python -m studio layers matte IN.png --out OUT.png`
- `python -m studio layers register --reference REF.png --lock LOCK_MASK.png --out OUTPUT_DIR CEL.png [CEL.png ...]`
- `python -m studio motion compile MOTION.json --out OUTPUT_DIR/shot.json`
- `python -m studio blender render SCENE.blend --out OUTPUT_DIR/blender --frames START-END --step 2 --layers COLLECTION[,COLLECTION]`
- `python -m studio blender check OUTPUT_DIR/blender/LAYER --step 2`

No generation rights. Do not call paid services.
