# Production status — 12 October 2026

## Runtime added 12 October 2026 (studio v2)

- `python -m studio`: Codex agent runner (separate worker and reviewer sessions, revisions, author gates, pause-on-interrupt), render queue with checkpoints and assembly, automated QA flags with repair tasks, layer split/matte/registration, motion specs with contact locks, dialogue worklist, mouth exposures, loudness mix, and opt-in paid image/voice generation (off, $0 caps).
- Engine v2 replaces the v1 compositor: pivot-correct scale/rotation without clipping, parent transforms, multiplane parallax, blend modes, PRESS as a style state, 10 FX generators and the film post stack. BT.709-tagged review files and lossless FFV1 masters.
- All 128 shot specs are now runnable animatic specs (keyframe holds under scripted camera moves, slates for the 64 shots without art, FX tokens). The animatic locks timing; it is **not** animation.
- Skills moved to `.agents/skills/` (Codex discovery) and are generated from `roles.json`; per-skill boilerplate now lives once in `production/WORKER_CONTRACT.md`.
- Registration of the Beheto atlas against the drum body: poses 3 and 4 align; 2, 5, 6, 7 and 8 need redraws (drum geometry differs, not just position).

- Blender NPR skill (`$blender-npr-3d-anime`) wired to nine roles, with `studio blender render|check|import`: headless renders under the NPR contract, step-grid checks and import as engine exposures. The in-Blender script is tested against a stub of the Blender API only; it has not run in a real Blender here.

Still blocked on Luis: the three S01-11/12 timing conflicts, adding the original pencil portraits (tier-1 identity source), deciding which keyframes are approved, and any spend.

## Available

- Thirty individually bounded production departments, each with its own skill and independent designated reviewer.
- A versioned Cemí art-direction contract covering character, environment, story-frame and editorial modes.
- Separate digest-bound technical and Luis M. Minier author-approval gates; rejected versions are terminal.
- An append-only, hash-chained asset registry with provenance, continuity, supersession and canonical-only final-use links.
- A 27-stage complete-shot pipeline covering script supervision, layout, design, hand-drawn animation, cleanup, paint, FX, full sound post, QA and final author approval.
- A read-only loopback production dashboard and a studio-wide architecture validator.
- A persistent agent ledger, real host-agent handoff registry, explicit interruption pause and user-controlled recovery.

- Full Episode 1 script, visual bible, sound bible, effects specification and engineering contract.
- 128 body-shot templates; 27,120 contiguous frames at 24 fps.
- 77 numbered keyframe PNGs covering 64 shots; two rejected earlier frames kept separately.
- Clean plates and extracted cutouts from the first local renderer.
- A general compositor supporting RGBA layers, replacement sequences, explicit exposures, independent layer rates, transform keys and camera keys.
- A deterministic experimental mesh renderer, retained for reproducibility and explicitly rejected for production quality.
- Two rejected motion-test MP4s and their temporary synthesized sound tracks.
- An eight-second / 384,000-sample mono loop at 48 kHz.
- Frame-sequence review sheets documenting the visible failures.
- Three newly generated replacement-pose atlases and an empty-canoe plate. These need registration, matte review, character continuity review and further breakdown drawings.
- Earlier character/style configuration, the SDXL planning/generation CLI, the Qwen style-training proposal and the river asset pack.

## Rejected approach

The first 24-second test distorts Beheto's face, shoulders, hands, clothes, drum and hull. In the wide shot, the people pulse inside sliding canoe cutouts, paddles do not perform a credible stroke, wake fragments remain attached, and the foreground has a water seam. The bell's clapper is rigidly attached to the bell layer. See the frame audit.

The author's correction is binding: animate the full scene with convincing action while keeping the artwork stable. Do not replace the deformation with a still-image slideshow.

## Replacement-cel pass

The first replacement sheets have been generated, not completed as animation:

| File | Intended use | Current limit |
|---|---|---|
| `beheto_eight_poses.png` | Hover → contact → weight press → settle | Drum/head registration and matte edges need review; no final timing assigned |
| `lead_canoe_eight_poses.png` | Reach → plant → pull → lift → recovery | Hull geometry and paddle-side continuity vary; must isolate/stabilize hull and repair the stroke before use |
| `children_six_poses_unapproved.png` | Look back → turn forward → brace | Background/alpha and age/identity consistency need review |
| `drum_clean_plate.png` | Empty canoe and environment behind Beheto | Must be checked against original composition and occlusion |

Generating these sheets does not establish that they meet the production standard. They are preserved with the code and research so the next pass can continue without losing provenance.

## Still to complete

The studio architecture now validates cleanly; the episode does not. System readiness and art/episode readiness are deliberately reported separately.

1. Register usable cel drawings against fixed landmarks. Redraw inconsistent anatomy, hulls and grips.
2. Complete the 24-second S01-11/S01-12 action with actual palm placement, weight, paddle drag/lift/recovery, passenger counterbalance, travelling wakes and current turn.
3. Complete the rest of S01 and all remaining episode shots, including missing backgrounds and character poses.
4. Implement and review the specified PRESS state, Echo crowd acting, era transitions, lip sync, film treatment and final camera coverage.
5. Record exact dialogue and build the sound mix with original or appropriately licensed music.
6. Review the complete sequence in motion, not only contact sheets. A technical export check cannot approve animation.

## Source precedence

Current user corrections → current episode script for action and staging → approved character references and canonical art direction → earlier proposals. The earlier 90-second river pack and current episode script differ in canoe assignments. Their contents remain separate; never silently merge them into a new cast arrangement.
