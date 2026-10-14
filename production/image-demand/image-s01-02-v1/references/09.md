# HERALDS OF THE CEMÍ — CANONICAL ART DIRECTION
## Artist lock: 2026-10-09 · Visual direction v2 · Luis M. Minier

### Source-of-truth precedence

1. **Author's original pencil portraits:** unique facial structure and artist signature. Angular/boxy organic construction, bold uneven eyebrows, soulful heavy-lidded eyes, specific noses, imperfect human asymmetry, hand-shaped curls and varied facial proportions.
2. **Author-approved illustrated series overview (provided in chat 2026-10-09; the full-color wide collage with Bronx skyline, amber sky, Jayc close-up, families, and 24 issue thumbnails):** **finish, materials, mark-making, cinematic palette and editorial mood reference**. Do not copy character faces, cover layouts or typography indiscriminately. Keep the original image locally as a reference; it is NOT an automatically approved LoRA training item.
3. **Option B — Moody Urban Dusk:** base lighting language: midnight/navy ink shadow, muted steel blue, charcoal, warm copper/amber streetlight and dusk skyline. Avoid monotone dull blue: luminous sunset amber and selective saturated blues/red accents are part of the reference.
4. **Author character bible:** canonical per-character build, hair, age, expression, costume, props and historical variants. Mood-board portraits may be look exploration, not identity canon until the author approves.

### What the finished frames LOOK like

- **Hand-inked graphic-novel animation**, not polished generic anime, not 3D, not a glossy vector cartoon and not unfinished graphite.
- Strong and irregular ink contour, visibly handmade confident brush/pen pressure, small broken contour edges; deliberate **hatching and crosshatching** are a signature texture, especially hair, fabric folds, face planes, masonry, rust and environmental wear. Deliberate pen marks are NOT the same as rough construction scribbles.
- Clean outer shape and readable silhouette despite richly textured interiors. Higher mark density near eyes/hair/hero focal point; simpler shadow masses in other areas to remain animatable.
- Defined geometric cheek/jaw/nose construction, large-but-grounded expressive eyes and uneven bold brows; 10–20% anime influence in facial acting, eyelids and lighting polish, NOT proportion homogenization.
- Dense grouped curls, locs and distinct hair masses with fine hand-inked strands; hair silhouettes must be character-specific, not automatically an enormous curly afro for everyone.
- **Full rich color** integrated with black linework: painterly watercolor/gouache-like color fields, print-grain/paper tooth where relevant, 2–3 cel-shading planes plus local fine ink texture, cinematic navy/orange light split.
- Atmospheric Bronx streets and buildings, elevated train, Santo Domingo architecture, Taíno river and forest history: grounded, detailed, lived-in, context-specific rather than stock sci-fi neon.
- Humans feel tired, grounded, resilient, Dominican/Afro-Caribbean, varied by character; do not lighten/darken skin pigment merely to match the color grade.

### Separate production compositions (do not confuse them)

**Mode CHARACTER_ASSET:** exactly one named character, full-body/front/side/back/expressions as requested; uncluttered neutral dark-slate or transparent background; no title, slogans, floating notes, typography, collage tiles or random crowns. Keep stable accessories. Crop complete hands and shoes inside frame.

**Mode ENVIRONMENT_PLATE:** no inserted character by default; cinematic textured buildings/landscape, layered for camera moves; no inexplicable graffiti lettering or motivational text.

**Mode STORY_FRAME:** only storyboard-required characters, poses, props and setting; blank speech bubbles only where comic scripting explicitly requests them; no generated dialogue text. Explicit signage may be composited accurately in post-production.

**Mode EDITORIAL_MOODBOARD:** issue headings, titles, captions and designed typography allowed **only if directly requested**. The reference overview uses typographic editorial design; that is not a rule to paint wall slogans into scenes.

### Exact generation prompt formulation

Positive prefix:
`cemistyle, in the original author's recognizable hand-drawn Cemí visual language, complete cinematic hand-inked 2D graphic-novel animation, organic angular/asymmetric facial design, bold expressive brows and grounded soulful eyes, individualized nose and jaw, textured confident variable-width black ink contours, intentionally controlled fine crosshatching and hair strands, nuanced graphic cel-shadows over warm richly colored painterly washes, ink/paper tooth, Caribbean/Bronx lived-in visual texture, Option B Moody Urban Dusk, deep navy and steel-blue shadow contrasted with atmospheric copper-amber dusk light, subtle mature anime influence in eyes and expressive acting`

Negative prefix:
`generic anime face, same face on all characters, slick vector gradients, smooth plastic 3d skin, doll eyes, photorealistic render, unfinished pencil construction marks, messy uncontrolled scribbles, monochrome sketch, washed-out flat coloring, text, letters, words, floating captions, promotional slogans, meaningless graffiti, wall writing, speech-bubble text, logos, watermarks, wrong body proportions, wrong hairstyle, extra fingers, mismatched eyes, duplicated limbs`

### Acceptance checks

- Does the scene resemble **the user's pencil-derived drawings PLUS the full-color illustrated overview**, or does it look like an unrelated model's anime?
- Does it have *intentional ink texture*? If all hatching disappears, FAIL. If outlines are lost under random scribble, FAIL.
- Are faces asymmetrically human, and clearly different between JC, Manny, Mikey, elders and children? If same-face, FAIL.
- Does the navy/steel/amber grade feel cinematic while skin remains accurate and accents vivid? If dull, FAIL.
- Are costume/build/hair/props correct against the author bible? Manny is tall, very broad, close-cropped hair; JC is lean with short curls and fade in the text, **unless the author explicitly locks a new adaptation**.
- Does any unnecessary wall lettering, quote, poster typography, or AI gibberish appear? FAIL.
- Is this a separate usable layer/character/frame, not a collage sheet when an asset was requested? FAIL.

### SDXL fine-tune/animation engineering implications

Do **not** train SDXL on the overview collage with its text and 24 cover thumbnails; it will learn unwanted lettering and multi-panel compositions. Manually crop multiple author-approved illustrations into single scenes, characters, textures and environmental views; caption by appearance and mark-making. Validate against held-out style tests **and** face/identity control tests. Use style LoRA for the mark-making/grade; separate approved face/body references, ControlNet poses or identity LoRAs for exact cast. For animation, reuse approved ink shapes and image layers, rig/animate, interpolate in-betweens then reapply ink/light without face flicker.

**Status:** visual contract, not proof of a trained model or accepted final artwork. Only author approval makes a generated frame canonical.
