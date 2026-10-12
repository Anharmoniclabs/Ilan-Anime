# Local ComfyUI generation for Ilan-Anime

ComfyUI's open-source inference engine runs on your own computer or an existing GPU host. It does not require Comfy credits, a Comfy login, platform builds or serverless releases. Hardware, electricity and any separately rented compute still have costs. This integration calls the documented local server API; it does not modify Comfy's billing or hosted services.

## Implemented and verified

- Loopback-only HTTP adapter using Python's standard library; no platform SDK or API key.
- Reference-image → VAE encode → local checkpoint sampling → PNG output. Optional local LoRA and preprocessed ControlNet pose/line/depth guidance.
- Core-node allowlist, checkpoint availability checks and launcher that disables partner/API and custom nodes.
- Hash-bound approved upstream references, explicit seed, workflow hash and art-contract hashes.
- Saved prompt IDs, durable submission intent, manual recovery and queue/history reconciliation after lost acknowledgements. No automatic resubmission, reconnection, restart, provider fallback or credit purchase.
- Downloads become **exploratory** asset-registry versions with shot, continuity and provenance records. The existing dashboard reads this registry. Existing technical review, author approval and final-use gates remain required.

HTTP integration tests run against a synthetic local server. They test protocol/state behavior, not a real diffusion model, image quality or GPU performance. No actual images were generated during this implementation. No ComfyUI checkout, model weights or GPU were detected in the implementation environment.

## Install on the machine that owns the compute

Use an existing ComfyUI installation if you have one. Otherwise follow the upstream [manual installation guide](https://docs.comfy.org/installation/manual_install) for your operating system and GPU. Its PyTorch build must match that machine. Install into a separate environment; do not install GPU libraries into the studio's dependency-light runtime.

Use the official [ComfyUI repository](https://github.com/Comfy-Org/ComfyUI). Pin the checkout to a reviewed commit, retain its GPL-3.0 license, and record `git rev-parse HEAD` plus the environment's `python -m pip freeze` with your production records. Record SHA-256 hashes of each checkpoint, LoRA and ControlNet file alongside its license. No third-party source or model is redistributed here, and model licenses are separate from ComfyUI's license.

Put a compatible, locally licensed checkpoint in `ComfyUI/models/checkpoints/`. Optional compatible LoRA and ControlNet weights go in `models/loras/` and `models/controlnet/`. Downloads and training are not performed by this adapter. The repository does **not** contain a trained Cemí LoRA. Matching model families is the operator's responsibility; a filename check cannot prove compatibility or art fidelity.

From the studio repository, start the installed core (replace paths with your actual installation):

```bash
python -m production.comfy.launch --comfy-root /path/to/ComfyUI --python /path/to/comfy-venv/bin/python
python -m production.comfy.local doctor
```

On Windows the `--python` path can point to `python_embeded/python.exe` in the portable distribution. `--cpu` allows CPU inference for an installed model but is not an episode-scale performance promise. `--print-only` prints the launch argument list without starting anything.

The launcher uses `--offline` when available, with `--disable-api-nodes` as an older-version fallback, always plus `--disable-all-custom-nodes` and loopback binding. This is a local core-node profile, not an OS network sandbox. Use only the trusted checkout/environment. It cannot remotely enforce how an independently started server was configured.

For a GPU machine you already control, run ComfyUI there and create a local SSH tunnel:

```bash
ssh -N -L 8188:127.0.0.1:8188 your-gpu-host
```

The studio still calls `http://127.0.0.1:8188`. This command does not provision or rent a GPU. Keep the server private; this adapter has no public-server authentication layer.

## Produce one drawing

1. Read the current shot/script and `production/art_direction.json`. Register the selected reference in `production/asset-registry.json` and complete its existing digest-bound review/author gates. Do not turn an old keyframe or rejected atlas into canon automatically. See [asset pipeline](ASSET_PIPELINE.md).
2. Copy `production/comfy/s01-11.example.json` to a new job specification. Replace the reference IDs, checkpoint name, license and shot-specific pose text. Its example references intentionally do not assert approvals that have never been recorded. Use a new job ID for each pose/revision. The source PNG establishes canvas size; use a properly registered 16:9 layout for story frames.
3. Optionally add `lora` and `lora_strength`, or `controlnet`, `control_image: {asset_id, version}` and `control_strength`. Control images must already be preprocessed, registered and approved. This profile does not include a pose detector or automatic identity adapter.
4. Run from the repository root:

```bash
python -m production.comfy.local prepare path/to/job.json
python -m production.comfy.local submit s01-11-contact-v1
python -m production.comfy.local poll s01-11-contact-v1
```

`prepare` is offline. `submit` submits once. Each `poll` makes one status check and collects outputs if complete. No background scheduler is installed. Files and the durable record live in `production/comfy-runs/<job_id>/`; output hashes are recorded in the shared registry. One coordinator must serialize registry writes across jobs, as required by the existing asset registry. The CLI prevents simultaneous operations on the same job; a lock left by a crashed process must be inspected before removal.

If a connection breaks, stop the production task and ask Luis before continuing. After actual approval, record it explicitly:

```bash
python -m production.comfy.local resume s01-11-contact-v1 --approval 'APPROVE RESUME s01-11-contact-v1'
```

The string records a real decision; it is not authorization by itself. Resume only reads/reconciles the existing job and retrieves outputs. It never submits another prompt. If the interruption happened before submission, no matching prompt may exist: inspect the server, then create a separately authorized new job ID. Never guess that a timed-out POST failed to run.

## Studio handoff

The pipeline TD/coordinator owns Comfy job execution and shared asset registration. Workers supply bounded generation specifications for their assigned shots. Their role contract does not independently grant network, paid compute, publication or additional delegation permissions. Local generation is explicitly authorized by the current user request; no paid provider is selected.

After collection, the designated reviewer inspects the actual PNG and compares identity, costume, rigid geometry, hands/contact, lighting and registration to canon. Record the separate technical and author decisions through `asset_registry.py`; only then can the asset become `canonical` and appear in pipeline final-use links. Do not overwrite the downloaded PNG after review. A fix is a new generation job and asset version.

The adapter does not auto-complete a task ledger assignment or impersonate a host agent. A coordinator can attach its job manifest and output records to the assigned task's own result directory and submit the real worker result using `runtime.py`. Preserve any required real host bindings. The asset registry remains the source for canonical downstream media.

Approved replacement cels then feed the existing `projects/cemi_episode_01/src/compose.py` layers and exposure sheet. Registration, alpha preparation, cleanup, in-betweens, timing, sound and playback review are still required. This change provides local drawing inference transport, **not** a demonstrated automatic image-to-video or full-episode production system. In particular, it does not add a video diffusion model or substitute warped stills for acting.

## Primary references

- [Core source and license](https://github.com/Comfy-Org/ComfyUI)
- [Local API routes](https://docs.comfy.org/development/comfyui-server/comms_routes)
- [Upstream command-line flags](https://github.com/Comfy-Org/ComfyUI/blob/master/comfy/cli_args.py)
- [Official API example](https://github.com/Comfy-Org/ComfyUI/blob/master/script_examples/basic_api_example.py)
