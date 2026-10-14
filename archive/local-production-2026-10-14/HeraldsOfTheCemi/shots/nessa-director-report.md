# Nessa Director Report — nessa-shot-02

## Shot chosen

**"3:07 — the coin on the nightstand"** — a 5-second extreme close-up insert of the copper coin, complementary to the existing Juan Carlos desk clip (`ch01-jerome-0307-v2`).

## Why this shot

- The desk shot is a character beat (typing, looking at the train). The coin is the manuscript's first supernatural-adjacent object and the story's central motif; an insert gives the sequence an object beat between character moments.
- Page 13 gives dense, concrete visual material: copper-colored, heavy, spirals and hooked triangles (*señales viejas*), warm "like a plate somebody held a minute too long," on the nightstand. All of that is textual canon, not invention.
- It shares the palette (copper/terracotta/amber/indigo/teal) and graphite hand-drawn aesthetic with the desk shot, so it cuts cleanly against it.

## Source pages

- `canon/pages/page-013.md` (PDF page 13): coin description, warmth, nightstand, señales viejas, grandmother, fever backstory.
- Pages 14–15 were read for context (Chismosa, contact mic/steam riser, projector, the 3:07 moment) but the coin was chosen as the strongest complementary insert.

## Canon vs. design (kept separate in `shots/nessa-shot-02.json`)

- **Canon (textual facts):** coin on nightstand; copper, heavy, spirals + hooked triangles; runs warm, "off"; given at twelve after a fever.
- **Design proposals (my choices, not canon):** extreme close-up composition; faint copper glow as watercolor bloom; face-down phone and hoodie sleeve in soft background; slow push-in and one train-light sweep in the video prompt.

## Actual tool results

1. `image_generate` (Qwen/Qwen-Image-2512, 1664×928, seed 3071313, path `art/nessa-shot-02.png`): **generated successfully** in ~28s. SHA256 `b7602bee23555c6355ae47122dabed4666cfcf6c4524c510a9c3c2becea550aa`, 2,571,318 bytes.
2. `media_probe`: confirms valid PNG, 1664×928, rgb24, probe score 99.
3. `production_update` (asset `nessa-shot-02-image`, version 1): registered with snapshot.
4. Registered `tests` check: **passed** (exit 0) — source page references, canon/design separation, PNG decoding.

## Honest limits

- I cannot see images; the PNG is **not visually reviewed**. The generation receipt and probe confirm integrity only, not aesthetic quality.
- No animation was submitted. Per the user's correction and AGENTS.md, animation requires explicit user approval of this exact image (`/approve-image art/nessa-shot-02.png`).
- No LoRA is trained; this is text-to-image with style described in the prompt.

## Status

**Awaiting user image approval of `art/nessa-shot-02.png`.** No video will be submitted until the user approves this exact image.
