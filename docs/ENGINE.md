# Shot engine spec (v2)

`studio.engine` renders one shot from JSON. Every frame is a pure function of its integer frame number. v1 specs (the old `compose.py` format) still load.

```json
{
  "id": "S01-11", "size": [1280, 720], "frames": 240, "status": "exploratory",
  "background": [20, 32, 43, 255],
  "layers": [
    {"name": "river", "source": "assets/bg/river_clean.png", "fit": "cover", "rate": 1, "parallax": 0.6, "tags": ["bg"]},
    {"name": "hull", "source": "cels/hull.png", "rate": 2, "pivot": [400, 90],
     "keys": [{"frame": 0, "x": 0, "y": 0, "ease": "smooth"}, {"frame": 239, "x": 36, "y": 0}]},
    {"name": "beheto", "parent": "hull", "rate": 2, "tags": ["character"],
     "exposures": [{"start": 0, "end": 12, "source": "cels/beheto_hover.png"},
                   {"start": 12, "end": 18, "source": "cels/beheto_contact.png"}]},
    {"name": "wake", "sequence": ["fx/wake_01.png", "fx/wake_02.png", "fx/wake_03.png"], "loop": true, "rate": 2},
    {"name": "roots", "source": "assets/cels/foreground_roots.png", "fit": "stretch", "rate": 3, "parallax": 1.3},
    {"name": "super", "generator": {"type": "text", "text": ["BEFORE"]}, "screen_space": true, "rate": 3}
  ],
  "camera": [{"frame": 0, "scale": 1.0, "ease": "smooth"}, {"frame": 239, "scale": 1.05}],
  "shake": [{"start": 100, "end": 104, "amp": 6}],
  "post": {"grade": "before", "grain": 0.35, "weave": 0.3, "chroma": 0.3, "vignette": 0.4}
}
```

## Layers (back to front)

| Field | Meaning |
|---|---|
| `source` / `sequence` / `exposures` / `generator` | One held drawing; a cycle (`loop`); explicit `[start, end)` drawings on the layer clock; or a procedural FX layer. |
| `rate` | Drawing clock: on 1s, 2s, 3s… Drawings and layer keys change only on this grid; `smooth: true` evaluates keys every frame. |
| `in` / `out` | Layer active range in shot frames. |
| `keys` | `x`, `y`, `scale`, `angle` (degrees, counter-clockwise), `opacity`; `ease`: linear, smooth, ease_in, ease_out, hold. `x`/`y` place the unscaled image's top-left; scale and rotation happen about `pivot` (source pixels, default centre). Rotated cutouts are never clipped. |
| `parent` | Inherit another layer's transform (passengers in the hull, clapper in the bell). Child coordinates are in the parent's image space. |
| `parallax` | Camera multiplier: 0 = fixed to screen, 1 = moves with the camera, >1 foreground, <1 distant plates. `screen_space: true` sets 0. |
| `fit` | `none`, `stretch`, `cover`, `contain` (applied once at load). |
| `blend` | `normal`, `add`, `screen`, `multiply`, `lighten`. |
| `tags` | `bg`, `character`, `line`, `shade`, `highlight`: PRESS uses these to change drawing style. |
| `effects` | `transmitted_light` (darken below + additive cel + airbrushed halo), `light_figure` (rim from alpha edge), `glow`. |

## Generators

`sigil` (spiral opening into a triangle, drawn on over `draw_frames`), `text` (tracked serif caps; `reveal_frames` for type-on; drop the cover face into `projects/cemi_episode_01/assets/fonts/cover_serif.ttf`), `slate`, `speed_lines` (2-drawing loop), `train_strobe`, `ring` (shockwave cels), `lanes` (LANE_FIELD), `phone` (chat bubbles typed on), `solid`, `gradient`.

## Camera and post

`camera` keys: `x`, `y`, `scale`, `angle`, evaluated every frame and folded into each layer's single resample. `shake`: random walk snapping on 2s.

`post` values are scalars or `[{"frame", "value"}]` keys:

| Key | Effect |
|---|---|
| `grade` | `present`, `before`, `1934`, `1957`, `1973`, `flashback`, `classroom`, `sodium`; or keys `[{"frame", "grade", "blend": 24}]` for WIPE_ERA. |
| `press` | PRESS 0–1: depth collapses (parallax), saturation ×(1−0.85p), shade cels gone by .3, highlights by .6, line layers unify at ≥.6, `bg` layers become a flat gradient at ≥.6, character drawings slow to 6s at ≥.8. |
| `grain`, `weave`, `chroma`, `halation`, `vignette`, `saturation` | Film transfer: 24 baked grain plates; gate weave under 1.5 Hz; edge-weighted chroma bleed; bright-area orange bleed. |
| `harmony` | `[{"start", "end", "dissolve"}]`: freeze, 3-tone pastel posterize, hatching, cream border. |
| `flash` | `[{"frame", "frames", "mode": "white"|"invert"}]`. |
| `fade` | `[{"start", "end", "to": "black"|"white"|"navy"|"cream", "dir": "out"|"in"}]`. |
| `double_exposure` | `[{"start", "end", "source", "opacity"}]`. |
| `heat_shimmer` | `[{"start", "end", "strength", "region": [x, y, w, h]}]`. |

## Output

`studio render`: `.mp4` review (H.264, BT.709-tagged), `.mkv` lossless FFV1 master, or a directory of PNGs. `quality: draft` uses bilinear resampling; finals use bicubic. `render_scale` (or `Compositor(scale=…)`) renders a proportionally smaller preview from the same spec.
