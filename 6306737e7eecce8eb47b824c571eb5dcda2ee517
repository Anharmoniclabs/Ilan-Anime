# Heralds of the Cemí — Nessa production workspace

Open the project in Nessa:

```sh
nessa chat /home/alabs/Projects/HeraldsOfTheCemi
```

## Your approval comes before animation

Nessa may research the book, propose shots and generate images autonomously.
It must show each image and wait. After inspecting the exact image, type:

```text
/approve-image art/nessa-shot-02.png
```

Then ask Nessa to animate that approved image. Approval is tied to file content;
an image revision needs a new approval. A model's review never approves for you.

## Project contents

- `sources/`: original supplied PDF and extracted text.
- `canon/pages/`: 242 pages with stable PDF page references for retrieval.
- `cemi_training_pack/`: supplied pack, preserved separately from canon.
- `shots/`: source-linked briefs and Nessa director outputs.
- `art/`, `delivery/`: generated media and provider receipts.
- `production/state.json`: versioned assets and attributed review notes.
- `dataset/manifest.json`: empty reviewed dataset, currently not training-ready.
- `cloud/`: prepared Qwen LoRA recipe and GPU deployment requirements; not deployed.

## What actually runs

The initial `run_pilot.py` was directed by Codex and dispatches fixed Nessa tool
calls. The user requested real Nessa autonomy; `autonomous_director.py` instead
runs Nessa's cloud reasoning model through `Agent.run`. Nessa chooses its prompt
and tool calls. That run has image generation only; it stops for approval.
Evidence is saved under `~/.agentharness/runs/cemi-autonomous-*/evidence`.

The first Qwen edit missed the requested style and setting and was marked
needs-work. A revised Qwen-Image-2512 frame and a Wan motion test were generated
before the approval correction. Those are experiments, not approved episode art.

No custom LoRA, voice/dialogue model, full episode, RunPod pod or ComfyUI endpoint
has been produced by this setup. The actual training gate currently reports zero
approved images. Original art, motion references and cloud deployment access are
still needed for those branches. The book's names outrank the moodboard labels.
