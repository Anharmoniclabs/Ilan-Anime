# Independent quality review: episode-wiring

Decision: APPROVE the bounded wiring task only. This is not approval of shot animation, release readiness, artwork, or Luis's creative approval. No submitted artifact was edited. Hand off this report to the coordinator and separate producer.

## Acceptance evidence

- `audit.json`: all 128 unique slots independently compared to canonical episode IDs, starts, durations and ends; contiguous [0,27120), 24 fps and 16:9. All source hashes and 128 artwork hashes match. Full action contracts, drawing requirements, prop/environment requirements and missing/unvalidated action lists are embedded in every row. These lists are requirements, not proof of drawing completion.
- `native-open.json` and `native-open-receipts/`: independently opened the submitted FilmCraft project through the live engine. Its 128 markers and seven real clips occupy exact canonical ranges. Native JSON inspection also matched each clip's original media path, source-in 0, speed 1 and duration. 121 slots remain empty. Rejected S14-03 is not placed. The scripted black clips S01-15 and S15-09 are legitimate source media, not missing-shot padding.
- `audit.py`/`audit.json`: independently hash-checked, ffprobed and fully decoded all eight selected draft clips. Counts, duration, every frame timestamp, 24 fps, square pixels, 16:9 and silent streams pass. Recomputed timeline equals the submission, and two refreshes produce identical bytes.
- `relink-check.json`, `sandbox/native-validation.json`: executed the actual relink command with the existing pinned Amaia v2 record in an isolated review output directory. It refreshed and rebuilt/reopened the native edit; same selection produces the same timeline. Original links remain unchanged.
- `sandbox/assembly-check.json`: actual assembly routine returns 2 with all 128 slots refused before creating an assembly directory. `negative-checks.json` independently exercises nonfinal states, a complete label without evidence, duplicate IDs, gaps and corrupt end timing. Reviewed release code requires canonical registry/final-use evidence, exact digests, independent technical and author records and full-action attestation. Successful whole-episode encoding cannot be exercised with unfinished sources and is not claimed.
- Original `index.html`: parsed every href/src and verified all local files exist. Thumbnails, shot status, timing, artwork, draft/native links and expandable action requirements are present; no network dependency. No browser rendering/layout inspection was available or claimed.
- Provenance accurately distinguishes 120 missing-motion shots, five technical-approved editorial r1 clips, one unreviewed water r1 clip, partial Amaia v2 and rejected graph v1. Existing rejected mesh work is not placed; excluded-history preserves earlier rejected revisions. README identifies specific Amaia breakdown/ghost-seat/water gaps and graph remediation, and points to source results and reviews. No policy, canonical spec, approval or paid-generation change is part of this submission.

## Visual inspection and automated QA

Viewed the submitted `inspection-midpoints.jpg`, current Amaia/rooftop references and historical supplied reference. Independently decoded all eight MP4s to review-local 320x180 PNG sequences. Ran `python -m studio qa` on corresponding review-only decoded-frame shot specs, passing the original MP4 with --render; all commands completed. Reports reside at `render-qa/SHOT/qa/qa_report.json`. These flattened inspection adapters do not describe the originals' native layers, so their generic no_acting flags at f0 do not determine actual acting quality. Both black cards also trigger freeze flags: S01-15 f0–95 and S15-09 f0–191, consistent with scripted holds.

Directly viewed every flagged frame in `qa-flags.jpg` and five decoded samples per clip in `decoded-samples.jpg` (first, quarter, midpoint, three-quarter and last):

- S00-01 f0/24/48/72/95 shows progressive sigil reveal; S00-02 f0/30/60/90/119 shows the text card appearing.
- S01-01 f0/36/72/108/143 shows paddle immersion and withdrawal over water. Still unreviewed motion; these sparse samples are not a continuity/playback pass.
- S01-03 f0/48/96/144/191 shows Amaia with sleeping child, head down at f144 and increasing close-up. Missing ghost seat staging and full acting remain documented; no complete-action claim is accepted.
- S01-15 f0/24/48/72/95 and S15-09 f0/48/96/144/191 are black.
- S02-01 f0/72/144/216/287 shows title reveal. S14-03 f0/96/192/288/383 shows the UI graph and disconnected footer at the end; its rejection remains respected.

No real-time playback, exhaustive full-resolution contact/anatomy inspection or visual browser inspection was performed. Approval applies to wiring, which introduces no new scene pixels or animation and explicitly keeps these visual limitations open.

## STORY_FRAME criteria boundary

Source precedence is preserved: current author corrections and Amaia/rooftop references supersede older comic language. Identity, style, grade, text, anatomy/geometry, crop, layers, action, setting and single-asset criteria remain shot-level acceptance gates, not automatically passed by this wiring. The selected images remain still references; incomplete/partial motion cannot pass final assembly. Sampled Amaia retains her wrap, pendant, child and moonless canoe setting; the graph's finish/action defects are retained as rejected. Editorial typography is confined to existing scripted cards or the explicitly requested review index. The wiring provides one editable episode sequence and does not substitute a collage, painting pan or padded video for completed animation.

No blocking repairs are required for this bounded deliverable. All downstream art/action gaps and Luis approval gates remain open.
