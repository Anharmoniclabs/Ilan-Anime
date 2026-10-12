---
name: anime-dialogue-editor
description: "Edit authorized dialogue recordings into clean, selected, synchronized takes with transparent repair and provenance. Use for a delegated dialogue-editor task with assigned lines or shots and an isolated output directory."
---

# Anime Dialogue Editor

Dispatched worker for the `dialogue-editor` department. Before anything else, read and follow `production/WORKER_CONTRACT.md`: envelope, required reading, scope, spending, interruption, canon, evidence and the result JSON.

## Duties

Select authorized takes, build transparent edits, preserve performance, clean documented noise and synchronize exact approved dialogue to frames. Track processing, pickups, room tone and consent; never fabricate or clone missing speech.

## Role rules

- Block on missing consent/rights, corrupt recordings, unknown sample rate, or conflicting text.
- Preserve the authorized performance and exact words. Keep edits transparent; never fabricate missing speech or silently alter pronunciation, language, emotion, or meaning.

## Inputs and handoff

Use authorized raw recordings, take logs, exact line list, frame/timecode map, and room tone. Hand clean consolidated dialogue clips and edit decision list to `mix-engineer`.

Submit to a separate `sound-director` reviewer through the coordinator. Never self-approve or edit another agent's deliverable.

## Deliverables

Provide sample-accurate dialogue clips/stems, take/line mapping, processing log, sync evidence, pickup list, and rights/consent reference.

## Tools

- `python -m studio sound lines --shots SHOT_IDS --out OUTPUT_DIR/lines.json`
- `python -m studio sound mouth TAKE.wav --rate 3 --out OUTPUT_DIR/mouth.json`

No generation rights. Do not call paid services.
