# General minimum-separation constraint for drawing and animation

This tool implements the requested signed midpoint-preserving pair correction:

```text
delta = max(0, m - (u - l))
u' = u + delta / 2
l' = l - delta / 2
```

In two dimensions, define an **oriented unit axis** `a` from the lower
control point toward the upper. Measure `g = dot(U-L, a)` and compute:

```text
delta = max(0, m - g)
U' = U + delta * a / 2
L' = L - delta * a / 2
```

In image coordinates, Y grows downward, so an ordinary upper/lower vertical
pair uses **`axis: [0, -1]`**. If both points already satisfy the gap,
the correction is zero. Their midpoint is preserved. The kernel does not infer
which two points should be paired and is not a drawing/animation generator.

## Available uses, across the entire studio

- **Draft drawing IR:** supply `separation_constraints` on any new
  `studio/drawing` IR with references to Bézier control points. The shared
  raster and SVG renderer applies the correction automatically. Endpoints
  repeated within the same primitive are moved together, preserving curve
  continuity. Invalid or unsafe corrections raise an error.
- **Explicit tool call:** `python -m studio.drawing constrain --input
  input.drawing.json --rules rules.json --out new-empty-take` writes the
  corrected IR, SVG, preview PNG and audit report to a new directory.
  The input and existing artwork are never overwritten.
- **Animation QA:** add `separation_constraints` to an element of a motion
  specification, with `upper` and `lower` names matching that element's
  named drawing/pose points. `studio.motion.check` rejects insufficient
  separation for each drawing. It NEVER silently edits approved poses.

## Example drawing rule

```json
{
  "upper": {"id": "fabric.panel", "segment": 0, "point": 1},
  "lower": {"id": "fabric.panel", "segment": 1, "point": 2},
  "minimum": 8,
  "axis": [0, -1]
}
```

This works for any curve in the IR: eyelids, clothing gaps, arm/wrist silhouette
clearance, prop spacing and effects boundaries. It applies to specifically
named point pairs only, not every possible boundary intersection.

## Example motion rule

```json
{
  "name": "amaia-cloth",
  "kind": "character",
  "poses": [{
    "frame": 0,
    "drawing": "pose-000.png",
    "points": {"hem.upper": [215, 340], "hem.lower": [215, 345]}
  }],
  "separation_constraints": [{
    "upper": "hem.upper",
    "lower": "hem.lower",
    "minimum": 9,
    "axis": [0, -1]
  }]
}
```

Motion QA reports a violation of **4 pixels**. To repair it, edit a *new draft*
drawing with the correction tool and update the pose asset. Never relabel
changes to a fixed authored drawing as a new pose.

## Constraints and exclusions

- **Opt-in only.** Existing drawings and shots without constraints behave as
  before. Neither original raster artworks nor approved assets are modified.
- **No invented anatomy.** The method ensures scalar spacing, not believable
  geometry, style, occlusion, rig contact or acting. Interdependent constraints
  may need a global solver; they should not be automatically projected in
  arbitrary order.
- **No proof of creative quality.** The tool provides deterministic numerical
  correction and motion validation. Independent visual review and exact-asset
  author approval are still required.
- A new fixed drawing is **exploratory** until approved. A non-destructive,
  provenance-recorded take is mandatory for the CLI path.

Tests: `python -m unittest tests.test_drawing_separation -v`.


## Frame-by-frame sequence integration (experimental)

The native tool now accepts a manifest containing existing *frame-local drawing IR*
files and a common list of explicit point-pair rules. It checks and corrects
each frame independently, preserves source files, validates pair midpoint and
gap after correction, and writes new registered RGBA drawings.

Run an existing, **unapproved** drawing sequence:

```bash
.venv/bin/python -m studio.drawing sequence \
  --manifest production/engineering/my-sequence/sequence.json \
  --out production/engineering/drawing-takes/SEPARATION-REAL-001
```

Minimal manifest:

```json
{
  "fps": 24,
  "source_kind": "production-draft",
  "frames": [
    {"drawing": "pose-0000.drawing.json"},
    {"drawing": "pose-0001.drawing.json"}
  ],
  "rules": [{
    "upper": {"id": "cloth.sleeve", "segment": 0, "point": 1},
    "lower": {"id": "cloth.sleeve", "segment": 2, "point": 2},
    "minimum": 28,
    "axis": [0, -1]
  }]
}
```

The optional synthetic demonstration generates 48 *new*, deliberately
collapsing sleeve test frames (not from Amaia or any approved shot):

```bash
.venv/bin/python -m studio.drawing.sequence_fixture \
  --out production/engineering/drawing-takes/SEPARATION-DEMO-001
```

Files: `before.mp4`, `after.mp4`, `comparison.mp4`,
`before-motion.json`, `after-motion.json`, `measurement.png`,
`report.json`, per-frame PNGs and `corrected_ir/*.drawing.json`.
`studio.motion.compile_spec` must reject the uncorrected motion spec
and accept the corrected one when all named-point clearances pass.

Demonstration run (48 frames, 24 fps, minimum 28 px):
**38/48 violating frames before, 0/48 afterward;**
maximum required gap correction 18.3317 px; maximum
frame-to-frame change in the gap correction 1.33361 px.
These are deterministic *synthetic-test* measurements. They do not
establish correct character anatomy, rendered stroke quality, identity
preservation or author approval.

**Actual Amaia movement is not yet demonstrated.** The latest existing Amaia
rig's articulated arm movement was previously rejected for doubled source
contours; its accepted scope was restricted to neutral body plus face
controls. Never use that rejected movement as an approved input. A real
character test requires newly approved/action-specific replacement drawings
and actual per-frame/pose correspondence points.
