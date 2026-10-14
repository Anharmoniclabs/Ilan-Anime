---
name: blender-npr-3d-anime
description: "Make 3D in Blender read as hand-drawn 2D anime (EEVEE NPR): setup, cel shading, lighting, normal editing, rigging, stepped animation, painterly environments, Grease Pencil, line art, VFX, rendering. Use for any Blender shot, prop, environment or render in this repo, and to review footage for 3D-look failures before it reaches the studio engine."
---

# Blender NPR 3D anime

Working rules for 3D that must look 2D, plus how Blender output enters this repo's pipeline. Read `production/WORKER_CONTRACT.md` first when dispatched as a worker.

Source: Noggi's course "EVERYTHING About Creating Beautiful 3D Anime (Blender + DaVinci Resolve)" (Feb 2026) and its course page. The principles, setup and art-style sections were distilled from the transcript. Topic sections follow the course's chapter structure plus standard EEVEE NPR practice: strong defaults, verify against reference footage. Version-specific settings below were checked against Blender's own behavior, not the course.

## Where 3D fits Heralds of the Cemí

3D is a tool for things drawings keep getting wrong. It does not replace Luis's drawings.

| Use 3D for | Why |
|---|---|
| Rigid props: canoe hulls, drum, paddles, bell and a **separate clapper** | They must never drift or flex (the rejected mesh tests failed exactly here; the Beheto atlas drum moves 4–17 px between poses). |
| Perspective and multiplane blocking: mangrove tunnel (S01-09 MULTIPLANE_RUSH), ballroom, reading room | Correct depth and parallax, then paint over. |
| Camera moves over sets: crane, roll, dolly zoom | Exact geometry under the move. |
| Background crowd banks (Echo LIGHT_FIGURE cycles) | 3–4 stepped cycles reused across a crowd. |
| Water wakes, rings, splinters as 3D VFX flattened to cel steps | Consistent timing, drawn look. |

Characters in 3D only after Luis decides the character style question (cel-separable line/flat/shadow layers vs fully rendered paintings). Identity always comes from his pencil portraits and character bible (`production/art_direction.json` tier 1 and 4). A 3D character that "looks good" but doesn't match those is a fail.

Cemí style targets that change the generic advice below:

- Line: confident, irregular, variable-width ink with controlled broken edges. Never a uniform outline.
- Shading: two or three cel planes (lit, shadow, optional deep shadow) with navy/steel shadows and amber/copper light where the scene's actual light falls. Moonless BEFORE stays moonless.
- Texture: paper tooth, painterly wash and controlled crosshatching. On anything that moves, these are **locked textures** applied in compositing inside a shadow mask, never regenerated per frame, or they boil.
- Environments painterly; characters flatter. Do not shade them the same way.

## Core NPR principles

1. NPR follows the world you envision; PBR simulates reality. Every choice below serves the imagined look.
2. The camera view is king. Cheat, break and deform anything off-camera. Judge only the render.
3. 3D is too perfect. Add irregular line weight, slight asymmetry and off-register edges on purpose.
4. Extreme poses are authored per pose: a mesh shaped or swapped for one stepped key is a new drawing. Warping a finished *image* (the rejected Cemí mesh tests) is not.
5. The target is a 3D model that looks 2D, not a 2D model in 3D. Final-look references drive modeling.

## Blender setup

| Setting | Value | Notes |
|---|---|---|
| Version | 4.2 LTS or newer; Goo Engine (community NPR fork) if you need its extra nodes | Check Goo Engine's current distribution terms. EEVEE changed in 4.2 ("EEVEE Next"); settings below say which version they apply to. |
| Engine | EEVEE | The toon shading core, **Shader to RGB**, exists only in EEVEE. Cycles has no equivalent. Its Python identifier has been `BLENDER_EEVEE` or `BLENDER_EEVEE_NEXT` depending on the release; `studio/blender_npr_setup.py` tries both. |
| Color management | View transform **Standard**, look None | AgX (default since 4.0) and Filmic re-map your colors. |
| Frame rate | 24 fps, `fps_base` 1 | Nothing else. |
| Resolution | The shot canvas: 1280×720 for this episode (never above 1920×1080) | Older-anime softness: render low, upscale after. |
| Motion blur | Off | 4.2+: `render.use_motion_blur`; older: `eevee.use_motion_blur`. Smears are authored. |
| Film | Transparent for element layers | So the studio engine can composite them. |
| Shadows | Legacy EEVEE: cascade size 4096. EEVEE Next: no cascade setting; raise shadow resolution / lower light resolution limit; jittered soft shadows off | Engine shadows are usually replaced by authored shadow shapes anyway. |
| Ambient occlusion | Legacy: enable AO to expose it to shaders. EEVEE Next: the toggle is gone; the AO node still works | Multiply AO into the shadow band for contact darkening. |
| Passes | Combined, Z, Cryptomatte object + material | For mattes and shadow edits. |
| Line art | Grease Pencil **Line Art** modifier (built-in) and/or Freestyle (built-in). Pencil+ is a paid third-party add-on | See topic 9. |

