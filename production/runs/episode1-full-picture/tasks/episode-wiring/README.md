# Episode 1 inspection timeline

[Repository map](../../../../../docs/REPOSITORY_MAP.md) · [Current status](../../../../../docs/STATUS.md)

Snapshot checked 14 October 2026 against `timeline.json`, `validation.json` and `native-validation.json`.

Open **index.html** directly from disk. No server, JavaScript, hosting or network is used. Keep this task within the repository for relative source links. The current user explicitly requested this local review index; it is not production scene art.

Open **episode.filmcraft** in FilmCraft: 128 range markers span exactly [0,27120), at 24 fps, 1280×720, square pixels, Rec.709. Twelve inspection clips occupy their real shot slots; 116 slots have no media. Markers name missing, partial, unreviewed or rejected states. The two black clips are script-required S01-15 and S15-09; no other black padding, stills, loops or proxy paintings are placed. FilmCraft displays empty timeline gaps as empty/black during playback; this is an incomplete editable inspection sequence, not a finished episode. Do not export it through the GUI as final animation.

Current source snapshot: 10 technically approved drafts, one unreviewed water draft and one partial Amaia S01-03 draft; 116 shots have no motion clip. The approved drafts include the five editorial r1 clips, graph r1 and four finished native inserts. Rejected graph v1 and Amaia finish revisions remain preserved in their source runs and are not selected. No author approval or full action coverage is inferred from technical review. `links.json` records the exact selected sources and reviews; `timeline.json` records all 128 slots. Existing rejected mesh tests are never used.

## Commands (repository root)

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python production/runs/episode1-full-picture/tasks/episode-wiring/wire.py refresh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python production/runs/episode1-full-picture/tasks/episode-wiring/wire.py native
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python production/runs/episode1-full-picture/tasks/episode-wiring/check.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python production/runs/episode1-full-picture/tasks/episode-wiring/wire.py assemble
```

`refresh` rereads canonical timing, artwork index, contracts and the explicit `links.json` selection; verifies artwork and pinned clip hashes, exact decoded frame count, 24 fps rate/duration, square-pixel 16:9 and no audio; regenerates machine timeline and offline index. `native` also saves/reopens the editable sequence and verifies all placements and markers. Receipts get a fresh numbered directory on each successful invocation. `seed` establishes this initial curated selection only: do not use it to refresh later coordinator relinks.

The native edit is generated: manual FilmCraft changes should be saved to a separate task-local filename before regenerating. `links.json` is the persistent selection input. No file is selected by modification time or filename glob. Rebuilding never changes canonical specs or source media. Clip/native source paths in FilmCraft are absolute; after moving the checkout regenerate with `native` to relink them.

To replace a shot, coordinator supplies a JSON record inside this task directory containing `path`, pinned `sha256`, `native`, `status`, and optional `task_result`/`review` repository-relative paths. Status is `unreviewed`, `technical-approved`, `partial`, `rejected` or `complete` (a label alone never enables assembly). Run:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python production/runs/episode1-full-picture/tasks/episode-wiring/wire.py relink --shot S01-03 --record production/runs/episode1-full-picture/tasks/episode-wiring/replacement.json
```

This verifies source hash/rate/frame count/silent streams, updates the explicit selection, refreshes the index and rebuilds the native timeline. Shorter clips are refused; they need a separately scoped partial-range contract rather than padding. Missing scripted actions in a full-duration clip still require `partial`. Existing versions remain in source task directories. No automatic generation or retry occurs. Stop on any connection interruption and obtain coordinator direction before a later invocation.

## Strict silent assembly

`assemble` exits 2 and writes **assembly-check.json** before creating media when any shot is missing, partial, rejected, unreviewed or only technical-approved. Today all 128 slots fail final eligibility. `complete` additionally requires the exact path/digest/version to be canonical in the existing hash-chained `production/asset-registry.json` with an active final-use link for this shot. It also requires a coordinator-supplied full-action attestation pinned by `release_attestation_sha256`, referenced by `release_attestation`. Its fields are `shot`, `sha256`, `full_action_coverage: true`, `status: canonical`, `creator_id`, `technical: {decision: approve, reviewer_id, sha256}`, and `author: {decision: approve, id: luis-m-minier, sha256}`. Technical reviewer must differ from creator. These records are never generated or approved by this worker. Link records name `asset_id` and `version` for registry verification. Local approval records remain the repository trust boundary; this script does not authenticate people independently.

Only after every gate passes does assembly encode each approved clip once at 1280×720, 24 fps, BT.709 H.264 yuv420p, no audio, then concatenate in canonical order and verify 27,120 frames. No rate conversion, repeated frames, tpad, loop or still fallback exists. The output directory must not already exist. The successful whole-episode encoding branch cannot be exercised with current unfinished sources; the refusal branch has been exercised. No episode MP4 was produced.

## Evidence and compatibility

The following implementation evidence describes the initial wiring submission, when eight source clips were inspected and seven were placed. Current placement counts are in `native-validation.json` (12 clips, 116 empty slots); old check records are retained rather than rewritten.

- Python standard library + Pillow: offline JSON/HTML/thumbnails; executed here.
- FFmpeg/ffprobe: eight clips decoded/count-probed; dimensions, duration, rates, silence and SHA-256 verified. Thumbnail art hashes checked for all 128 slots.
- FilmCraft 0.2.1/schema 12 through local `studio.craft.Session`: live schemas discovered, saved recipe executed, native saved and reopened. Seven placed clips and all 128 markers verified against exact frame offsets. Water's 1920×1080 source is fitted to 1280×720 without crop; other clips already match.
- Native project points to original renders; source EffectCraft/FilmCraft projects remain linked in the offline index. Missing native motion assets are intentional gaps.
- `checks.json`, `validation.json`, `native-validation.json`, `native-reopened.json`, and receipts contain automated evidence. Two independent refreshes reproduce identical machine timeline bytes from recorded source hashes.

## Downstream remediation and art contract

Every slot embeds its full action contract, proposed phases and microkeys, required registered character drawings, prop/contact requirements, environment layers and script conflicts. These are requirements and unvalidated coverage, not claims that every listed drawing is absent: existing drafts may cover subsets. All new selected artwork remains still-image coverage, not animation. Amaia specifically needs registered seat silhouettes with bench/gunwale occlusion, seat-targeted gaze, at least two head-lowering and two return breakdowns, and independent water; the ghost count was subsequently resolved by the author: fourteen-to-eleven, exactly three losses (see ../../author-decisions.json). The current episode script and timeline reflect that correction. Source HANDOFF and result links preserve these limits. The original graph v1 review requested separate editable components, connected ownership discovery, paper-to-sandwich breakdowns and finish correction; the current selection uses independently reviewed graph r1. Old editorial and water v1 revisions were rejected; r1 does not inherit approval; editorial r1 has its own new technical approval.

STORY_FRAME criteria are carried forward in action contracts and the art-direction source hash; this wiring makes no pixel-quality or creative approval claim. Current author corrections and script precede older graphic-novel research. Source tiers/identity/style/grade/text/geometry/crop/layers/action/setting/single-asset checks remain for the independent shot reviewers. Registered replacements must establish acting; camera motion and warped paintings cannot satisfy full-action attestations. Audio and voices remain excluded from this silent workflow. Submit this wiring to the coordinator's separate quality-review worker; this worker cannot approve it.
