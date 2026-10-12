---
name: anime-studio
description: "Run Heralds of the Cemí production in this repo: plan shot pipelines into the ledger, drive Codex workers and independent reviewers, render, QA and assemble. Use for any request to produce, continue, render or review the anime."
---

# Coordinate the studio

You are the coordinator. You own the ledger for a run; workers and reviewers are separate Codex sessions started by the runner. Read `AGENTS.md`, `docs/STATUS.md` and `docs/STUDIO_RUNTIME.md` first.

## Loop

1. `python -m studio status` - see runs, pauses, spend and what exists.
2. New shot or sequence: write a pipeline spec like `production/examples/s01_11_12_pipeline.json`, then `python -m studio plan <spec>` (adds the 27 tasks).
3. `python -m studio run --run <run> --dry-run` to see what would start, then `python -m studio run --run <run> [--max-tasks N] [--parallel N]`. Each ready task gets a Codex worker; each submission gets a separate Codex reviewer of the role in `roles.json`; rejections become revision tasks (capped in `production/policy.json`).
4. When the runner reports `awaiting_luis`, stop and tell Luis exactly what to watch and which command records his decision (`python -m studio approve ... --i-am-luis`). Never run `approve` yourself.
5. Picture work at any time: `python -m studio animatic`, `render`, `queue`, `qa`, `assemble`.

## Hard rules

- One coordinator per run. Never edit `ledger.json` or `handoffs.json` by hand.
- A paused run stays paused until Luis says to resume; then record it with `python production/runtime.py --run <run> resume --approval 'APPROVE RESUME <run>'`. Before resuming, inspect the paused task's output directory so nothing is launched or paid for twice.
- Never role-play several agents in one reply. If `codex` is unavailable, say so and stop.
- Paid generation only through `python -m studio generate`, only when `production/policy.json` enables it and the task budget allows. Never raise caps or flip `enabled` yourself.
- Report approved, rejected, blocked and awaiting-Luis work separately. Tests, renders, contact sheets and QA with zero flags are not approval. Only Luis approves creative work.
- Animation means registered replacement drawings with real contacts, not warps, sliding cutouts or camera moves. See `research/animation_audit/REPORT.md`.
