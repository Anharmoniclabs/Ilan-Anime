# Worker contract (every department)

Every role skill in `.agents/skills/anime-*/` points here. This file holds the rules that used to be repeated in each skill. Role files add only their duties, role rules, handoff, deliverables and tools.

## 1. Envelope

You were started for exactly one ledger task. Its envelope has `id`, `role`, `shots`, `objective`, `inputs`, `output_dir`, `depends_on`, `state`, and may add `acceptance_criteria`, `budget`, `art_direction_mode`, `requires_author_approval`. Confirm `role` matches your skill and that the task was dispatched to you. Take no other work.

## 2. Read before acting

1. `AGENTS.md`, `docs/STATUS.md` and every path in `inputs`.
2. Before any animation work: `README.md` and `research/animation_audit/REPORT.md`.
3. Visual roles (the skill says so): `production/art_direction.json`, its canonical document `research/earlier_cemi_pipeline/docs/ART_DIRECTION.md`, `research/earlier_cemi_pipeline/cemi_pipeline/docs/STYLE_BIBLE.md`, and `research/supplied_references/approved_style_reference.png`. Use the task's exact `art_direction_mode` and satisfy every criterion for that mode.

Resolve paths from the repository root. Rejected or unapproved inputs may be inspected when assigned for review or planning; they keep their status. If a required input, dependency or approval is missing or ambiguous, return `blocked` naming the exact path and the decision needed.

## 3. Scope

- Work only on `shots` and `objective`, inside any budget. Without a budget, make one bounded submission; do not start your own revision loop.
- Write only inside `output_dir`. Source assets, other tasks and the ledger are read-only. Do not follow symlinks out of `output_dir`.
- Do not spawn or delegate. Return handoff recommendations to the coordinator.
- Do not publish, push Git changes, download models or launch external jobs. Never use Higgsfield.
- Prompt rules are not a sandbox; the host's stronger permissions win.

## 4. Spending (generation)

Paid generation is allowed only when **all** are true:

1. `production/policy.json` has `generation.enabled: true`;
2. your skill lists the generation kind (`image` or `voice`);
3. the task `budget.max_cost_usd` is above zero;
4. you call it through `python -m studio generate ...`, which enforces the cap and logs every call.

Anything generated is `exploratory` until a separate reviewer approves it technically and Luis M. Minier approves the exact file digest. Never call a paid API directly. Never clone or imitate a real person's voice. AI voices must be disclosed in the credits.

## 5. Interruption

On interruption, connection failure or an uncertain external result: checkpoint inside `output_dir` if you can, then stop. Do not retry or resume. The coordinator asks the user first.

## 6. Canon

Current author corrections → current episode script → approved references → older research. 16:9, 24 fps and canonical shot IDs and timing stay unless the user changes them. Keep plans, exploratory assets, reviewed submissions and author-approved material clearly separate. Never silently promote anything.

Status words: `exploratory`, `submitted`, `technical-approved`, `author-approved`, `canonical`, `rejected` (terminal), `superseded`.

## 7. Evidence

Inspect what you produced. State which images, frames, audio or video you directly viewed or heard, and which checks were only automated. A text spec, a static sheet or a successful decode never proves movement.

## 8. Result

Write `result.json` in `output_dir` and return the same object:

```json
{
  "task_id": "the assigned id",
  "role": "your role id",
  "status": "submitted",
  "artifacts": ["repository-relative path inside output_dir"],
  "evidence": ["source path and specific observation or performed check"],
  "blockers": []
}
```

- `status` is `submitted` or `blocked`. Submitted means ready for review, not approved.
- List only real existing paths inside `output_dir`.
- Add `host_agent_id` when the envelope requires host bindings; never invent one.
- Use `blocked` when inputs, capabilities, approvals or dependencies stop the task. Name each blocker. Partial artifacts may still be listed.
- You never approve your own work or mark the episode complete.
