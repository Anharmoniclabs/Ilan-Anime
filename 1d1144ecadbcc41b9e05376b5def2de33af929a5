# Four silent insert/environment drafts — independent review requested

Status: submitted exploratory drafts. No technical or author approval, canonical promotion, generation, paid call, ledger change, or additional agent was used. Route to the coordinator's independent animation-supervisor reviewer.

| Shot | Selected review | Native project | Timing |
|---|---|---|---|
| S03-03 | S03-03/review.mp4 | S03-03/native/shot.ecproj | 288 frames / 12 s |
| S04-02 | S04-02/review-matte.mp4 | S04-02/native-matte/shot.ecproj | 144 frames / 6 s |
| S05-13 | S05-13/review-matte.mp4 | S05-13/native-matte/shot.ecproj | 96 frames / 4 s |
| S06-03 | S06-03/review.mp4 | S06-03/native/shot.ecproj | 144 frames / 6 s |

All selected videos: 1280×720, 24 fps, video only. Each shot directory contains shot.json, editable composition recipes, independent source layers, probe.json, checks.json, a complete decoded PNG sequence, and a decoded review sheet. Native files reference this task directory by absolute path; keep it in place or relink after moving. Earlier native/ and review.mp4 variants for S04-02 and S05-13 are preserved diagnostic predecessors, superseded by native-matte/ and review-matte.mp4. S05-13/preview.mp4 is an unsuccessful empty export from an initial path-resolution error, not a deliverable.

## Action and contact evidence

S03-03: an actual numeric pan on one stable painting. Registered plate 1408×792; crop origin x=128*f/287, y=72 at output resolution. No deformation, zoom drift, or invented pixels. Desk, food, laundry, radiator and bedside coin are revealed across the pan. This is a modest 128 px pan using the available plate, not an expanded panoramic painting. Actual artwork places desk/laundry left and radiator right, so that layout takes precedence over the contract's proposed radiator-first phase order. Eight separately drawn steam cels at three-frame exposures alternate with a 24-frame empty interval. No fan is visible in the supplied painting, so none was invented. Background photographs are painted set dressing, not live cast acting. The dev-board detail remains as supplied in the desk painting; no claim of newly drawn hardware detail.

S04-02: three gauze layers, separate exact labels SMOOTHING / GATING / NOISE FLOOR, and comb / door / line icons. All graphic layers have editable SVG source files. One rigid connected shared-sigil drawing and one unchanged waveform translate through all three panes on 3s. Sigil center crossings measured from the authored path occur at frames 30, 69, 108. No random logo, shape filtering, scale change, or added people. Pipe and projector derive from the supplied illustration with task-local object masks, over the clean room painting. Their masks and the clean graphic finish should receive independent style/matte review; no final finish acceptance is claimed.

S05-13: supplied clean plate and original RGBA coin preserved in sources/. Derived coin-matte-clean.png removes 891 alpha=1 specks outside/around the silhouette before fixed-size resampling. The painted coin is translated down 98 output pixels to rest on the visible tabletop; opaque contact bottom is recorded in registration.json. One separately anchored contact shadow remains on the wood. No coin scaling or rotation is animated. A copper glint is alpha-clipped to the coin and traverses at f12–14. White flash is only f17. Independent template matching against decoded coin pixels measured +2 px x at f1, -12 px y at f12/14/15, -9 at f16, -1 at f18, and zero at f19/95. Source settle frames 19,20,48,95 are pixel-identical. The lift is exactly the script's 12 screen pixels; physical inches cannot be inferred from the painting.

S06-03: intentional static window POV. Nearby windows, street and El remain dark, distant skyline retains the painting's normal ambient glow. No cars, people, lamp flicker, camera move, or temporal glow modulation added. First/last source pixels are identical. Small differences among decoded held frames are H.264 compression, not authored motion.

None of these four script shots calls for character acting. The room pan and blackout hold fulfill explicitly scripted background coverage; they are not substitutes for acting elsewhere or a claim that the episode is animated.

## Exact remaining continuity dependency

S05-13 coin-rgba.png contains a broad engraved spiral/hooked triangle with different line width, opening and triangle proportion from production/runs/episode1-picture-motion/tasks/editorial-motion-r1/shared-sigil.json and shared-sigil.svg. See sigil-continuity-comparison.png. Adding the thin native vector over the existing groove would double the mark rather than repair it. No destructive repaint was attempted. Final continuity needs either a clean unengraved copper face in this exact perspective/light, plus a registered shared-sigil engraving overlay, or an independently reviewed repaint of the supplied coin face using that shared path. The current coin motion draft preserves its original artwork and is submitted with this explicit limitation. It is not continuity-approved.

## Inspection and automation boundaries

Directly viewed: supplied room/filter/coin/clean-plate/blackout images; required approved style image and current Amaia/rooftop references; native room f0/287, filter f0/72, coin f0/12, blackout f0; decoded sheets containing room f0/72/144/216/287, filter f0/24/48/72/96/120/143, coin f0/1/3/9/12/14/15/16/17/18/19/95, blackout f0/72/143; enlarged decoded coin contact crops f0/1/12/16/18/19; sigil comparison. Coin silhouette stays rigid, with material-colored rim light and no conspicuous rectangular matte or white halo in the inspected composites. Contact shadow stays under the resting rim and separates visibly at the lift. No real-time playback claim is made.

Automated: every selected video fully decoded (672 frames total); ffprobe frame count/rate/dimensions/audio checks; coin timing assertions and decoded template tracking; source hold equality; all four saved native projects reopened successfully and rendered again. Native/studio checkpoints differ slightly at fractional translations because the engines resample differently (largest mean RGB error 0.777/255 on the room's midpoint); fixed-pixel endpoints and coin checkpoints closely agree. See technical-checks.json and pixel-checks.json. Codec variation during holds is documented rather than counted as meaningful action.

## STORY_FRAME contract observations

- Source precedence: current task and author-direction.json → current script and microkeys → selected new90s artwork/current Amaia and rooftop style correction → older canonical style documents. No author approval inferred from source selection.
- Identity: no live named characters assigned; no new cast introduced. Earlier character-specific identity tiers are not applicable to these inserts/environment shots.
- Style/grade/setting: supplied warm-room/cool-window painting and dark Bronx/El skyline are preserved; no global new grade. Abstract panes are native story graphics. Coin retains supplied painterly material, pending exact motif correction.
- Text: only the three expressly scripted filter labels added, exactly spelled. No sound, captions, slogans or generated lettering added.
- Geometry/layers: rigid coin and symbol transforms, fixed table contact, source originals retained, separate BG/steam/coin/shadow/glint/flash/endpoint/pane/icon/text/sigil/waveform layers. SVG sources remain editable.
- Crop/action/single asset: each video is a standalone 16:9 shot of full script duration. Review sheets are evidence only. Room inventory and coin action remain framed; final motif continuity remains a dependency.

## Reproduction

build.py records the initial source derivation and native recipes; matte-cleanup.py records the bounded alpha/endpoint corrections. They write only beneath this task directory. Do not overwrite saved evidence for review. The final shot.json files use absolute source paths. For an independent export into a new filename use `python -m studio render <shot>/shot.json --draft --out <task-local-new-file>.mp4`. Execute the selected saved native recipe through `python -m studio craft run <recipe> --out <new-task-local-directory>`; it refuses an existing output directory. Native recipe filenames are native-recipe.json for room/blackout and native-matte-recipe.json for filter/coin. verify.py and pixel-checks.py contain the performed checks. FFmpeg here uses fps_mode=passthrough; an earlier unsupported vsync option failed before decoding and was corrected. No connection interruption or external job occurred.
