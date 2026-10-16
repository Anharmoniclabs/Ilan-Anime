# Production status — 14 October 2026

[Home](../README.md) · [Repository map](REPOSITORY_MAP.md) · [Documentation index](README.md)

## Current saved checkpoint

The full episode remains unfinished. Counts below were checked against the saved [inspection timeline](../production/runs/episode1-full-picture/tasks/episode-wiring/timeline.json) and [validation record](../production/runs/episode1-full-picture/tasks/episode-wiring/validation.json) on 14 October 2026.

| Area | Saved state |
|---|---|
| Story timing | 128 body shots, 27,120 frames, 18:50 at 24 fps; output 16:9 |
| New representative stills | 128 selected images in the [new shot index](../production/runs/episode1-anime90s-scenes/shot-index.json); still coverage is not action coverage |
| Motion inspection | 10 technically approved drafts, one unreviewed water draft, one partial Amaia draft; 116 slots have no motion clip |
| Completed action attempt | [Action checkpoint](../production/runs/episode1-action-completion-20261014/checkpoints/progress.json): four blocked tasks, two independent rejections, zero new technically approved motion shots |
| New staged draft work | [S01-07 picture-draft run](../production/runs/picture-draft-s01-07-v1/) and [catalog](../production/picture-drafts/catalog.json) are local work in progress; inspect their current ledger rather than inferring completed footage |
| Sound | Excluded from the current silent picture workflow; no finished episode voice/mix delivery |
| Final approval | Technical draft reviews do not confer exact-file author approval or finished-episode status |
| Backup | [Git-object volume manifest](../backups/2026-10-14/manifest.json): incomplete, five of 299 expected volumes present |

Open the [local episode browser](../production/runs/episode1-full-picture/tasks/episode-wiring/index.html) for shot-by-shot sources and limits. Use [the repository map](REPOSITORY_MAP.md) for editable sources, all runs and archives. Saved ledgers/checkpoints describe recorded work, not live process activity; inspect them before any authorized recovery.

## Drawing engine — 16 October 2026

Branch `feature/reference-drawing-engine` adds `studio/drawing/` ([manual](DRAWING_ENGINE.md)). Verified locally: the 8 approved paddle cels reconstruct into editable layers (layered mean color error 1.5–5.1/255); Amaia front-view expressions are drawn procedurally from a candidate identity model; Qwen picks expressions from script lines (8/8 valid); S01-01 re-renders byte-identically from its approved plan; and FLUX.2 Klein produced a three-quarter Amaia on CPU in ~23 min with some identity drift. No new shot animation, independent review or author approval is claimed.

The dated sections below preserve earlier implementation and production history. Their earlier coverage counts and descriptions of running/paused tasks are snapshots; use the current checkpoint above and the latest exact task evidence for present work.

## New shot illustrations — 14 October 2026

The author requested new 1990s anime artwork for every scripted Episode 1 shot,
following the new cast/style review. All 128 shot IDs now have a new representative
image, including native editorial cards, in
`production/runs/episode1-anime90s-scenes/`. The run preserves earlier sources and
all revisions. Its `shot-index.json`, selected PNGs and 32-page review PDF identify
the selected stills; per-task manifests and independent reviews record limits.

This completes source-image coverage only. Symbol/prop registration, typography
cleanup, additional action drawings, animation and sound remain unfinished.
No new shot-image author approval or final episode approval is inferred.

## Craft integration — 13 October 2026

- `studio craft doctor|tools|run|cels` connects all seven installed local engines.
- Saved recipes retain per-app state and write durable call receipts. The shared
  worker contract routes production departments to the appropriate engine.
- Explicit PNG exposures now produce an editable EffectCraft composition, PNG
  frames, a verified 24 fps preview, a FilmCraft timeline, and a compatible local
  studio shot spec. Original drawings are copied and hashed; outputs remain exploratory.
- All seven live connections, a 13-step multi-app recipe, cel holds/alpha,
  native project reopening and local compositor interoperability were exercised.
  Five focused regression tests pass, including the live engine test.
