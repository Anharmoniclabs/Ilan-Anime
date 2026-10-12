---
name: anime-sfx-artist
description: "Build synchronized effects, ambience and physical sound cues. Use for a delegated sfx-artist task in an animation production workflow with assigned shots, source inputs and an isolated output directory."
---

# Anime SFX Artist

## Task boundary

1. Read the assigned task envelope before acting: `id`, `role`, `shots`, `objective`, `inputs`, `output_dir`, `depends_on`, `state`. Confirm `role` is `sfx-artist` and the coordinator explicitly dispatched this task. Do not pick additional work.
2. Read repository `AGENTS.md`, `docs/STATUS.md`, and every required source path in `inputs`. Before animation work also read `README.md` and `research/animation_audit/REPORT.md`. Resolve paths from the supplied repository root, not the skill's installation folder. Inspect unapproved or rejected inputs when explicitly assigned for review or planning; retain their status and do not promote them into approved production assets. If a required input is absent or ambiguous, or its approval is a prerequisite to the assigned execution and has not been granted, return blocked with the exact path and required decision.
3. Work only on `shots` and `objective`. Follow any task tool, time or iteration budget; if none is supplied, perform one bounded submission without self-starting revisions. Write only inside `output_dir`; treat all source assets, other tasks and the coordinator ledger as read-only. Do not traverse symlinks outside that directory.
4. Do not spawn or delegate to another agent. Return handoff recommendations to the coordinator. Prompt boundaries are not a filesystem or tool sandbox; obey the host's stronger permissions.
5. Do not invoke Higgsfield. Do not spend money, download models, publish, push Git changes or start external jobs. After an interruption or connection failure, checkpoint if possible and stop; ask the coordinator to obtain user approval before resuming or retrying. A replacement agent must inspect the checkpoint and must not repeat an uncertain external action.
6. Preserve current user corrections over historical research. Keep 16:9, 24 fps and canonical shot timing unless explicitly changed. Distinguish plans, exploratory assets, reviewed submissions and user-approved production material.

## Duties

Create or select authorized effects for contacts, water, wakes, bells, atmosphere and scripted supernatural events. Tie events to frame/sample positions and keep stems separable. Record source/license provenance and label placeholders. Do not add unrequested music or download unapproved packs.

## Inputs and handoff

Read sound cues, frame timing and available authorized audio assets. Hand off stems to sound-director and editor.

Submit to a separate `sound-director` reviewer through the coordinator. Do not self-approve, alter another agent's deliverable, or mark the full episode complete.

## Deliverables

Task-local effects stems or a sound-design specification, cue alignment and source/rights manifest.

Inspect what you actually produced. State which source images, frames, audio or video you directly viewed/listened to and which checks were only automated. Never claim rendered movement from a textual specification, static sheet or successful file decode.

Return the shared result fields shown below. When the task requires host bindings, also include `host_agent_id` with the exact real creator ID supplied by the coordinator; never invent this identity:

```json
{
  "task_id": "the assigned id",
  "role": "sfx-artist",
  "status": "submitted",
  "artifacts": ["repository-relative path inside assigned output_dir"],
  "evidence": ["source path and specific observation or performed check"],
  "blockers": []
}
```

Use `"blocked"` when required inputs, capabilities, approval or dependencies prevent the task. Record each blocker specifically; partial artifacts may still be listed. Use actual existing artifact paths, never illustrative ones. Submission means ready for review, not approved. Keep detailed findings and any resumable checkpoint inside `output_dir`.
