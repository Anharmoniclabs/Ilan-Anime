# Controllable GPU branch — prepared, not provisioned

Preferred platform: RunPod. No RunPod credential or running ComfyUI endpoint was
configured in this session. No GPU pod was rented and no model weights were
downloaded onto this CPU laptop.

## LoRA pilot

`qwen_lora_pilot.yaml` targets the original `Qwen/Qwen-Image`, not Qwen-VL and
not the reference-editing checkpoint. It is an AI Toolkit recipe based on the
trainer's official model documentation, not a claim that training has run.
The 500-step trial is a bounded starting experiment; it does not guarantee fit.

1. Gather individually reviewed images with captions and provenance in
   `dataset/manifest.json`. Do not mark the composite moodboard as training art.
2. Run `studio_dataset_check` in Nessa. The configured gate is 27 training and
   3 held-out validation images, with no duplicate hashes across splits.
3. Run `scripts/export_training.py`; it refuses an unready manifest and emits
   separate train and validation directories. Review diversity independently.
4. Provision a GPU environment only after supplying account access and an explicit
   rental/spend limit. Start with an 80 GB GPU target; measure actual memory and
   step time rather than promising a particular fit or price.
5. Pin the installed AI Toolkit commit and exact base model revision. Record CUDA,
   PyTorch, GPU, source hashes and effective recipe before training. Install its
   dependencies in the pod, not the laptop's system Python.
6. Copy the project to `/workspace/HeraldsOfTheCemi`, run a short compatibility
   smoke test, then use AI Toolkit's `run.py` with the prepared YAML.
7. Compare base and LoRA with fixed seeds/prompts and untouched validation examples;
   save adapter weights, sample grids and review notes. Do not promote solely on loss.

Schema for an approved manifest item:

```json
{"image":"dataset/images/001.png","caption":"dataset/captions/001.txt","sha256":"ACTUAL_FILE_SHA256","approved":true,"source_type":"original","provenance":"Creator and source record","split":"train"}
```

## ComfyUI and Wan-Animate

Use a private/authenticated ComfyUI endpoint on the provisioned pod. Import an
official matching workflow and inspect `/object_info` against installed nodes and
checkpoint filenames. Export API-format workflow JSON before automation.
The standard API provides `/upload/image`, `/prompt`, `/history/{prompt_id}` and
`/view`; retain prompt IDs and recover jobs rather than resubmitting.
The current Nessa HF media tools do not control this unconfigured endpoint.

Wan2.2-Animate needs a character image AND a motion-reference video, plus its
preprocessing artifacts. Neither a trained adapter nor a motion clip is supplied
in the pack. Follow the official Wan preprocessing/generation flow when those
inputs and the GPU exist. HF Wan2.2-I2V is the working pilot path; it does not
provide the same motion-transfer controls.

References checked 2026-10-08:
- https://ostris.com/docs/ai-toolkit/models/qwen-image
- https://github.com/ostris/ai-toolkit
- https://docs.comfy.org/development/comfyui-server/comms_routes
- https://huggingface.co/Wan-AI/Wan2.2-Animate-14B
- https://huggingface.co/Wan-AI/Wan2.2-I2V-A14B