`python -m studio blender render` applies everything in this table except the shading itself.

## Reading a target style

An art style is the set of rules that keep images consistent: color, shape, shading, anatomy, layout, line. Reverse-engineer it before modeling.

Design: hard cel boundaries, no gradients on characters; line art everywhere (uniform or deliberately varied); near-real body anatomy with stylized faces; simpler drawing under speed and distance (swap simpler models for fast or far shots); exaggerated poses and expressions.

Animation: limited animation on 1s, 2s or 3s, with background elements as slow as 4s; mixed rates inside one shot (focus character on 2s, background on 4s, camera on 1s); animate only what matters; smears instead of motion blur.

Production quirks to imitate, not fix: flat cloth patterns that don't perspective-correct; small artist inconsistencies (a strand flipping in front of an eye); characters flat and environments painterly; native resolution of the era.

## 1. Characters and modeling

- References first: neutral full-body front and side, ideally a 3/4 placed in the scene. Ground contact at the heel; 2D feet are often drawn slanted.
- Sculpt then retopologize for organic proportion, or poly-model for controllable animation topology. Pick per asset.
- Keep deformation loops (shoulders, elbows, hips, mouth, eyes). Stylize the silhouette and face, not the deformation structure.
- Model for the camera: cheat proportions, delete what never shows, split meshes where flattening needs it.

## 2. Shading (most of the look)

- Shader to RGB → Color Ramp (Constant interpolation) quantizes light into flat bands. Where the boundary falls matters more than the colors.
- Lit and shadow colors are chosen values per material, never the physical result. For Cemí: shadow ramps toward navy/steel, light toward amber only where a lit source exists.
- Layer weight / normal-based rim lights, per-material shadow tints, backface tricks for double-sided cloth, AO multiplied into the shadow band.
- Speculars as drawn shapes; painted gradient maps; per-material light-response overrides.

## 3. Lighting

- One key sun plus few, intentional fills. Soft area lights fight the flat look.
- Light linking (Cycles 4.0+, EEVEE 4.2+) or separate view layers so characters and environments are lit and styled independently.
- Shadows: author them (normal edits, painted shapes) or edit engine shadows with Cryptomatte/Z in compositing. Soft physical shadows read as 3D.

## 4. Normal editing

Bend normals (data transfer from a proxy shape, Normal Edit modifier, geometry nodes) so the terminator lands where a drawing would put it, and stays put while the head turns. Use it for face shadow shapes, hair shadow masses and rim placement.

## 5. Rigging

Standard armature and weights are enough for most shots. Add only what the shot needs: separate hair/cloth controls, pose-swap or shape-key slots for smears and alternate meshes, a 2D-expression face rig, and controls that break proportion on purpose. Rigid props get bone parents, never deformation.

## 6. Animation

- Pose to pose with strong silhouettes. Characters on stepped keys: Constant interpolation or a **Stepped** F-curve modifier at the shot's drawing rate. Camera and environment may move on 1s.
- Reuse the common shot grammar: slow push-ins, held frames with wind/flicker overlays, impact frames and smears, speed lines, eye close-ups, dust bursts.
- The defining failure: everything on 1s with smooth interpolation. `studio blender check` catches it.

## 7. Environments

Block in 3D for perspective, then paint over or texture painterly. Painterly for most scenes; cel-shaded only where the set interacts with character animation. Hand paint-over for hero shots; procedural texturing and geometry-node scattering for mid and far ground. Prefer add-ons whose output stays editable.

## 8. Grease Pencil

