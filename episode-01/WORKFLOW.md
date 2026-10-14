# Approved production workflow — version 1

Approved by the user on 2026-10-11: “perfecttttttt lock that exact worflow in”.

Reference: `build/take-02/opening-assembly.mp4`, 35 seconds, 840 frames, 1440×1080, 24 fps. The archive in `approved-workflow-v1/` preserves the renderer, plans, prompts, consumed art and approved video with SHA-256 hashes.

Subsequent scene-reference update: the user supplied eight new scene images in Downloads. See the [scene gallery](assets/scene-references/downloads-2026-10-11/index.html) and its `manifest.json`. Those images define the corresponding new shot compositions, costumes and seating. In particular, the new procession puts Amaia and her son in the lead canoe. The rear-canoe rule below describes the archived fleet only; it does not override the newer supplied scenes. The animation workflow remains approved as written.

## Visual and motion rules

- 1990s vintage cel anime: restrained acting, flat two-tone character shading, painted backgrounds, deliberate holds. No return to the earlier exaggerated action direction.
- 4:3 framing; 24 output frames per second. The working canvas is 1440×1080. Resolution changes must preserve framing and proportions; enlarged files must not be described as newly drawn native 4K art.
- Generate actual successive drawings for the action. Use transparent character/prop cels over separately painted backgrounds. A sprite sheet is an internal source of individual cels, never the displayed scene.
- Keep character identities, costumes, passenger counts, scale, seating and hull geometry consistent with the approved references. For this fleet, preserve Amaia holding her toddler in the rear canoe.
- Set explicit `[drawing_index, held_frames]` exposures. The approved wide fleet uses eight drawings in a 48-frame cycle: holds of 9, 3, 6, 3, 6, 3, 9 and 9 frames. These exact settings are the travel-shot reference, not a mandatory cycle for every action.
- Camera movement advances every output frame, independently of drawing holds. Use restrained pans/tracks and gentle heave; keep the subject's scale consistent. Water motion is a separate layer.
- Match moonless river lighting. Check that boats sit on the water and that foreground/background overlaps make physical sense. Bounds checks supplement visual inspection; they do not prove scene geometry is correct.

## Repeatable production steps

1. Read the next shot's action, camera, duration and continuity requirements from the supplied script and validated shot list.
2. Inspect the relevant model sheets and approved art. Generate the background, key poses and in-betweens with the built-in imagegen tool, keeping the established identities and composition.
3. Inspect each result. Reject or correct extra limbs, changed proportions, clipped paddles, unsupported children, opaque backgrounds and registration drift before using a cel.
4. Copy selected art into versioned project assets and save the exact prompts. Bind assets and exposure tracks in `data/render-plans.json`.
5. Composite with `episode.py`: uniform aspect-preserving scaling, separate camera/background motion, character cels and water effects. Keep all timing tied to frame numbers.
6. Render to a new take. Check first, middle and last frames plus the action changes between key poses. Correct placement and motion problems before assembly.
7. Validate frame counts, frame rate and contiguous shot timing; run the relevant renderer tests. Assemble only shots that actually exist.
8. Update the review page and status. Clearly distinguish motion drafts, missing assets, pending sound and completed episode work.

## Preserve the baseline

Do not overwrite `approved-workflow-v1/` or take-02. Develop the live renderer and future shots alongside them. Workflow improvements should retain the approved look and motion behavior; use a new take to compare changes. This approval does not require asking again before normal production work.

The approved opening is a silent motion draft. Remaining scene animation, dialogue/ambience, the five-depth-plate treatment, disappearing-seat inserts and analog finishing remain production tasks. The locked workflow is not a claim that those are already done.
