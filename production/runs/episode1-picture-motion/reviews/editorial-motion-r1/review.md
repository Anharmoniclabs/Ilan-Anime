# Independent animation-supervisor review: editorial-motion-r1

Decision: approve for the bounded technical editorial revision. This is not Luis's creative approval, canonical promotion, character-animation approval, or final episode approval. No submitted files were edited.

## Inspection and verification

Source root: production/runs/episode1-picture-motion/tasks/editorial-motion-r1. Read the current author direction, assigned script rows, prior rejection, shot/source indexes, native build recipe and actual JSON native projects. Current author corrections override older style references; script explicitly requests these character-free editorial cards. V1 remains separately present; shared-sigil.json and shared-sigil.svg compare byte-identical to v1.

Directly viewed all five submitted decoded-sheet.jpg images: S00-01 f0/12/24/36/48/60/69/72/73/95; S00-02 f0/3/12/21/24/25/119; S02-01 f0/36/69/72/78/102/111/120/129/138/287; S01-15 f0/48/95; S15-09 f0/96/191. Also independently decoded and viewed S00-02 f119 full size, confirming exact mixed-case “They count. We remember. — ABUELA.” and readable, contained Spanish lines. Viewed all five QA flagged-frame sheets, each flag at f0. No real-time playback or independent GUI reopening claimed.

Ran python -m studio qa for all five shots with their actual preview.mp4. Since r1 has no engine shot spec, review-only shot.json adapters reference its native-render PNG frames one-for-one, with post disabled. These adapters are QA evidence, not replacement native deliverables. Reports and flagged images are in each shot's qa directory here. All five no_acting flags are inapplicable to these explicitly editorial shots. S01-15 and S15-09 freeze flags correctly identify scripted black holds. No frame-count mismatch or other QA defect.

Independently fully decoded all MP4s and probed streams: 1280×720, 24/1 fps, video only; lengths S00-01 96, S00-02 120, S01-15 96, S02-01 288, S15-09 192. See independent-checks.json. Both black holds have maximum RGB value zero across every decoded pixel. Grain persists through every navy-card frame: corner red-channel standard deviation ranges 2.37–2.70, 1.51–1.79, 1.50–1.82 respectively. The simulated repeating 24-plate source is disclosed, not represented as a film scan.

Actual shot.ecproj data contains separate Solid backgrounds, Shape sigils, editable Text layers, Footage grain instances, opening Null controller and title shimmer Text/mask. S00-01 controller contains 96 position keys with x 639.2635–640.5720 and y 359.7412–360.2570, parented to the rigid sigil. Native Trim End keys complete at f72 and preserve three-frame draw increments; no disconnected stroke or warped geometry appears in sampled frames. S00-02 opacity keys complete the dissolve at f24. S02-01 completes the sigil at f72, type at f78 and has one masked shimmer interval f102–137. Saved native structure and recipe agree; worker reopening claims were not independently rerun.

## STORY_FRAME criteria

- source_precedence: pass. Current author direction and script control. Latest Amaia/rooftop style correction supersedes old comic guidance. Character source tiers 1/4 have no applicable identity test on these cards; no claim of character canon.
- identity: not applicable; no characters requested or depicted.
- style: pass for explicitly scripted editorial content. Restrained serif typography and thin gold continuous mark with visible film texture; no vector puppet or scene-art substitution.
- grade: pass. Navy, cream and gold are readable and consistent; pure black holds preserved. No skin pigment test applies.
- text: pass. Spanish, mixed-case English attribution, CEMÍ accent and EPISODE 1 · 3:07 match requested wording. No unauthorized words.
- anatomy_geometry: pass for applicable rigid geometry. One shared connected open spiral-to-triangle path, stable text and sigil; no anatomy or contact action required. Prop perspective registration remains future scene work.
- crop: pass. Complete marks, wording and effects remain inside frame; full backgrounds without exposed edges.
- layers: pass. Actual native projects provide separate editable background, sigil, typography and effect elements; alpha grain assets remain external dependencies inside the task. Keep delivery together.
- action: pass for bounded editorial requirements. Draw-on, 24f dissolve, single shimmer, grain and opening weave present with exact shot lengths. No character or environment acting completion claimed.
- setting: pass. Script requests navy/black fields rather than a Bronx, Santo Domingo or Taíno environment.
- single_asset: pass. Each assigned shot has its own native composition and silent rendered clip. Contact sheets are review evidence only.

All three requested repairs are satisfied. No targeted repair remains. Exact author approval and final sound remain separate gates.