- Scope is integration and technical fixtures, not new episode animation or audio.
  See `docs/CRAFT_WORKBENCH.md` and `production/craft-validation/`.

## Runtime added 12 October 2026 (studio v2)

- `python -m studio`: Codex agent runner (separate worker and reviewer sessions, revisions, author gates, pause-on-interrupt), render queue with checkpoints and assembly, automated QA flags with repair tasks, layer split/matte/registration, motion specs with contact locks, dialogue worklist, mouth exposures, loudness mix, and opt-in paid image/voice generation (off, $0 caps).
- Engine v2 replaces the v1 compositor: pivot-correct scale/rotation without clipping, parent transforms, multiplane parallax, blend modes, PRESS as a style state, 10 FX generators and the film post stack. BT.709-tagged review files and lossless FFV1 masters.
- All 128 shot specs are now runnable animatic specs (keyframe holds under scripted camera moves, slates for the 64 shots without art, FX tokens). The animatic locks timing; it is **not** animation.
- Skills moved to `.agents/skills/` (Codex discovery) and are generated from `roles.json`; per-skill boilerplate now lives once in `production/WORKER_CONTRACT.md`.
- Registration of the Beheto atlas against the drum body: poses 3 and 4 align; 2, 5, 6, 7 and 8 need redraws (drum geometry differs, not just position).

- Blender NPR skill (`$blender-npr-3d-anime`) wired to nine roles, with `studio blender render|check|import`: headless renders under the NPR contract, step-grid checks and import as engine exposures. The in-Blender script is tested against a stub of the Blender API only; it has not run in a real Blender here.

Still blocked on Luis: the three S01-11/12 timing conflicts, adding the original pencil portraits (tier-1 identity source), deciding which keyframes are approved, and any spend.

## Earlier baseline available — 12 October 2026

- Local ComfyUI image-generation adapter with optional LoRA/ControlNet, loopback-only transport, paid/custom-node-disabled launcher, durable manual recovery and exploratory asset registration. HTTP contract tested with a synthetic server; no real GPU/model generation has run. See [setup and limits](COMFY_LOCAL.md).

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

### Earlier picture-motion recovery — 14 October 2026

Later user instruction: **run**. The runtime restriction was resolved through
approved escalated host execution; child workers retain their workspace-write
sandbox. Separate Codex reviewers completed the saved water, editorial and graph
reviews and requested targeted revisions. `water-motion-r1` and
`editorial-motion-r1` were running at that checkpoint; `research-graph-r1` was
queued. `amaia-registration` was running in `episode1-picture-motion-continuation`
from the six saved drawings; a silent eight-second draft has been rendered and
is undergoing checks. The old Amaia task is archived as incomplete, not still
running. No paid generation was enabled. See
`production/runs/episode1-picture-motion/checkpoints/2026-10-14-recovery/run-resumed.json`
for active runner checkpoints; inspect before launching duplicate work. This
supersedes the runtime-blocked status below, not the unfinished episode status.

Continued the interrupted `episode1-picture-motion` run. Recovered the existing
water-motion submission; its independent review could not launch because
`codex exec` failed initializing the in-process app-server client with
`Read-only file system (os error 30)`. The run is paused; no retry, spending,
policy change or new creative approval occurred. The first recovery call had
a missing runner checkpoint; that bookkeeping was repaired before the reviewer
process was attempted.

Watchable checkpoint:
`production/runs/episode1-picture-motion/checkpoints/2026-10-14-recovery/silent-motion-excerpts.mp4`.
This packages seven existing draft shots (including two scripted black cards)
into a labeled 55-second silent reel, 1,320 frames at 24 fps, 1280×720.
Source frame counts, silent streams and full output decoding were verified.
It is not the full episode and adds no newly animated shots. The accompanying
`coverage.json` records source hashes and omissions; `recovery.json` records the
execution blocker. Amaia's six raw replacement drawings remain saved, awaiting
registration/compositing and independent review. The remaining 121 shots are
not represented in this reel. Full acting, continuity cleanup and shot review
remain unfinished; sound stays outside the current request.

