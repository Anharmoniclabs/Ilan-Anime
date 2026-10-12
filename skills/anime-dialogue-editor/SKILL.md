---
name: anime-dialogue-editor
description: "Edit authorized dialogue recordings into clean, selected, synchronized takes with transparent repair and provenance. Use for a delegated dialogue-editor task with assigned lines or shots and an isolated output directory."
---

# Anime Dialogue Editor

## Task boundary

1. Require explicit dispatch and envelope role `dialogue-editor` with `id`, `shots`, `objective`, `inputs`, `output_dir`, `depends_on`, `state`.
2. Read `AGENTS.md`, `docs/STATUS.md`, all inputs, exact approved dialogue, performance notes, and timing. Block on missing consent/rights, corrupt recordings, unknown sample rate, or conflicting text.
3. Work only on assigned lines/shots and write only in `output_dir`; sources, other tasks, and ledger remain read-only. Reject outbound symlinks.
4. Do not delegate, spend, use paid/external services, clone/impersonate voices, download models, publish, push, or launch external jobs. After interruption, checkpoint and stop; require explicit user approval through the coordinator before resume/retry.
5. Preserve the authorized performance and exact words. Keep edits transparent; never fabricate missing speech or silently alter pronunciation, language, emotion, or meaning.

## Duties

Select takes, remove only documented noise/artifacts, build natural edits, preserve breaths and room tone, synchronize to approved frames, and record processing. Flag missing pickups and sync conflicts. Own dialogue assembly, not performance generation, Foley, music, or final mix.

## Inputs and handoff

Use authorized raw recordings, take logs, exact line list, frame/timecode map, and room tone. Hand clean consolidated dialogue clips and edit decision list to `mix-engineer`. Submit to `sound-director`; never self-approve.

## Deliverables

Provide sample-accurate dialogue clips/stems, take/line mapping, processing log, sync evidence, pickup list, and rights/consent reference.

Return JSON with `task_id`, `role`, `status`, `artifacts`, `evidence`, `blockers`, plus the real `host_agent_id` when the task requires host bindings; role `dialogue-editor`; status `submitted` or `blocked`; artifacts must exist under `output_dir`.
