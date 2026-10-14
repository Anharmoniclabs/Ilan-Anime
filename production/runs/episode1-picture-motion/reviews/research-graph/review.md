# Independent animation-supervisor review — research-graph / S14-03

Decision: reject for revision. Submitted artifacts were read only. This review does not provide author approval.

## Inspection and limits

Read the task envelope, all three inputs, worker contract, role skill, README, status, rejected-motion audit, art-direction contract and canonical art/style documents. Viewed approved_style_reference.png, current Amaia master, current Bronx rooftop reference, and selected S14-03-r2.png. Current author corrections and script take precedence; the selected still is not author-approved canon.

Decoded the actual preview MP4 completely and viewed every distinct exposure-start image plus f383 on decoded-1.jpg through decoded-4.jpg. Viewed f129, f132 and f324 at full resolution. This was sequential frame inspection, not real-time playback. Frame numbers are zero-based local frames; episode offset is 21792. Parsed native projects rather than reopening them in their applications.

Ran studio QA against native-v1/studio-shot.json with native-v1/preview.mp4 as render; see qa/qa_report.json. The initial invocation supplied the render directory and failed because this CLI requires a movie path; corrected invocation completed. Viewed qa/flagged_frames.jpg. Its sole no_acting@0 flag is a false positive for this UI-only assignment: do not add character acting. No freeze, length, matte or boil flags were returned; those checks do not prove semantic or visual acceptance.

## Acceptance and STORY_FRAME criteria

- Export: PASS. ffprobe and full FFmpeg decode confirm 384 frames, 16 seconds, 1280x720, 24/1 fps, video only. Exposure durations total 384 and all boundaries are multiples of three.
- Native deliverables/layers: FAIL. shot.ecproj contains one Comp and 61 Footage items; all 61 layers use complete flattened PNG drawings. studio-shot.json has one cels layer. edit.filmcraft contains a single preview.mp4 clip. Exposures and the Python source are editable, but text, chart objects, pins and connectors are not independently editable native graphics.
- Source precedence: assessed under current 90s anime correction and exact shot script, not obsolete comic-only facial rules. No character identities appear; portrait tiers/identity are not applicable to this UI insert.
- Style: FAIL. f0–383 use mechanically uniform rounded rectangles and linework on a flat cream field. Sandwich/pins are minimal schematic icons, with no visible hand-ink finish. UI simplicity is appropriate, but the submitted finish does not establish the current requested anime style. Full-screen UI framing itself is allowed by the shot.
- Grade: acceptable UI contrast with navy type, cream field and amber connectors; no skin-pigment concern. Rich environmental lighting is not required for a full-screen diagram.
- Text/script semantics: PARTIAL. Aperture Civic, registered 2024, five-month website, no employees, shell/holding branches, eleven tabs and Manny line are legible. No invented company names or numerical pie-chart legend. “His building. His work.” is added wording. The Ballroom/arts-space/mural footer at f300 is detached from the graph and does not visibly resolve their relationship to the ownership discovery. No website appearance communicates the scripted gorgeous facade.
- Anatomy/geometry: PASS for stable UI boxes, text and pin positions; no faces, grips or anatomy. No mesh warps or camera-pan substitution.
- Crop: PASS. All eleven tabs and main diagram elements fit the final export without accidental clipping.
- Action: PARTIAL. Lines build during f36–95; paper appears f96 and shrinks f117–129, then switches to a fully formed sandwich at f132. This is not the claimed readable fold transformation. Holding and branches build f150–240, pins drop f264–300, pie wedge grows f300–324. The final 60-frame read hold is reasonable for dense UI and is not itself a rejection reason. Footer at f300 appears as text instead of making a graphic connection.
- Setting: acceptable abstract UI insert; no unsupported street names or addresses. Four schematic buildings and a JC/home pin appear. The map is explicitly an illustration, not geographic evidence; no fabricated quantitative data is claimed.
- Single asset: PASS. One continuous S14-03 UI shot, not an unsolicited collage or character substitute.

## Required handoff

See result.json repair_notes. Preserve native-v1; return a separately versioned native revision with separable graphic objects, a readable document-to-sandwich transition, and the exact ownership-discovery beat. Re-export and independently review the new exact file. Do not promote to canonical or infer Luis approval.
