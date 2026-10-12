# The Cemí 10/10 studio standard

“10/10” is a release standard, not a label attached to generated work. A department, shot, or episode passes only when every applicable gate below has specific evidence and the final creative gate is approved by Luis M. Minier.

| Gate | Required evidence | Automatic failure |
|---|---|---|
| 1. Canon | Current script/version, shot IDs, cast, props, location, time and author corrections identified | Silent merge with historical proposals; unresolved contradiction treated as fact |
| 2. Art identity | Approved character/prop/environment references and correct production mode | Generic anime face, same-face cast, wrong age/build/hair/costume, invented typography |
| 3. Cemí finish | Variable hand-ink contour, controlled hatching, painterly color, paper/print texture and scene-correct navy/steel/amber lighting | Plastic 3D/vector finish, unfinished graphite, dull monochrome blue, uncontrolled scribble |
| 4. Drawing integrity | Registered keys/breakdowns with stable skull, anatomy, hulls, props, grips and contacts | Whole-painting warp, optical-flow performance, pulsing identity, flexible rigid objects |
| 5. Full-scene motion | Character acting, environment, props, FX, secondary action and camera are separately planned and executed | Static slideshow, camera-only motion, held atlas presented as animation |
| 6. Timing | Script-supervised frame count, exposure sheet, spacing/contact charts and resolved timing conflicts | Invented duration, gaps/overlaps, unapproved cadence changes |
| 7. Layer/FX integrity | Clean mattes, occlusion, independent water/wakes/clapper/FX and reproducible composite | Water attached to hull, matte seams, effects deforming characters or props |
| 8. Sound | Authorized dialogue, ambience, Foley/SFX, music provenance, sync and final mix evidence | Placeholder audio called final; cloned voice without authorization; unknown music rights |
| 9. Independent review | A different designated reviewer watches/listens to the real deliverable and records frame/time evidence | Self-approval, file-existence check, successful decode or contact sheet alone |
| 10. Author approval | Luis approves the exact version after technical review | Assumed approval, approval inherited by a revision, or exploratory work promoted silently |

## Status vocabulary

- **Exploratory:** useful experiment; not eligible for production.
- **Submitted:** worker claims the bounded deliverable is ready for independent review.
- **Technical approved:** the designated reviewer accepted measurable requirements.
- **Author approved:** Luis approved that exact immutable version creatively.
- **Rejected:** preserved for evidence and learning; forbidden as a final-use dependency.
- **Superseded:** historically valid but replaced by an explicitly linked later version.

Technical approval never implies author approval. Author approval never repairs missing provenance or an unsafe dependency. A changed file has a new version and must pass its required gates again.

## Review method

For animation, play the sequence at speed and frame-step action/contact/occlusion changes. Record exact frames or timecodes for any model drift, line boil outside the intended texture, hand/paddle contact, hull rigidity, wake travel, matte edge, lip sync or unintended hold. Compare representative frames to approved identity and palette references. State which media were directly viewed or heard.

For still assets, review the requested production mode, full silhouette/crop, anatomy, identity landmarks, costume/prop continuity, color values, texture, alpha edges and prohibited lettering. A contact sheet can support review but cannot replace checking the full-resolution asset.

## Production truth

Infrastructure can reach a 10/10 design standard while an episode remains unfinished. Passing unit tests proves that ledgers and validators enforce their declared rules; it does not prove that an image looks right or that a shot moves convincingly. The repository must report studio-system readiness and episode-art readiness separately.

`episode_ready` additionally requires every shot to be covered by unchanged canonical production assets linked for final use with an exact picture kind (`final-animation`, `final-picture`, or `picture-master`) and exact audio kind (`final-audio`, `final-mix`, or `audio-master`). The corresponding real `quality-review` pipeline stage must have completed host bindings, its edit/manifest/pipeline dependencies, a hashed on-disk QA report, the exact set of reviewed picture/audio digests, and Luis's author approval. Labels in `episode.json` are necessary reporting fields but can never establish release readiness by themselves.
