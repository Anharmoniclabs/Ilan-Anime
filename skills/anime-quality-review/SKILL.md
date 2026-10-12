---
name: anime-quality-review
description: "Independently inspect motion, continuity and evidence. Use for a delegated quality-review task in an animation production workflow with assigned shots, source inputs and an isolated output directory."
---

# Anime Quality Reviewer

## Task boundary

1. Read the assigned task envelope before acting: `id`, `role`, `shots`, `objective`, `inputs`, `output_dir`, `depends_on`, `state`. Confirm `role` is `quality-review` and the coordinator explicitly dispatched this task. Do not pick additional work.
2. Read repository `AGENTS.md`, `docs/STATUS.md`, and every required source path in `inputs`. Before animation work also read `README.md` and `research/animation_audit/REPORT.md`. Resolve paths from the supplied repository root, not the skill's installation folder. Inspect unapproved or rejected inputs when explicitly assigned for review or planning; retain their status and do not promote them into approved production assets. If a required input is absent or ambiguous, or its approval is a prerequisite to the assigned execution and has not been granted, return blocked with the exact path and required decision.
3. Work only on `shots` and `objective`. Follow any task tool, time or iteration budget; if none is supplied, perform one bounded submission without self-starting revisions. Write only inside `output_dir`; treat all source assets, other tasks and the coordinator ledger as read-only. Do not traverse symlinks outside that directory.
4. Do not spawn or delegate to another agent. Return handoff recommendations to the coordinator. Prompt boundaries are not a filesystem or tool sandbox; obey the host's stronger permissions.
5. Do not invoke Higgsfield. Do not spend money, download models, publish, push Git changes or start external jobs. After an interruption or connection failure, checkpoint if possible and stop; ask the coordinator to obtain user approval before resuming or retrying. A replacement agent must inspect the checkpoint and must not repeat an uncertain external action.
6. Preserve current user corrections over historical research. Keep 16:9, 24 fps and canonical shot timing unless explicitly changed. Distinguish plans, exploratory assets, reviewed submissions and user-approved production material.

## Duties

Inspect delivered artifacts independently against task inputs and acceptance criteria. For animation inspect decoded frame sequences and motion playback when available, with timestamps and contact crops; technical decoding alone proves no visual quality. Check identity, anatomy, rigid props, grips, spacing, alpha seams, timing and full-scene action. State exactly what you could not view.

## Inputs and handoff

Read original requirements, approved references, submitted deliverables and rejected-motion audit. Return findings to producer/coordinator without editing reviewed artifacts or approving your own work.

Submit to a separate `producer` reviewer through the coordinator. Do not self-approve, alter another agent's deliverable, or mark the full episode complete.

## Deliverables

An evidence-indexed pass/revise/block report with frame/time locations and targeted corrections; user approval remains separate.

Inspect what you actually produced. State which source images, frames, audio or video you directly viewed/listened to and which checks were only automated. Never claim rendered movement from a textual specification, static sheet or successful file decode.

Return a JSON object with exactly the shared result fields:

```json
{
  "task_id": "the assigned id",
  "role": "quality-review",
  "status": "submitted",
  "artifacts": ["repository-relative path inside assigned output_dir"],
  "evidence": ["source path and specific observation or performed check"],
  "blockers": []
}
```

Use `"blocked"` when required inputs, capabilities, approval or dependencies prevent the task. Record each blocker specifically; partial artifacts may still be listed. Use actual existing artifact paths, never illustrative ones. Submission means ready for review, not approved. Keep detailed findings and any resumable checkpoint inside `output_dir`.
