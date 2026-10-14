# Cemí animated-series pipeline — practical blueprint

## Architecture

`author pencil drawings -> hand-approved cleaned/colored master frames -> per-image captions + provenance -> SDXL style LoRA -> character identity controls -> storyboard shot manifest -> keyframes -> controlled motion/inbetween -> compositing/audio -> QA -> final video`

**Do not train from a single portrait or let one AI output define the entire house style.** A style LoRA learns statistical associations, not a guaranteed exact copy. Start with ~30–80 high-quality *distinct* curated approved outputs/paintovers across multiple subjects; quality and variation matter more than count. Begin with ~1,000–1,500 steps and compare checkpoints on the same held-out prompts. These are starting experiments, not promised optimal settings.

## Required infrastructure

- CPU laptop: curation, captions, shot planning, storyboard, FFmpeg; full SDXL training is impractical here.
- CUDA GPU (cloud or owned) with roughly 16–24+ GB VRAM recommended for SDXL LoRA baseline; 24 GB is considerably more comfortable. An 8–12 GB GPU may need aggressive offload/optimizer changes not configured by this kit. CPU training is not supported.
- Python 3.10–3.11 is a conservative target for training example compatibility; CUDA-enabled PyTorch, diffusers, transformers, accelerate, peft, safetensors and datasets installed together.
- Model access and licenses: `stabilityai/stable-diffusion-xl-base-1.0`; explicitly accept applicable model terms and maintain weight provenance.

## Setup and dataset

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp assets/approved_art/manifest.example.json assets/approved_art/manifest.json
# Add the actual approved jc_front.png and other separate artwork files before preparing.
python -m cemi_pipeline prepare --manifest assets/approved_art/manifest.json --out data/style_train
```

The manifest has `file`, `approved`, `origin` (`author_original` or `author_approved_refinement`) and human `caption`. The script checks image size, paths, duplicate SHA-256, approvals, presence/captions; it creates Hugging Face `imagefolder` compatible `metadata.jsonl`. It does **not** auto-generate training references, detect incorrect faces, assess captions, or choose train/validation splits. Check provenance output and don't upload private source art. Original pencil studies are useful as reference, but mixing them with finished colored samples may teach raw graphite/no-color. Favor finished author-approved illustrations for the primary style LoRA.

## SDXL LoRA training

Use Hugging Face's official [`train_text_to_image_lora_sdxl.py`](https://github.com/huggingface/diffusers/blob/main/examples/text_to_image/train_text_to_image_lora_sdxl.py) from a **specific tested release/commit**, not an unknown third-party training script. Install that checkout's `examples/text_to_image/requirements_sdxl.txt` and run `accelerate config`; use an SDXL-safe VAE if half precision creates NaNs. Pin the upstream revision in your actual training log.

```bash
# Example after obtaining the official script + its matching dependency versions:
python -m cemi_pipeline train-command \
  --trainer /path/to/diffusers/examples/text_to_image/train_text_to_image_lora_sdxl.py \
  --dataset data/style_train --out models/cemi-style-v1 \
  --steps 1500 --rank 16 --resolution 1024
# Prints exact command; rerun with --run on a properly configured CUDA host to actually train.
```

Save tested checkpoints and compare against a fixed prompt grid. Use a unique trigger `cemistyle`, rather than a real person's name. The model may still invent text or anatomy errors despite negative prompts. Training a style does **not** lock the identity of JC or Manny.

## Character shots and generation

```bash
python -m cemi_pipeline shot --character JC --shot-id ep01_sc01_sh01 \
  --scene 'JC at a quiet Bronx desk, listening to a room, medium close-up, no text' \
  --seed 8124 --out outputs/shots/ep01_sc01_sh01.json

python -m cemi_pipeline render --shot outputs/shots/ep01_sc01_sh01.json \
  --lora models/cemi-style-v1/pytorch_lora_weights.safetensors \
  --out outputs/keyframes/ep01_sc01_sh01.png
```

The included renderer provides **text-to-image keyframes only**. For shot-to-shot identity, use separately approved character turnaround references, ControlNet OpenPose/depth for position/composition, plus an SDXL-compatible identity reference method (e.g. IP-Adapter) and face/hands review. **Do not treat ControlNet, AnimateDiff or IP-Adapter as interchangeable**; select compatible SDXL checkpoints/components and test their licenses. Character LoRAs may eventually help if enough consistent canonical views exist.

## Animation options

1. **Recommended first episode: 2.5D cutout/rigged animation.** Isolate head, hair, torso, upper/lower arms, hands, legs, mouth/eye layers on clean transparent PNGs, rig in Blender Grease Pencil/2D tools, animate key poses and camera. Stable character identity is easier than full generative video.
2. **AI-assisted short shots:** generate approved keyframes; add pose/depth guides and an SDXL-compatible image-to-video/motion model; render short 2–4 second clips; reject face/style drift. Interpolate only after QA, not to hide structural errors.
3. **Classic frame-by-frame:** artist-approved extremes and in-betweens at 12 fps (animated on twos at 24 fps output), often composited at 24 fps; expect significant manual correction. Don't create every frame independently from random SDXL seeds.

Use `python -m cemi_pipeline assemble --frames outputs/shot_001_frames --fps 12 --out outputs/shot_001.mp4` for numbered/labeled frame PNGs. This performs assembly **only**, not motion generation or audio sync. For audio, edit the resulting MP4 and an independently licensed voice/music/soundscape in a video editor or FFmpeg.

## Suggested project deliverables

- `style.yaml` and approved original/finished reference plates.
- One standalone character reference per canonical character (3/4, profile, front, back, expressions, action, turnarounds, props); no excessive page typography.
- Scene cards keyed to script location, background set IDs, shot IDs, dialog timing, movement, camera, audio.
- Layered Photoshop/Krita `.ora` / PNG assets for 2.5D rigging.
- Per-shot manifests (seed, LoRA SHA256, base model revision, adapters, prompt, reference asset hash, color grade, render settings).
- Human review reports for off-model faces, bad hands, inconsistent height, random writing, prop continuity, skin-color fidelity, and temporal flicker.

## Next milestone

Gather at least 10 **separate** clean approved style plates first, then a more varied set for actual training. Approve JC and Manny master turnaround identities before frame animation. Render one controlled 4-second scene before committing to episode scale. Current repository includes infrastructure; **no LoRA has been trained, no animation generated, and no cloud GPU job has run**.
