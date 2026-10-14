> Current preview: [1990s cel-anime river travel](vintage-90s/README.md). The earlier exports described below are superseded.

# River opening

Source: `Heralds-of-the-Cemi-Final-1.pdf`, PDF pages 11–12, “BEFORE”.
The supplied asset pack provides two finished compositions. This proof adapts the
opening before the brass bell: 8 seconds of the three canoes, then 9 seconds of
Amaia holding her sleeping son. Timing and animation are adaptation choices.

## Watch

- `opening-HD/camera.mp4`: 1920×1080, 60 fps, 17 seconds.
- `opening-4K/camera.mp4`: 3840×2160, 60 fps, upscaled delivery.
- `review.html`: local player with shot navigation and frame stepping.

This is a **silent limited-animation proof**. Dairon has 12 generated paddle
drawings, exposed at 12 drawings per second. Amaia has two registered blink
variations over the supplied open eyes. Water has a small displacement animation.
Other passengers retain their supplied poses. These are not 1,020 independently
drawn frames, full-body sakuga, or a Sora model running locally.

## Proportion and placement controls

`../locked_scene.py` composites cels inside fixed source-pixel rectangles. It
rejects overlapping regions, out-of-canvas placements, mismatched cel dimensions
and per-region scale/translation settings. Sheet extraction preserves aspect ratio;
it rejects incompatible proportions. Masks further restrict Dairon's movement
away from Yara and limit Amaia's changes to her eyelids. There are no model-sheet
images pasted into the scene. Background/subject pixels outside the reviewed
regions stay on the original plate, prior to video compression and camera motion.

`../camera_motion.py` now accepts normalized `protected: [[x,y,w,h], ...]` subject
bounds per shot. Every output-frame camera sample must contain those bounds or
the render fails. `fit: match` preserves aspect ratio and pads tiny differences;
only explicit `fit: cover` crops for aspect ratio. The opening uses one shared
camera for all scene content. K01 has a 0.8% push; K02 is locked.

These checks prevent layout mistakes, not anatomical inconsistencies within a
generated drawing. The Dairon cycle remains a proof and may need hand cleanup
before final production. Pixel containment does not imply every passenger has
been animated.

## Reproduce or extend

From the AnimeMotion folder:

```bash
python river-opening/build_opening.py
python locked_scene.py river-opening/shot-01.json --out river-opening/new-shot-01
python locked_scene.py river-opening/shot-02.json --out river-opening/new-shot-02
```

Point `opening-camera.json` at the new shot directories, then:

```bash
python camera_motion.py render river-opening/opening-camera.json --out river-opening/new-HD --quality hd
python camera_motion.py render river-opening/opening-camera.json --out river-opening/new-4K --quality 4k
python -m unittest discover -p 'test_*.py'
```

Output directories must be new. Original pack images are preserved with hashes in
`asset-manifest.json`. Exact imagegen prompts are in `generation-prompts.json`;
generated sheets and registered cels remain available. Shot manifests record the
source hashes and cel drawings; timeline JSON records every exposure. The compositor
caches alpha masks and the water loop to reduce rendering cost on this machine.

All image generation used the built-in imagegen tool. Composition, timing, masking,
camera motion and video encoding run locally with Python and FFmpeg.
