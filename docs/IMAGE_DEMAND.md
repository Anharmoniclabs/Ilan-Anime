# One image when a shot needs it

`studio demand` creates one bounded assignment for the shot currently being
worked on. Each assignment has a fresh Codex worker turn followed by a separate
reviewer turn. It does not queue the episode's missing artwork. Codex runs using
the host's existing account and model configuration; availability of an image
tool in this chat does not establish availability in every CLI worker.

The production coordinator calls `python -m studio demand ensure SHOT` when
it reaches a shot needing an image. This combines preparation and one complete
worker/reviewer cycle; it returns the saved state or reuses canonical artwork
on later calls. It never advances to a different shot on its own. This is the
integration point for local planning before handing that shot to HF video.

## Coordinator commands

```bash
python -m studio demand status
python -m studio demand ensure S01-01
```

For a preview of the assignment before a live turn:

```bash
python -m studio demand need S01-01
python -m studio demand work S01-01 --dry-run
python -m studio demand work S01-01
```

`need` first checks the asset registry and existing shot keyframes. A saved
candidate gets an inspection turn instead of another generation. Canonical
artwork is reused. S00 sigil and title cards stay with the local engine.
Demand preparation is idempotent; repeating a successful `work` collects its
existing result and never starts another image. The CLI holds a coordinator
lock while working. Other studio registry writers must not run simultaneously.

The caller chooses the shot at the point its layout/animation needs an image.
For a specific model sheet or composition, add repository-relative paths:

```bash
python -m studio demand need S03-01 --ref path/to/model-sheet.png
```

Use `--candidate path/to/existing.png` to select a recovered image that is not
in the episode manifest or registry. This does not approve it. Different inputs
or a correction require an explicitly requested new `--revision 2` on both
`need` and `work`. Failed/interrupted work never retries itself. Inspect saved
outputs before authorizing a new attempt; the existing paused pilot is separate.
After a rejection, pass `--correction "specific repair"` when preparing the new
revision. An active or paused prior demand prevents a duplicate revision.

## Reference packet

`production/image-demand/image-SHOT-vN/packet.json` records:

- Exact shot action, timing and adjacent same-sequence script context.
- The art contract, author-derived art direction and character bible.
- Style reference, existing candidate, nearest same-sequence reference images,
  named historical character-sheet proposals where available, and explicit refs.
- Every source's SHA-256, registry state and a frozen copy of the exact input.

Workers and reviewers receive the reference images as image attachments, not
just filenames in prose. The current script and author corrections override
historical cast arrangements. Historical sheets and baseline keyframes retain
their unreviewed status; a filename containing “approved” is not an approval.
New demand output becomes an automatic continuity anchor only once canonical.
Changed source bytes or withdrawn approvals stop the assignment.

## Worker: exactly one full image turn

Read your role skill, task envelope, packet and frozen documents. View every
reference. Identify the actual cast, ages, costumes, handedness, props, scene
era, light direction, composition and the intended moment within the action.
Record conflicts or missing identity sources as blockers; do not invent them.

If the route is `review-existing`, copy the supplied candidate to
`output_dir/candidate.png`, inspect it and report its actual flaws. Do not
regenerate it or call a model. Preserve the image bytes when already PNG; an
incompatible aspect ratio needs an explicit composition revision, not cropping
away people or props.

For `generate-one`, use the host's built-in image-generation/editing tool and
its imagegen skill for **one** image. Attach the exact packet references to
that call and request a complete 16:9 frame in the author's established style.
Write the full final prompt in output_dir. Account/tool limits apply. This
specific on-demand task authorizes the host image tool; it does not enable the
paid `studio generate` API, HF billing, model downloads or provider fallback.
If the tool cannot generate or save an image in this worker, return `blocked`
with that capability gap. A prompt document is not a completed image.

Inspect the actual output against the references. Save `candidate.png` and
`continuity.json` inside the assigned output_dir. The continuity object contains:

```json
{
  "candidate_sha256": "SHA256_OF_CANDIDATE",
  "references": {"EXACT_SNAPSHOT_PATH_FROM_PACKET": "EXACT_SHA256_FROM_PACKET"},
  "checks": {
    "identity": "Specific likeness observations or defects",
    "costume": "Clothing, hair and age observations",
    "props_and_contact": "Hands, grips, rigid geometry, count and placement",
    "composition": "Camera, silhouettes, blocking and screen direction",
    "lighting": "Time of day, light direction and actual scene palette",
    "line_and_color": "Ink weight, hatching, painterly color and texture",
    "neighbor_continuity": "Comparison to the attached scene anchors",
    "script_fidelity": "Exact action and cast preserved; no invented elements"
  },
  "continuity": {
    "character_ids": [], "costume_ids": [], "prop_ids": [],
    "time": "Actual scene time/era", "location": "Actual scene location"
  }
}
```

The `references` mapping must contain every image snapshot in the packet, not
the prose documents. Fill continuity IDs with actual identified subjects.
Submit both files in the normal worker `result.json`. Evidence must describe
what you saw; mechanical file checks do not establish artistic consistency.

## Review and downstream use

The independent reviewer receives the same image references plus the candidate.
Reject material drift in likeness, costume, props, scene lighting or style.
The coordinator checks the candidate/report hashes and records the real creator
and reviewer thread IDs. Successful technical review registers the exact file
as `technical-approved`; it does not record Luis's author decision.

Luis's creative review uses the existing digest-bound asset workflow in
[ASSET_PIPELINE.md](ASSET_PIPELINE.md). Only after author approval and explicit
canonicalization can the image feed production video:

```bash
python -m studio demand video S01-01 \
  --out production/video-jobs/s01-01-v1 --frames 144
python -m studio video submit production/video-jobs/s01-01-v1
python -m studio video import production/video-jobs/s01-01-v1
python -m studio render production/video-jobs/s01-01-v1/imported/shot.json \
  --draft --out production/video-jobs/s01-01-v1/review.mp4
```

This uses the existing anonymous HF bridge and its no-retry/no-paid-fallback
behavior. Video submission is explicit, once per prepared job; interrupted jobs
are inspected rather than resubmitted. Shots longer than 14 seconds need authored
segment boundaries, not automatic cuts. Blender/FFmpeg/compositing stay local.
The resulting video still needs motion review, sound and final shot approval.

This is demand-driven production tooling, not a background schedule or a promise
of exact likeness. No image model can guarantee exact consistency from references;
specific review evidence and targeted new revisions are how drift is controlled.

CLI turn implementation follows [OpenAI's non-interactive mode documentation](https://learn.chatgpt.com/docs/non-interactive-mode).