2D drawing inside 3D: corrections, smears, effects, full hand-drawn passes over a render. One GP layer per element (hair, impact, FX); use modifiers (offset, noise, build) instead of redrawing. GP instances along curves repeat grass, fire, rain. GP changed data model in 4.3 (GPv3); check modifier names in your version.

## 9. Line art

| Method | Strength | Cost |
|---|---|---|
| Material/shader lines (fresnel, layer weight) | Per-object control, cheap | Interior lines limited |
| Inverted hull (solidify, flipped normals, back-face culling) | Classic outline, thickness per vertex group | Silhouette only |
| Line Art GP modifier / Freestyle | Creases, intersections, per-collection rules | Slower; needs taper and noise to stop looking vector |
| Hand-drawn GP | Most drawn feel | Most labor |

Combine: hull or Line Art for characters and props, shader lines for detail, then vary weight, taper and break edges (vertex-group thickness, noise, geometry nodes). Perfectly even lines read as vector. For Cemí, line weight must vary and edges must break in places.

## 10. VFX

GP VFX (smoke, fire, impact stars, speed lines) match natively. 3D VFX (water, splinters, explosions) get flattened to cel steps and lines. Repeating effects become stepped cycles (wakes on 2s), not per-frame simulation.

## 11. Rendering into this repo

The studio engine composites, grades and adds the film finish. Blender's job is clean, registered element layers.

1. One view layer or collection per element (hull, drum, beheto, paddle_lead, wake, fg_roots). Render each as an RGBA PNG sequence at the shot canvas with transparent film.
2. Pick who owns the camera. **Blender camera:** import layers with `screen_space` (parallax 0) and leave the shot spec's camera empty. **Engine camera:** render from a locked camera and let the spec's camera and parallax move the layers. Never both.
3. Render through the setup script so settings and stepping are applied the same way every time:
   `python -m studio blender render scene.blend --out renders/blender/S01-11 --frames 0-239 --step 2 --layers hull,drum,beheto`
4. Check the steps, then import as exposures (identical consecutive frames become holds):
   `python -m studio blender check renders/blender/S01-11/beheto --step 2`
   `python -m studio blender import renders/blender/S01-11/beheto --name beheto --rate 2 --tags character --out .../beheto.layer.json`
5. Put the imported layers into a motion spec (`kind: rigid` for props, `character` for figures) or a shot spec, then `studio motion check`, `studio render --draft`, `studio qa`.

Rendered elements are `exploratory` like any other asset until reviewed and approved by Luis.

## 12. Compositing

The course does this in DaVinci Resolve; here the studio engine post stack covers it (`docs/ENGINE.md`):

| Resolve technique | Studio equivalent |
|---|---|
| Flat grade, then rebuild stylization in layers | Element layers + `grade` presets per register (present, BEFORE, 1934, 1957, 1973) |
| Shadow tinting via Cryptomatte | Render a shadow-mask layer; composite with `multiply` |
| Glows on speculars and lamps | `glow` layer effect, `halation` |
| Grain, screen dirt, chroma softness | `grain` (baked plates), `weave`, `chroma` |
| Speed lines, impact flashes, smear overlays | `speed_lines` generator, `flash`, drawn smear cels |
| Flat pattern textures that ignore cloth perspective | A locked texture layer clipped to the cloth's matte |

## 13. Export

24 fps, native canvas, no re-encode chains (FFV1 masters, H.264 review copies). Watch at speed and frame-step before sign-off.

## Quality gates before a 3D element counts as "2D"

- [ ] 24 fps; characters stepped on 2s/3s (`studio blender check` passes); camera may be on 1s.
- [ ] No motion blur; smears authored.
- [ ] Hard cel boundaries with two or three planes; no smooth gradients on characters.
- [ ] Line weight varies and breaks; nothing mathematically even.
- [ ] Characters and environments visibly differ in treatment.
- [ ] Unimportant elements hold still.
- [ ] Rigid props stay rigid (`studio qa` lock regions show no drift beyond camera motion).
- [ ] Identity matches Luis's references, not "good anime".
- [ ] Judged on the rendered image at speed and frame-stepped, never the viewport or a single still.

## Sources

- Course video: https://www.youtube.com/watch?v=xZWxEoa-Dwk (Noggi, Feb 2026)
- Course page and resources: https://noggi3d.notion.site/3d-anime-guide
