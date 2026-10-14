# Approved animation workflow

The user explicitly approved the Episode 1 take-02 opening and asked to lock its exact workflow on 2026-10-11. Read `episode-01/WORKFLOW.md` before further episode work.

Latest scene art: the user subsequently identified eight new Downloads images as the scenes. They are preserved and mapped in `episode-01/assets/scene-references/downloads-2026-10-11/manifest.json`. Use these supplied compositions and character designs for their corresponding new shots; this updates the scene references, not the approved animation method. The new night procession places Amaia and her son in the lead canoe, superseding the old asset's rear-canoe placement for this pass. Sunset images are alternate opening references without an assigned script shot ID. Keep the approved baseline intact.

- Continue with the approved 1990s vintage cel-anime workflow: generated reference-matched drawings, transparent cel layers, explicit frame exposures, independent camera/background movement, local FFmpeg compositing.
- Use `episode-01/build/take-02/opening-assembly.mp4` as the approved motion/style reference. Its preserved baseline is `episode-01/approved-workflow-v1/`.
- Maintain 4:3 composition, 24 fps output, uniform character scaling, and source-script timing. Working renders are 1440×1080. Do not silently substitute a different visual style, format, or animation method.
- Generate and build incrementally. Inspect actual composites, fix anatomy/registration/occlusion problems, render real animation, and assemble contiguous finished draft shots. Do not fill unfinished shots with still-image pans or repeat old footage to imply completion.
- Keep approved references and previous takes intact. New assets and takes get new filenames/directories. Routine generation, fixes, and rendering within this workflow are already authorized; this file adds no approval checkpoint.
- Approval locks the workflow and reference look; it does not mean the full episode, audio, or all storyboard requirements are complete. Report progress accurately.
