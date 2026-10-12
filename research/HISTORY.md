# Cemí animation research and production history

This is a reconstruction from the available project files, the current conversation, and retrieved prior project context. It is not a verbatim export of every past conversation. Source documents and artwork are kept beside this account so proposals can be distinguished from implemented work.

## 1. The author's art comes first

The project began from Luis M. Minier's hand-drawn portraits: expressive heavy brows and eyes, irregular organic facial construction, distinctive noses and curls, visible ink/pencil character, and Caribbean/Bronx specificity. The author asked for full color, then progressively cleaner and more finished comic/anime linework with fewer construction marks.

The continuing grade became Option B, Moody Urban Dusk: deep navy/steel shadows, charcoal, amber/copper rim lighting and warm skin. This is an art-direction vocabulary, not permission to turn every setting into sunset. The prologue script requires moonless night.

The canonical 9 October direction is preserved verbatim at [ART_DIRECTION.md](earlier_cemi_pipeline/docs/ART_DIRECTION.md). It separates character assets, environment plates, story frames and editorial moodboards. It also rejects gratuitous wall lettering and generic same-face anime designs. Later requests for actual NYC graffiti apply where the scene calls for it, not as a license for invented slogans everywhere.

## 2. Early style-training exploration

The 8 October training kit explored a Qwen-Image-compatible style LoRA. It contains a composite moodboard, caption examples, a crop script and a training plan. Its own README explicitly says it is not a complete training dataset, does not include trained weights, and should not train directly on a labeled collage.

Preserved kit: [training_2026_10_08](archive_imports/training_2026_10_08/cemi_training_pack/).

A subsequent repository developed SDXL-oriented planning and keyframe generation, with a character/style manifest, dataset preparation, command generation and frame assembly. A style LoRA was kept distinct from character identity controls. The original code does not claim to implement every proposed full-cast command or to have trained a model.

Preserved snapshot: [earlier_cemi_pipeline](earlier_cemi_pipeline/), from `Anharmoniclabs/cemi` at `5bc8ae64d84292746e752dfe2bd1fbd35ab1adb0`. Important sources are its [pipeline blueprint](earlier_cemi_pipeline/cemi_pipeline/docs/PIPELINE.md), [style bible](earlier_cemi_pipeline/cemi_pipeline/docs/STYLE_BIBLE.md), [full character index](earlier_cemi_pipeline/configs/cast_full.json), and [author character descriptions](earlier_cemi_pipeline/data/character_bible.txt).

Earlier discussions also explored Blender, 2.5D rigs, generative video and cloud GPUs. These are historical alternatives. They are not current requirements or evidence of installed software, working integrations, trained weights or finished animation.

## 3. The 90s animation direction

The author asked for research into 1990s animation, color, cinematography and production. Prior discussions named *Ghost in the Shell*, *Evangelion*, *Cowboy Bebop*, *Yu Yu Hakusho*, *Perfect Blue*, and the earlier *Akira* as visual study references. These are reference titles, not copied assets or a claim that all these productions used identical techniques.

The proposed “Resonant Urban Myth” direction combined the author's character construction with distinct Bronx, Santo Domingo and historical-Caribbean settings; deliberate color states; economical acting; selected showcase action; atmospheric backgrounds; and controlled finishing. The final actionable contract is in the supplied [episode script](../projects/cemi_episode_01/data/EPISODE_SCRIPT.md), which specifies:

- 24 fps output, ordinary drawings on 3s, showcase action on 2s and brief impact frames on 1s.
- Painted backgrounds, flat cel-shadow planes, separate effect drawings, reusable banks and controlled holds.
- PRESENT, ECHO and BEFORE visual registers.
- PRESS as a change in drawing, depth, timing and sound—not simply a desaturation filter.
- A shared spiral/triangle motif and an exact eight-second, 192-frame sound loop.
- Independent layer timing, deterministic integer-frame evaluation, a shot manifest, and final audiovisual review.

These are the project's selected production rules. This repository does not promote earlier assistant summaries into independently verified historical scholarship. Exact URLs for two earlier general cel-production web references were not recovered, so no URLs were invented for them.

## 4. River designs and the first asset pack

The 11 October river pack contains 13 character sheets, three empty background plates, two keyframes and an earlier planning PDF. Its README distinguishes completed assets from missing shots and animation. It also records the Yara/Amaia design correction and identifies the third child/background survivors as proposals where appropriate.

Preserved pack: [Cemi-River-Scene](archive_imports/river_2026_10_11/Cemi-River-Scene/).

That pack's earlier 90-second cut and canoe assignments differ from the later full-episode script. Preserve both as versioned source evidence; use the current script and latest author corrections to resolve staging. Do not quietly combine the casts from the two versions.

