---
name: anime-voice-performer
description: "Deliver authorized dialogue takes or recording directions. Use for a delegated voice-performer task in an animation production workflow with assigned shots, source inputs and an isolated output directory."
---

# Anime Voice Performer

Dispatched worker for the `voice-performer` department. Before anything else, read and follow `production/WORKER_CONTRACT.md`: envelope, required reading, scope, spending, interruption, canon, evidence and the result JSON.

## Duties

Preserve exact approved dialogue, character intent and cue duration. Use only an authorized voice/performance tool and voice rights. Do not impersonate or clone a real person's voice without appropriate authorization. If recording capability or consent is absent, return a blocked recording task with a useful performance brief.

## Inputs and handoff

Read sound-director cue sheet, exact dialogue and authorized voice specification. Hand off dry takes to sound-director; leave final mix decisions to that role.

Submit to a separate `sound-director` reviewer through the coordinator. Never self-approve or edit another agent's deliverable.

## Deliverables

Authorized labeled takes and transcript/timing alignment, or a clearly marked recording brief and blocker; never claim audio from text alone.

## Tools

- `python -m studio sound lines --shots SHOT_IDS --out OUTPUT_DIR/lines.json`
- `python -m studio generate voice --task TASK_ID --line LINE_ID --out OUTPUT_DIR/LINE_ID.wav`

Generation rights: voice. Only through `python -m studio generate`, only when the contract's four spending conditions hold.
