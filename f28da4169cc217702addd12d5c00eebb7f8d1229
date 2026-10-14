# Camera tooling

`camera_motion.py` adds camera movement to existing video, including the output of `cel_animation.py`. It uses local Python and FFmpeg. It does not call an image or video generation service or change the source drawings.

## Use from this conversation

Ask for a push-in, a tracking pan, a pull-back, a rise, or a specific sequence of camera beats. The assistant can write a camera timeline and render it here without a browser server or GPU. Camera files are separate from the drawing exposure sheets so a shot can be reframed without regenerating artwork.

Create a starting track:

```bash
python camera_motion.py preset pan-right \
  --source cel-demo/dairon-refined-source/animation.mp4 \
  --save my-camera.json
python camera_motion.py render my-camera.json --out camera-take-01
```

Available presets: `locked`, `push-in`, `pull-back`, `pan-left`, `pan-right`, `rise`.

Render the supplied Dairon tooling demonstration:

```bash
python camera_motion.py render cel-demo/camera-test.json --out camera-preview
```

The supplied `camera-test.json` uses restrained framing and clean cuts. `cel-demo/camera-test-dissolves.json` keeps a second demonstration with short cross-dissolves and larger moves. The existing Dairon artwork fills much of the canvas, so larger zooms/pans can crop limbs or the paddle even while the camera stays inside the artwork.

## Timeline format

```json
{
  "fps": 60,
  "size": [1280, 720],
  "shots": [
    {
      "name": "Push toward the character",
      "source": "animation.mp4",
      "start": 0,
      "duration": 2,
      "camera": [
        {"at": 0, "x": 0.5, "y": 0.5, "zoom": 1, "ease": "smoother"},
        {"at": 0.4, "x": 0.5, "y": 0.48, "zoom": 1.12, "ease": "linear"},
        {"at": 1, "x": 0.52, "y": 0.48, "zoom": 1.16}
      ]
    }
  ]
}
```

- Source paths are relative to the timeline JSON. `start` and `duration` trim seconds from the source; duration defaults to the remaining video.
- `at` is progress through the shot: 0 is its first rendered frame, 1 is its last. Keys must increase strictly and include both endpoints.
- `x` and `y` are normalized camera centers: 0 is left/top, 1 is right/bottom. Defaults are 0.5. Increasing x tracks the camera right and makes the image move left.
- `zoom` is a magnification of at least 1. A value of 1 shows the full frame. Panning requires some zoom or a wider source plate; at zoom=1, the camera center is constrained to 0.5.
- `ease` belongs to the outgoing segment. Choose `linear`, `smooth` (cubic), `smoother` (quintic), `ease-in`, `ease-out`, or `hold`. The default is `smoother`, which starts and ends with zero velocity/acceleration. `hold` deliberately creates a camera cut at the following key.
- Camera centers are constrained so the crop never crosses the source canvas. Clamping is reported; it can flatten movement near the edge. These limits prevent empty borders, not clipping of a character or prop. Frame the subject intentionally.
- Aspect ratios must match by default. Explicit `fit: "cover"` permits cropping to match the output; `fit: "contain"` permits letterboxing. Camera coordinates refer to the fitted canvas.

The camera updates every output frame independently of cel exposure. A character animated on twos still uses those same drawings while the camera can move at 60 fps. This does not interpolate character anatomy or create in-between poses.

## Edits and resolution

Each shot after the first can have a transition **into that shot**:

```json
"transition": {"type": "dissolve", "seconds": 0.2}
```

Supported transitions: `cut` (default), `dissolve`, `fade-black`. Overlap durations are rounded to whole output frames and reduce the final timeline length. Overlapping transitions or trims beyond the source are rejected.

Use `--quality draft`, `--quality preview`, `--quality hd`, or `--quality 4k` to override size with 640×360, 1280×720, 1920×1080, or 3840×2160. Output frame rates are 24, 30 or 60. Larger exports enlarge existing artwork; they do not create native 4K drawing detail. Preview/HD camera crops use spatial oversampling to reduce pixel stepping. 4K uses its output resolution as the working canvas to bound memory use.

Outputs are silent picture edits; source audio is currently omitted and reported. This version does not provide layered parallax, 3D orbiting, automatic subject tracking, optical-flow interpolation or an interactive camera editor.

## Outputs and verification

Every new output directory contains:

- `camera.mp4`: rendered camera/edit timeline.
- `shots/`: individual camera passes and their exact FFmpeg filter expressions.
- `camera-samples.csv`: per-frame camera position, zoom and clamp status.
- `camera-manifest.json`: frame counts, source hashes, trim and transition details.
- `source-spec.json`: input timeline.
- `poster.png`: first output frame.

Existing output directories are never overwritten. A build is published only after output dimensions and frame count match the planned timeline. Inputs are read-only. Tests inspect actual rendered motion of a stationary marker, mixed cut/dissolve duration, 4K output, crop bounds, keyframe timing and validation:

```bash
python -m unittest -v test_camera_motion.py
```

## Protected scene framing

For the river opening, shots can now specify `protected: [[x, y, width, height]]`
in normalized source coordinates. The renderer checks every output camera sample
and rejects any track that clips those bounds. This requires `fit: match`, which
now preserves the full image with padding for minor aspect-ratio differences.
`fit: cover` remains an explicit crop choice. Registered cel-region composition
is available in `locked_scene.py`; see `river-opening/README.md` for the example.

