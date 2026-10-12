# Rejected local animation — frame inspection

Review date: 12 October 2026. Source videos: `projects/cemi_episode_01/renders/`.

The author reported that the result looked warped. Both MP4s were decoded: 576 frames for the 24-second current test and 120 frames for the five-second bell test. Enlarged sequential crops were inspected. These sheets show samples from the decoded videos, not just the input art.

| Segment | Visible problem | Implementation cause | Required correction |
|---|---|---|---|
| Current 0–10 s | Face, beard, shoulders and cloth stretch during the lean | Broad radial displacement of a flattened painting | Registered replacement pose drawings; stable skull and torso geometry |
| Current 0–10 s | Drum and hull move as if flexible | Water displacement is applied to the lower full image | Rigid props and hulls; water-only effects/masks |
| Current 10–24 s | Arms and faces pulse while the boat slides | Local mesh handles plus whole-canoe translation | Coherent articulated/hand-drawn stroke with actual blade entry, drag and recovery |
| Current 10–24 s | Wake fragments stick to the hull | Water pixels were retained in cutouts | Clean alpha silhouettes and independently travelling wake cels |
| Current 10–24 s | Water seam near foreground roots | Foreground extraction includes a wedge of original water | Object-accurate occlusion matte |
| Bell | Clapper has no independent lag or strike | Clapper and shell share one rigid layer | Separate clapper layer, contact timing and suspension geometry |

Evidence: [head](head_sheet.jpg), [hands/drum](hands_sheet.jpg), [canoe](boat_sheet.jpg), [foreground/water](root_sheet.jpg), [bell](bell_sheet.jpg).

The earlier renderer's deterministic-frame check and successful FFmpeg decoding only confirmed technical behavior. They did not prove good animation. The earlier positive delivery language is superseded by this rejection.

Reducing warp amplitude would not solve the missing action. Replacing all movement with held pictures would also fail the author's request. New drawings, stable geometry, physical contact, and shot-specific timing are required.
