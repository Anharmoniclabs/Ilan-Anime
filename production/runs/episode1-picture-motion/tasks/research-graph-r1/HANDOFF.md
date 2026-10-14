S14-03 / research-graph-r1 — submitted, exploratory

This is a replacement version for independent animation-supervisor review. No technical approval, author approval, canonical status or episode completion is claimed. Only S14-03 was changed. Original task inputs and rejected native-v1 remain untouched.

Open `native-r1/shot.ecproj` in EffectCraft. It contains 34 editable Text layers and 124 Shape layers, with no raster footage: node panels, typography, connector exposure paths, icons, four building outlines, four pin tracks, chart drawings and background texture remain separate. Individual shape layers contain editable paths for ink contours, cel fills and hatching. Layer names identify their purpose and exposure. `objects.json` indexes their frame boundaries and recipe steps. `edit.filmcraft` is the silent preview's editorial timeline; it is not the graphics master.

`recipe.json` is the saved Craft recipe; `build_native.py` authors it. The live tool/command schemas and call receipts are retained. The recipe ran through `python -m studio craft run`, and the saved .ecproj was reopened in EffectCraft before rendering. `render_native.py` renders native states every three frames and exposes each state for three frames, then encodes the MP4 and saves the FilmCraft timeline. It uses no tween, warp, optical flow, still-camera substitution or paid service. `studio-shot.json` is a raster interchange for existing studio QA only; the editable deliverable is the native project.

Timing remains 384 frames / 16 seconds / 24 fps, local f0–383, episode f21792–22175, ending at 15:24:00 exclusive. Export is silent 1280×720. Verify with `verify.py`; technical results and exact hashes are in `verification.json` and `probe.json`.

Frame-indexed observations

- f0–35: eleven tabs, root facts, and a designed website thumbnail. Text uses Aperture Civic and script-derived facts only. The thumbnail is a graphic facade, not an invented documentary webpage.
- f36–95: three shell branches draw progressively and converge into the document. Node centers and connector endpoints remain fixed.
- f96–140: fifteen individually authored path drawings, exposed on threes. Page corner folds at f99–105; lower sheet folds over at f108–117; paper edges become filling and bread at f120–126; the illustrated crust and lettuce settle at f129–138. The final drawing remains registered as the lunch icon. No shrinking full-frame painting is used.
- f150–251: lunch-to-holding connector and the nonprofit/music/development branches build at the prior beat positions.
- f252–300: four building outlines and exactly four independently exposed pin tracks. JC's home is the red lower-left pin. Each pin settles on the same building; no contact drift was visible in the decoded states.
- f300–327: the red ownership line leaves JC's building, then three connector branches resolve to The Ballroom, The arts space and The mural. Removed the added sentence “His building. His work.” The pie has no legend, values, percentages or quantitative claim. Manny's exact dollar line appears at f324.
- f327–383 is a final reading hold after the graph completes. It is not offered as character acting.

Visual inspection and limits

Directly viewed the approved style reference, current Amaia master, current Bronx rooftop reference and selected S14-03-r2 still. Directly viewed native frames f0, f129, f327; all 77 distinct decoded exposure states plus f383 on `review-frames/decoded-states-01.jpg` through `07.jpg`; the 15 decoded lunch drawings on `review-frames/lunch-drawings.jpg`; decoded f327 at full size; and the QA flagged-frame sheet. These are sequential frame inspections, not real-time playback. A reviewer should still watch the actual MP4 at speed.

Automated checks confirm all 384 decoded frames, dimensions/rate/duration, zero audio streams, 158 native objects, exactly eleven tabs and four buildings, and all authored exposure boundaries divisible by three. All source render triplets are identical within their three-frame exposure. First verification decode invocation used an unsupported local FFmpeg option; corrected to `-fps_mode passthrough`. This was a local command-argument correction, not an external job retry or connection interruption.

`qa/qa_report.json` has one `no_acting` flag at f0. The original independent reviewer explicitly identified this flag as inapplicable to S14-03 UI GRAPH. There are no characters in this assignment; adding acting would expand scope. QA did not check creative style, identity, or intent.

STORY_FRAME contract notes for the reviewer

- Source precedence: current author correction in `production/art_direction.json` and the Amaia/rooftop images govern finish; exact current script governs information. Earlier supplied style image and canonical documents were read/viewed as required. Portrait identity tiers do not apply to an abstract UI-only insert.
- Style/grade: irregular ink polygon contours, selectively heavier edge strokes, deliberate short hatching, restrained paper flecks, broad cel fill planes and warm cream/amber against navy/steel. These are newly authored native graphic paths; no reference tracing or generated character art. Whether the finish sufficiently matches the series remains the independent reviewer's creative judgment.
- Identity/anatomy: no depicted people. Manny appears only in the scripted text. Stable node/building geometry and independent pin contact tracks replace anatomical checks.
- Text: editable post-composited UI labels; no invented company names or narrative footer. Shell numbers are anonymous UI identifiers, not company names. No quantitative pie data.
- Crop/layers: single full-screen UI composition, all objects in frame; native text, shapes, pins, connectors and chart are independently editable. No character mattes or alpha cel dependencies are needed.
- Action: progressive graph paths, discrete document-to-food drawings, four pin drops and project discovery links. No camera move.
- Setting: schematic building block only, without invented geography or street addresses. The linked named places come directly from the shot script.
- Single asset: one continuous S14-03 shot; review sheets are evidence, not the shot deliverable.

Coordinator handoff: assign a separate animation-supervisor to this exact preview/native version. No new agents were launched by this worker, no source assets were promoted and no approval policy was changed.
