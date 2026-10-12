# AnimeStudio project guidance (Codex)

This repo produces **Heralds of the Cemí, Episode 1** by Luis M. Minier. User instructions in the active conversation take precedence over this file.

## How work runs here

- Coordinator: use the `$anime-studio` skill (`.agents/skills/anime-studio/SKILL.md`). Production runs go through `python -m studio` (see `docs/STUDIO_RUNTIME.md`).
- Workers and reviewers: the runner starts each as its own `codex exec` session with a role skill (`$anime-<role>`) and the shared `production/WORKER_CONTRACT.md`. Role skills are generated from `production/roles.json` by `python production/build_skills.py`; edit roles.json, not the generated files.
- One coordinator writes a run's ledger. On interruption the runner pauses; ask Luis before resuming. No automatic retries, provider switching or scheduled reruns.
- Never role-play several agents in one response. If Codex delegation isn't available, say so.

## Before changing animation

Read `README.md`, `docs/STATUS.md` and `research/animation_audit/REPORT.md`.

- Preserve source artwork and rejected experiments; write new iterations separately.
- The mesh videos are rejected, not a baseline to expand.
- Do not claim finished animation from still keyframes, camera pans, warped paintings, unregistered sprite atlases, technical tests or the animatic.
- Keep faces, props, hulls and contact points stable. Use registered replacement drawings for substantial actions (`studio layers register`, `studio motion check`) and look at the frames.
- Follow original shot IDs and script timing. Output is 16:9 at 24 fps (Luis's request; the historical script says 4:3).
- Track partial coverage, missing assets, unrecorded voices and rejected work explicitly.
- Source imports under `research/` hold older proposals; current author corrections and the current script win.

## Money and approval

- Paid generation (images, voices) only via `python -m studio generate`, only when `production/policy.json` enables it, the role has the right and the task budget allows. Agents never edit policy.json, raise caps or run `python -m studio approve`.
- Generated work is `exploratory` until an independent reviewer approves it technically **and** Luis approves the exact file.
- No voice cloning or imitation of real people; AI voices are disclosed in the credits.
- Never commit credentials, API keys, signed URLs or unrelated personal context.
