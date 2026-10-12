# AnimeStudio project guidance

For multi-agent production, read `skills/anime-studio/SKILL.md` and use roles in `production/roles.json`. Spawn real workers only when the host provides delegation; never represent role-play as agents. On connection interruption, pause and ask before resuming. No automatic retries or provider switching.

Every visual task must declare one mode from `production/art_direction.json`, read the canonical art direction, and preserve Luis M. Minier's exact drawing-derived identity and finish. Independent technical review and Luis's approval of the exact asset digest are separate gates. Rejected versions never become upstream production material.

Use the asset registry for stable IDs, hashes, provenance, continuity, status and final-use links. Use the complete-shot pipeline for production dependencies; do not skip layout, cleanup, paint, effects, sound, QA or author gates because an output file exists. Architecture tests do not establish episode or visual readiness.

Read `README.md`, `docs/STATUS.md`, and `research/animation_audit/REPORT.md` before changing animation. User instructions in the active conversation take precedence.

- Preserve the source artwork and rejected experiments; write new iterations separately.
- The current mesh videos are rejected, not a production baseline to expand blindly.
- Do not claim finished animation from still keyframes, camera pans, warped paintings, unregistered sprite atlases, or technical test results.
- Keep faces, props, hulls and contact points stable. Use replacement drawings for substantial actions and view the resulting frame sequences.
- Follow original shot IDs and script timing. The user requested 16:9 despite the historical script's 4:3 format.
- Track partial coverage, missing assets, unrecorded voices and rejected work explicitly.
- Do not start paid generation, cloud GPU training, or model downloads merely because archived research describes them.
- Source imports under `research/` contain older proposals. Current author corrections and the current episode script supersede conflicting historical staging.
- Never commit credentials, Library transport helpers, signed URLs, or unrelated personal context.
