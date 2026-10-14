# Episode draft automation

The user requested full-episode automation after seeing the canoe test. The
coordinator uses current episode artwork as a provisional draft reference set,
preserving the original 128 shots / 27,120 frames / 24 fps. This is not author
approval of those references or permission to spend beyond the existing $5
ceiling. Paid generation remains disabled; the video bridge is anonymous-only.

```bash
.venv/bin/python -m studio episode init
.venv/bin/python -m studio episode auto
.venv/bin/python -m studio episode status
```

`init` snapshots source/script digests and builds a persistent queue at
`production/episode-automation-v1/episode.json`. Repeating init preserves it.
`auto` runs one full-duration video at a time, imports it, renders a review copy
with local script typography, and starts a real independent Codex reviewer.
The reviewer receives the actual source image and sampled decoded frames and
can inspect additional frames. Its session ID, evidence and output digest are
recorded. Sample inspection is not represented as continuous-playback review.

Approved *drafts* advance the queue. Rejected motion, missing art, long shots
requiring authored segment boundaries, interrupted reviews and generation
errors stop it. No automatic retries, provider switching, credit purchase or
scheduled reruns occur. Existing paused image-demand runs are untouched.

The shot needing an image produces one `image-request.json` using the on-demand
reference packet workflow. This requires a fresh image worker/host image tool;
the built-in chat image tool is not an unattended HTTP endpoint. The queue does
not pretend it has generated an image or insert a slideshow when that capability
is unavailable. Existing art retains its review status, and missing original
likeness references remain a final-production issue.

Use `run` for generation/import only, or `review` for the pending motion review
only. Source changes, duplicate attempt directories and concurrent coordinators
are refused. A paused queue is sticky: repeating `auto` reports the pause without
making another remote call. An already-generated browser/download result can
be recovered without another generation:

```bash
.venv/bin/python -m studio episode recover-clip --clip /absolute/path/to/result.mp4
.venv/bin/python -m studio episode auto
```

Recovery validates the clip and creates a review handoff. Failed generation
must never be resumed by editing the state JSON or removing submission locks;
inspect the failure and authorize a separate attempt when compute is available.

`assemble` refuses to create a full-episode file until every complete shot is
present with the exact frame count and matching digest. Its output is a picture
draft: original dialogue, sound design, lip sync, mix, independent final quality
review and author approval still apply. It never canonicalizes assets.

## First actual run

The local opening cards were collected. The S01-01 six-second paddle generation
was attempted once and HF returned `You have exceeded your ZeroGPU runs limit`.
The video job and episode queue are paused at that shot. No new visual clip was
downloaded, no HF credential was sent, and no paid fallback was attempted.
The full episode is **not running in the background** while this quota block
remains. Authentication may provide a different allowance, but this adapter
does not attach an HF token because authenticated ZeroGPU overages may consume
prepaid credit. Do not silently change that budget boundary.
