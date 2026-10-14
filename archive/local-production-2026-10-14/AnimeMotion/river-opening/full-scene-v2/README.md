# Full-scene redraw — first motion pass

`preview-loop.mp4` repeats the 1.5-second motion test three times for review.
`take-01/animation.mp4` contains one pass: 12 distinct full-scene drawings,
36 exposure frames, 24 fps, 1280×720. Held drawings are intentional; this is the
same exposure-sheet assembly approach used in the earlier jump test.

All accepted source images are complete frames in `frames/`. There are no pasted
rectangular animation regions, masks, optical-flow frames or camera transforms
in this pass. The paddlers' arms and torsos, paddles, hair, wakes and water change
across the scene. The eleven occupants remain visible in the accepted drawings.
Passengers' acting remains subtle and needs a stronger animation pass.

This is an initial motion test, not the finished opening scene. Remaining review:
stroke spacing and grip continuity, consistent paddle length, canoe contour drift,
background texture flicker and convincing passenger counterbalance. It is not a
claim that all character anatomy or every transition is production-ready.

The two attempted multi-frame sheets dropped or shrank Yara and were rejected.
A cropped-paddle frame and detached-grip in-between were also rejected and replaced.
Those files remain in `rejected/` for traceability; none is used in the video.

The full-frame art was generated with the built-in imagegen tool. Exact prompts
are in `prompts.json`; drawing order and exposures are in `sequence.json`.
Full-resolution original drawings remain available separately from the preview.

To assemble another take, run from AnimeMotion:

```bash
python cel_animation.py river-opening/full-scene-v2/sequence.json --out river-opening/full-scene-v2/take-02
```
