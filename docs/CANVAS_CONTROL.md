# Full Canvas Control — shot-wide editor (experimental)

This is the **scene-level** editor, not the two-point sleeve/bell demonstration.

It operates on the existing `studio.engine.Compositor` used by the episode.
Select **any of the 128 shot specs** and work on the entire 2D canvas:
background and foreground plates, all character and prop layers, parented
objects, effects, exposure clocks, parallax and the camera path.

## Start in GitHub Codespaces

Use a working terminal whose current directory is the Ilan-Anime checkout:

```bash
pwd
python -m unittest tests.test_canvas_control -v
python -m studio canvas --host 0.0.0.0 --port 8766
```

Open the Codespaces **Ports** panel. Find port **8766**, ensure visibility is
**PRIVATE**, and choose **Open in Browser**. Do not expose this development
editor as a public Codespaces port. The browser UI runs from the local Python
server and renders the local repository's actual shot layers.

- Left: all shot IDs; search/filter and select a shot.
- Center: real composed image, always the **full frame**, with pan/zoom and
  shot-specific framing handled by the compositor. Scrub any frame.
- SVG outlines: transformed source bounds for **each active layer**, not a
  hand-placed debugging dot. Click a layer or drag an outline to adjust its
  whole-layer placement at the current frame. A bounding rectangle is NOT an
  alpha-accurate silhouette or collision result.
- Right: entire back-to-front layer stack and camera; select any layer, edit
  keyed X/Y, scale, angle, opacity, base opacity, or parallax. Reorder stack.
  Character scaling/rotation is deliberately blocked: replacement drawings
  are required for new acting.
- **Audit this shot** samples transformed layer bounds through time, records
  off-canvas/partially clipped layers, and invokes the existing
  `studio.qa.acting_flags` check. Does NOT certify anatomy, overlap, pixels,
  flicker or animation quality.
- **Audit all shots** inspects **every saved episode shot spec** for missing
  source files and presence/absence of multi-drawing character layers. It is
  a structural inventory, not completed-shot approval.
- **Save NEW draft take** writes the updated, renderable spec to
  `production/engineering/canvas-takes/<SHOT>-canvas-<time>-<nonce>/`,
  alongside `edits.json` and `canvas-audit.json`. Existing source images
  and source shot specs are never overwritten or marked approved.

## Relationship to the minimum-separation solver

The engine's `studio.drawing.separation` solver can still correct **named
Bézier control points in editable drawing IR**. The canvas editor works one
level higher, on whole-shot layers, camera, exposure clocks and composition.
Do not confuse moving a transform key with painting a new character pose.

## Production limitations

The tool does not automatically infer all bone joints, reconstruct an arm
that has no source drawing, preserve ink if a raster is arbitrarily warped,
or guarantee 128 completed shots. The renderable shot editor and broad
inventory are engineering infrastructure. Real art-production completion
still needs valid replacement poses, contacts, independent visual review,
source-quality checks, and exact-file author approval.

The new browser preview renders drafts at half resolution for responsiveness,
without cropping the authored full frame. Final output still goes through
`python -m studio render` with the saved draft spec. The editor doesn't
change paid-generation policy.

## Regression

```bash
python -m unittest tests.test_canvas_control tests.test_drawing_separation tests.test_drawing_sequence -v
python -m unittest discover -s tests -v
```

If these fail, keep the PR in draft; don't merge on the strength of an
illustrative front-end alone.
