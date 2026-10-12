# Heralds of the Cemí — local image-model style kit

**Artist / project:** Luis M. Minier — Heralds of the Cemí.

## Style target
Blend the clean, cinematic, softly colored character rendering of the approved moodboard with the artist's original expressive graphite aesthetic: visible pencil grain, circular scribbled curls, heavy brows, tired expressive eyes, irregular contours, crosshatching, handwritten graphic-novel lettering, Caribbean/Antillean urban and historical settings, culturally specific material detail, dramatic yet restrained lighting, and textured rich colors under hand-drawn strokes.

Avoid generic glossy anime, plastic skin, perfectly smooth vectors, 3D CGI, overly polished facial symmetry, and fabricated cultural symbols.

## IMPORTANT: what is actually in this kit
The reference poster is **one composite AI-generated moodboard**, not a complete licensed training dataset. The named faces and labels on the poster are visual concepts, not canonical character identities; verify against your manuscript and original drawings. Do not train on the whole labeled poster as a single image; labels, grids, and text would contaminate generations. The included script makes *candidate crops* that require manual review. Add your own original drawings and individually approved illustrations for an actual style LoRA dataset. A good starting point is 30–100 diverse, clean, captioned images; more diversity improves robustness. Hold out 10% for validation.

## Model compatibility
**Qwen-Image** is a diffusion/image-generation model and may be adapted with a compatible LoRA trainer. **Qwen2.5-VL or other vision-language Qwen models are not drop-in image generators**. Confirm the exact checkpoint and your trainer's support before starting. This kit does not claim to include model weights or a tested LoRA.

For a local GPU use a current Qwen-Image-compatible training implementation (for example Diffusers/AI-Toolkit if its current version supports your exact model), and follow its configuration syntax. Full fine-tuning can require substantial VRAM; use LoRA, gradient checkpointing, mixed precision and/or cloud GPU as supported. The JSON file here is a *training plan*, not a plug-and-play trainer configuration.

## Suggested process
1. Put your own original high-resolution drawings in `dataset/images/` and matching UTF-8 `.txt` captions in `dataset/captions/` (same stem).
2. Optionally run `python scripts/crop_reference.py` to create **candidate** poster crops. Inspect each crop; exclude text, borders, mixed subjects, and small/blurry crops. These crops are supplementary references, not replacements for original art.
3. Caption each approved image with the trigger `cemi_lm_style` and factual content (subject, pose, environment, lighting, media). Avoid hallucinating names.
4. Train an image-model LoRA with a trainer compatible with the exact Qwen-Image checkpoint; start with conservative rank and learning rate, compare held-out generations every checkpoint, and stop when identity memorization or style collapse appears.
5. Evaluate on fresh prompts for varied skin tones, ages, body types, historically researched Caribbean locations, action scenes, and expression consistency.

## Inference example
`cemi_lm_style, original Caribbean graphic-novel illustration of a young sound engineer in a Santo Domingo rooftop workshop, wind-tossed scribbled curls, expressive tired eyes, organic pencil contours and visible crosshatching, cinematic sunset colors painted beneath graphite linework, dynamic composition, carefully researched urban details, no lettering`

Negative prompt (if the model supports it): `3d render, glossy plastic skin, vector smoothness, generic anime uniform face, watermark, typography, deformed hands, duplicate limbs, blurry, low resolution`

## Copyright and provenance
Only train on images you own or are licensed to use for training. Maintain a manifest recording creator, source, license/consent, date, and character approval. Do not present AI-generated images as your original hand drawings. The poster is a generated visual proposal based on the style instructions, not a substitute for the original artist references.
