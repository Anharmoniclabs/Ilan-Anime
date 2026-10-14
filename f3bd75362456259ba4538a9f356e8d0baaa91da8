# Current direction: 1990s cel-anime river travel

Watch `take-01/animation.mp4` for the eight-second update.

The current pass uses a new transparent, quiet fleet cel with simplified shadows
and restrained poses. The earlier vigorous paddle drawings are excluded. All
eleven passengers and three hulls stay together at fixed relative scale. The
original empty painted river is a separate background layer.

Movement at 1280×720, 24 fps:

- Canoes travel 220 pixels in world coordinates.
- The tracking camera moves 104 pixels in the same direction.
- The boats therefore advance 116 pixels across the screen while the bank passes.
- The fleet gently rises and falls by up to 2.5 pixels.
- The water surface ripples; the narrow waterline foam moves with the boats.
- A small amount of luminance grain softens the digital finish.

`take-01/motion.csv` records the camera and boat positions for every frame.
The compositor works at twice the delivery size to reduce position stepping.
Character proportions are not animated or stretched by the compositor.

This is a travel/staging pass with **held character poses**. The three canoes
share one layer; they do not yet rock independently. The waterline foam is held
with that cel, while the river surface beneath it changes. Character acting and
independent wake drawings remain separate work, not features claimed here.

Style decisions are recorded in `STYLE.json`. The new cel was created with the
built-in imagegen tool; prompts are in `generation-prompts.json`. The transparent
source is `assets/fleet-cel.png`. The previous studies remain separate historical
files and are not inputs to this render.

From AnimeMotion:

```bash
python vintage_motion.py river-opening/vintage-90s/shot.json --out river-opening/vintage-90s/take-02
python -m unittest test_vintage_motion
```
