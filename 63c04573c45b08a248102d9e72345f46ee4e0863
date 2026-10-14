# Local agent, remote generation, local episode finishing

The local studio coordinates work through the existing Codex runner. Blender,
FFmpeg, the compositor, shot timing and all saved assets stay local. Image/video
model inference needs remote GPUs on this machine. Nothing here uses Z.ai,
GLM or Hugging Face Inference Providers for the agent's reasoning.

Current user ceiling: **$5 total**, not $5 per shot. No money was spent by this
integration. `production/policy.json` is unchanged: paid generation is disabled.
The existing paused `pilot-20261012` run has not been resumed.

## Model choices to test

These are candidates selected for the task, not a measured quality ranking of
models on the author's drawings:

| Task | Choice | Integration status |
|---|---|---|
| Local orchestration / Blender scripting | Existing signed-in Codex CLI | Existing studio worker/reviewer runner; its own account limits apply |
| Reference-guided image creation | GPT Image via existing `studio generate image` | Already implemented; needs API credentials and user-configured spending policy |
| Open-weight character/reference edits | [Qwen-Image-Edit-2511](https://huggingface.co/Qwen/Qwen-Image-Edit-2511) | Recommended comparison candidate for consistency/multiple references; GPU endpoint not wired |
| Faster open-weight image edits | [FLUX.2-klein-4B](https://huggingface.co/black-forest-labs/FLUX.2-klein-4B) | Recommended comparison candidate; GPU endpoint not wired |
| Reference image to video | [Pepe104 MiniMax-H3 Turbo Space](https://huggingface.co/spaces/Pepe104/MiniMax-H3-Turbo-Lora-UNCENSORED) | New `studio video` bridge; live generation not yet verified |
| Stable props, authored geometry and layers | Blender 4.5.14 LTS installed locally | Existing NPR bridge; GPU rendering availability must be tested separately |

Qwen's model card describes improved character consistency and multi-image
editing. FLUX's card describes unified generation and multi-reference editing.
Neither guarantees the author's likeness or a finished anime style. Their
weights are not installed on this laptop. The selected video Space is not a
general endpoint for arbitrary HF image models or custom character LoRAs: its
LoRA choices are its own speed adapters.

The [Space source](https://huggingface.co/spaces/Pepe104/MiniMax-H3-Turbo-Lora-UNCENSORED/blob/main/app.py)
exposes `/generate` with first/last images, 24 fps, 2–14 second requests and
frame counts snapped to `17*n+5`. It calls a separate Qwen3-VL conditioner.
The adapter uses exact 16:9 input, a fixed seed and disabled prompt rewriting.
It trims only surplus tail frames on import, never pads a short clip with holds.
Last-frame-conditioned endpoints can be trimmed away when duration snaps;
review continuity rather than assuming the last reference is in the kept cut.

## Cost boundary

[HF's ZeroGPU documentation](https://huggingface.co/docs/hub/spaces-zerogpu)
says PRO accounts can automatically consume prepaid credits after the included
daily allowance runs out. The connected account is PRO, but remaining quota
and billing controls were not available to this local session.

Therefore this adapter connects **anonymously**, passing `token=False` (or
`hf_token=False` with older clients). It refuses client authorization headers.
It neither uses cached HF tokens nor offers a paid fallback. Anonymous quota
is small and may be insufficient for H3; quota exhaustion is a stop, not a
reason to switch credentials, buy credits, duplicate Spaces or retry requests.
The small $5 budget is not a credible guarantee of completing all episode
generation. Included quotas may permit incremental work over time, subject to
availability and creative review. No scheduled reruns are installed.

## Start on the host terminal

The Codex shell could not resolve HF/GitHub and had no cached Gradio client.
Run from the ordinary terminal, which may have network access:

```bash
cd /home/alabs/Projects/Ilan-Anime
uv pip install --python .venv/bin/python -r requirements-video.txt
.venv/bin/python -m studio video doctor
.venv/bin/python -m studio video submit production/video-jobs/s01-02-test-v1
```

One three-second S01-02 **technical candidate** is already prepared from the
existing keyframe. `first.png` and `job.json` record the exact input and prompt.
That source has not been promoted to approved character canon. Submission
uploads the prepared images to the selected community Space and its conditioner.

After successful download:

```bash
.venv/bin/python -m studio video import production/video-jobs/s01-02-test-v1
.venv/bin/python -m studio render production/video-jobs/s01-02-test-v1/imported/shot.json --draft --out production/video-jobs/s01-02-test-v1/review.mp4
.venv/bin/python -m studio qa production/video-jobs/s01-02-test-v1/imported/shot.json --render production/video-jobs/s01-02-test-v1/review.mp4 --out production/video-jobs/s01-02-test-v1/qa
```

The original downloaded MP4 keeps its generated soundtrack; the imported draft
has no audio so incidental speech/music cannot silently replace scripted sound.
The frame sequence enters the same engine layer format used by Blender imports.
Use Blender separately for authored props/layers; this does not turn a generated
video into an editable 3D scene or a separated character rig.

If generated in a browser instead, import the existing file without another call:

```bash
.venv/bin/python -m studio video import production/video-jobs/s01-02-test-v1 --clip /absolute/path/to/download.mp4
```

Do not delete `submission.lock` or rerun an interrupted submission. The state
records an uncertain outcome even after Ctrl+C. Inspect `downloads/` and remote
history and recover an existing clip first. A later retry is a separately
authorized job, not a silent retry of the old one.

## Agent handoff and episode completion

`production/video-plan.json` inventories all 128 shots, 27,120 frames (18:50),
and 143 mechanically split segments. This is a workload inventory, not a
generation queue: title cards need local typography, long shots need authored
segment continuity, and 64 shots lack keyframes. Start with one motion test.

The pipeline TD prepares/submits one bounded job; an independent reviewer
checks actual motion, stable faces/props, paddle-water contact and likeness.
Keep each job within its assigned task output directory when working under a
ledger envelope. Worker sandbox network permissions still apply; the coordinator
can submit prepared jobs from the host and hand their results back to the worker.
No worker receives broad network access from this change.

Technical import never writes canonical shot specs, assets, ledger approvals or
final episode files. Import results must be registered and reviewed under
`docs/ASSET_PIPELINE.md`, then approved by Luis before production use. Longer
shots need all approved segments composed on their exact offsets before the
existing render queue and assembly can finish the episode. Sound, lip sync and
final author review remain separate work.

Blender's NPR settings and stepped object animation were also smoke-tested
inside the installed Blender 4.5.14 LTS, without rendering. EEVEE settings,
24 fps and stepped F-curves applied successfully; optional legacy settings
were reported as unavailable. This does not verify GPU rendering.

Tests exercise failed/duplicate submissions, API drift, reference tampering,
episode coverage and real FFmpeg decode → layer import → compositor draft
export. Synthetic test video proves plumbing only; no real model generation
or animation-quality approval has occurred.