## 5. Episode keyframe generation

The current script covers an 18:50 body, 128 shots and a separately planned 1:30 ending. The author explicitly requested individual 16:9 frames and consistent art/color. The original script's 4:3 text remains unchanged for provenance; 16:9 is the current output override.

The generation sequence covered the river prologue, title, Jerome Avenue and JC's room, the building's history, sound anomalies, projector override, 1957 ballroom, blackout, breakfast, banner, café and map. Seventy-seven numbered usable source images were recovered for 64 shot IDs; this counts presence of art, not completed coverage. Two earlier rejected images are preserved separately.

Corrections made or identified during that pass included:

- Moonless water instead of the reference's sunset.
- Exactly three lit children, without an accidental fourth child.
- Maintaining cast identities rather than confusing Amaia and Yara or changing Mikey's sex.
- Treating ballroom → laundromat → church → vape shop → community arts space as inserts within one nine-second S03-09 shot, not separate scenes.
- Including the phone AR-mural insert within that same shot.
- Recognizing the wrong exterior view for S01-09's bow POV, missing dirt beneath young JC's fingernails, incomplete Chismosa pipe-to-roof coverage, and invented storefront details.

The current source inventory and shot templates retain these partial states rather than claiming each still completes its shot.

## 6. Failed service route and the local workflow

The author requested the complete moving episode. An attempted change to a hosted video workflow encountered zero available generation credits; no video jobs were submitted in that attempt. The author then explicitly directed a local workflow built from still drawings and animation techniques. That current direction does not depend on Higgsfield or another paid video service.

A local Python/Pillow/NumPy/FFmpeg renderer and general cel compositor were built, along with clean plates, cutouts, temporary sound, a 128-shot exposure sheet and export validation. The first footage was a 24-second S01-11/S01-12 test and a five-second bell test.

## 7. Author rejection and inspection

The author rejected the videos as warped and then emphasized that making them static would also fail the task. Decoded video inspection confirmed rubbery face/body deformation, distortion of rigid props, unconvincing paddle action, attached wakes, a foreground-water seam and a rigid bell clapper. See the [audit and frame evidence](animation_audit/REPORT.md).

The important finding is that successful encoding, deterministic output and nonzero pixel movement do not demonstrate credible acting. The test's visual approach was rejected, even though its plumbing ran.

## 8. Replacement drawings and repository handoff

The next pass generated eight Beheto pressure poses, eight lead-canoe/paddle poses, six child reaction poses and an empty-canoe plate. They are saved as unapproved production experiments. Their registration, matte quality, hull stability and paddle continuity still need repair; they are not a finished animated replacement.

The user requested that the workflow, code and recovered research be pushed to `Anharmoniclabs/animestudio`, then asked to approve the push. No push occurred before approval. The user subsequently explicitly instructed the push. This repository is that consolidated handoff, with unfinished and rejected work labeled.

## Source/reference register

| Source | Role | Verification state for this import |
|---|---|---|
| [Anharmoniclabs/cemi](https://github.com/Anharmoniclabs/cemi/tree/5bc8ae64d84292746e752dfe2bd1fbd35ab1adb0) | Existing project source and art direction | Retrieved and copied at the stated commit |
| `cemi_training_pack.zip` | 8 October training proposal | Recovered, extracted; archive SHA-256 in provenance |
| `Cemi-River-Scene-Asset-Pack.zip` | 11 October character/river assets | Recovered, extracted; archive SHA-256 in provenance |
| `HERALDS_EP1_90s_anime_script(1).md` | Episode action, timing and implementation contract | Full supplied text preserved |
| Current conversation and retrieved project context | Decisions, corrections and experiment chronology | Summarized; not a complete transcript |
| [Official Diffusers SDXL LoRA example](https://github.com/huggingface/diffusers/blob/main/examples/text_to_image/train_text_to_image_lora_sdxl.py) | Earlier training blueprint reference | Historical link preserved; no training run in this task |
| [Qwen-Image](https://huggingface.co/Qwen/Qwen-Image) and [Qwen-Image-Edit-2509](https://huggingface.co/Qwen/Qwen-Image-Edit-2509) | Earlier model exploration | Historical suggestions, not current compatibility validation |
| [Wan2.2 Animate](https://huggingface.co/Wan-AI/Wan2.2-Animate-14B-Diffusers) and [Wan2.2 I2V](https://huggingface.co/Wan-AI/Wan2.2-I2V-A14B) | Earlier motion-model exploration | Historical alternatives; not used by the current local renderer |

No newly generated literature review or unrelated project history is included. This document identifies what was recovered and where additional research or production is still required.
