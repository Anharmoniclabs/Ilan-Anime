# Heralds of the Cemí — SDXL + Animation Studio

Author-directed, open production scaffold for maintaining the *original Cemí hand-drawn graphic-animation look* across storyboards, assets and animated scenes.

**Target:** author-derived face construction + clean cel-shaded anime accents, **Option B (Moody Urban Dusk)**. **No gratuitous quotes, graffiti, or wall text in generated scenes.**

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m cemi_pipeline --help
python -m cemi_pipeline shot --character JC --shot-id ep01-sc01-001 --scene 'at his desk in the Bronx at dusk' --out outputs/jc-shot.json
```

**Training** requires approved individual artwork and a separate CUDA GPU. `prepare` builds a captioned dataset; `train-command` prints an official SDXL Diffusers training command; `render` renders single keyframes with an already-trained LoRA; `assemble` creates MP4 from frame PNGs. No model or data is included.

Read [visual contract](docs/STYLE_BIBLE.md) and [training-to-animation guide](docs/PIPELINE.md) first. Approved art and weights are excluded from git deliberately. Check `configs/characters.json` for character continuity; some physical traits are author-reviewable adaptation choices.

## Safety and reproducibility

Never mistake a prompt or random seed for true character locking; use approved reference sheets and motion/pose constraints. Verify all third-party models, trainer revisions, and licenses, and track SHA256. The `--run` flag launches real training only on a GPU environment you configured; without it, no training starts.
