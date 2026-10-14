# Heralds of the Cemí — Nessa studio project

## Mandatory user image approval

The user explicitly requires approving each exact image BEFORE any animation.
Generate and present the still, then STOP for their approval. Autonomy covers
making images and proposals; it does not authorize animation before approval.
The user-facing `/approve-image <path>` command records the exact SHA256.
Do not write approval records, impersonate the user, or treat model review notes
as approval. Any revised image needs fresh approval. The first pilot animation
was submitted prematurely before this correction; it is not approved final work.

The user authorized wiring this book and pack into Nessa and autonomously creating
the adaptation. Make reversible production decisions and keep progressing without
repeated plot intake. Begin with a short proof shot before episode-scale generation.

## Sources and canon

- `sources/Heralds_of_the_Cemi.pdf` is Luis M. Minier's supplied manuscript.
- `canon/index.json` and `canon/pages/page-NNN.md` preserve PDF page references.
- `cemi_training_pack/references/style_board.png` is a composite synthetic style
  proposal. Its names/faces are not authoritative character canon.
- Read manuscript pages for each shot. Record source page numbers and distinguish
  textual facts from visual design proposals. In particular Adrian Vale in the book
  is not automatically the character labeled VALE in the board.
- Style: graphite grain, scribbled curls, heavy expressive brows, irregular contours,
  crosshatching and rich restrained color. Avoid smooth generic anime and plastic 3D.
- The earlier ocean preview is a separate experiment, not a scene from this book.

## Production

Use one parent Nessa controller. `image_edit` submits reference-based Qwen editing;
`video_generate` submits Wan2.2-I2V; `media_job` resumes and collects durable jobs.
These are paid HF inference operations with explicit project-relative sources.
Never repeat a submitted job after a timeout: inspect its receipt and poll it.
Use `production_update` for asset versions/reviews and `production_status` for state.
Register FFmpeg/Blender assembly via `production_run`. Save editable sources.

The original pilot was bounded. The user's subsequent explicit instruction now
authorizes Nessa to generate every identifiable character and every scene in the
entire book. This supersedes the pilot image-count limit. Build chapter inventories
from all 24 chapters, reconcile aliases into canonical characters, and produce one
reference image per character plus one keyframe per scene. Include historical and
unnamed identifiable characters; treat anonymous crowds as ensembles. Use source
pages, maintain coverage and record unresolved ambiguities. Every image still
requires user review; NO animation is authorized by the full-book image request.
The main director must be Nessa's GLM model, with FLUX through Hugging Face for new images, not GPT (user update).
Use image_generate with black-forest-labs/FLUX.1-dev; FLUX.1-schnell is available
for drafts. Qwen reference editing remains available only when explicitly requested.
Do not claim dialogue, music, LoRA training, motion-reference transfer, human
acceptance or full-episode delivery unless those stages actually run and pass.

## Training and deployment state

No custom LoRA is trained yet. Dataset manifest starts empty; the moodboard must
not be turned into an apparent full training corpus. Keep validation images apart
from training. Run the dataset readiness check before exporting any training job.
RunPod/ComfyUI and Wan-Animate are preferred controllable backends but are not
connected. Existing HF cloud supports Qwen-Image-Edit-2509 and Wan2.2-I2V-A14B.
Do not invent provider support or run training with a planning-only JSON file.

## User-authorized 3D batch

Use the 40 recent Downloads PNG character illustrations as visual sources. User
authorized TripoSR reconstruction and editable Blender files for all of them.
Manifest: production/character-3d-manifest.json. Preserve the original source
filenames and hashes; do not guess character identities. Continuity guidance:
canon/character-3d-continuity.json. This authorizes static meshes and Blender
files, not animation or automatic visual approval. Resume via NESSA/scripts/cemi_3d_batch.py.