The studio architecture now validates cleanly; the episode does not. System readiness and art/episode readiness are deliberately reported separately.

1. Register usable cel drawings against fixed landmarks. Redraw inconsistent anatomy, hulls and grips.
2. Complete the 24-second S01-11/S01-12 action with actual palm placement, weight, paddle drag/lift/recovery, passenger counterbalance, travelling wakes and current turn.
3. Complete the rest of S01 and all remaining episode shots, including missing backgrounds and character poses.
4. Implement and review the specified PRESS state, Echo crowd acting, era transitions, lip sync, film treatment and final camera coverage.
5. Record exact dialogue and build the sound mix with original or appropriately licensed music.
6. Review the complete sequence in motion, not only contact sheets. A technical export check cannot approve animation.

## Source precedence

Current user corrections → current episode script for action and staging → approved character references and canonical art direction → earlier proposals. The earlier 90-second river pack and current episode script differ in canoe assignments. Their contents remain separate; never silently merge them into a new cast arrangement.

## Picture-motion review checkpoint — 14 October 2026

All 128 shot slots remain wired across 27,120 frames (18:50 at 24 fps), but this is an incomplete inspection timeline, not a finished episode. The four insert shots S03-03, S04-02, S05-13 and S06-03 passed independent technical review in `episode1-insert-finish/reviews/native-inserts/review.json` and are now linked into the episode index. Current coverage: 10 technically approved shot drafts, one unreviewed water draft, one partial Amaia draft, and 116 shots without motion clips. Technical review is separate from author creative approval. Sound remains excluded.

Amaia's `episode1-amaia-finish` run is paused at the revision limit. Review rejected `three-losses-r2` for undersized adult figures and insufficient bench support; the three fade endpoints, head arc, hull occlusion and 192-frame silent delivery passed. The author's fourteen-to-eleven / exactly-three-losses decision remains recorded in the current script. The rejected version has not replaced the earlier explicitly partial inspection clip. No full-episode delivery or dependable completion ETA exists yet.


## Action-production attempt — 14 October 2026

Luis authorized resuming draft production and creating the missing drawings. Run `episode1-action-completion-20261014` produced six bounded tasks: four blocked and two independently rejected. No new shot passed technical review; the inspection timeline remains 10 technically approved drafts, one unreviewed water draft, one partial Amaia draft and 116 slots without motion clips. The full 18:50 episode remains unfinished.

- **S01-07 writing:** a new seven-second silent draft and editable EffectCraft/FilmCraft sources were rendered. Independent review rejected pose holds/jumps, missing lift drawings, matte seams and lower-line contact. A focused 36-cell correction also failed: registered nib advance was only 4px/6px, with reversals, an unconnected return and clipped feathers. No second invalid clip was rendered.
- **S01-02 canoes:** two new source sheets remain unusable as a complete stroke because of grip loss and changing paddle/body geometry. The second sheet fixes cropped blades but not contact. No motion clip was produced.
- **S01-03 Amaia:** registration diagnostics established the adult-scale/seating problem. A new bench plate has visible wooden supports, but independent review rejected it as a complete three-adult solution because the layout crowds bodies/faces and still lacks valid contacts/lower bodies. No replacement shot was promoted.

All candidates, exact built-in imagegen prompts, hashes, diagnostics, native writing sources and reviews remain in [the run](../production/runs/episode1-action-completion-20261014/). The [production checkpoint](../production/runs/episode1-action-completion-20261014/checkpoints/progress.json) records the exact remaining drawing work. The [rejected writing draft](../production/runs/episode1-action-completion-20261014/tasks/s01-07-writing-action/native/preview.mp4) is available for inspection, not as finished episode footage. Its 168-frame reproducible PNG cache was removed after verifying the native projects reference retained source drawings; no original art was deleted. No Git uploads or paid API generation occurred in this pass.

The run is paused after the final blocked submission; no production worker remains active. No automatic continuation or completion is implied. The next attempt needs controlled contact-matched drawings and a valid seated layout; repeating the same multi-pose sheet approach has not supplied them.
