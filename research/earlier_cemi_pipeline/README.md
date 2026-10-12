# Heralds of the Cemí — SDXL Animation Studio

> **Visual source of truth:** [Canonical 2026-10-09 art direction](docs/ART_DIRECTION.md) — finished crosshatched hand-ink graphic-novel animation with rich painterly color and Option B dusk grade. No unnecessary wall slogans or text in generated assets.

> **CLI status:** the implemented CLI currently lives in `cemi_pipeline/` and covers nine core characters with single-shot generation. The full 68-entry author character index is present in `configs/cast_full.json`; a root-level `scripts/cemi_cast.py` batch generator is not yet checked in. The root-level examples below are target interface notes, **not working commands yet**. Run the nested CLI as documented in [its README](cemi_pipeline/README.md).

A repeatable, author-directed character generation and animation pipeline for Luis M. Minier's **Heralds of the Cemí**. Built from the artist's original hand drawings, not generic anime defaults.

**Locked direction:** Option B — Moody Urban Dusk. Maintain organic blocky faces, expressive heavy brows, subtle asymmetry and identity-specific hair. Clean 2D cel-shading; restrained anime influence; amber rim light and blue-gray shadows. **No random words, slogans, graffiti, or wall text in scenes.**

## Contents
- `data/character_bible.txt`: complete verbatim author character list and props
- `configs/cast_full.json`: indexed cast: 60 main/supporting entries + 8 age/time variants = 68
- `configs/style.json`: visual contract, palette and base-model settings
- `scripts/cemi_cast.py`: CLI for plan, GPU test render, contact sheet, integrity audit, review and export
- `scripts/prepare_style_dataset.py`: prepare only manually approved style-training art
- `docs/PIPELINE.md`: fine-tuning, identities, animation and release steps

## Proposed full-cast commands (not yet implemented)
```bash
python -m pip install -r requirements.txt
python scripts/cemi_cast.py validate
python scripts/cemi_cast.py plan --ids JC,MANNY,MIKEY --out outputs/test
python scripts/cemi_cast.py plan --out outputs/full_cast
python -m unittest discover -s tests -v
```

For an actual SDXL render install CUDA PyTorch and `requirements-gpu.txt` in a GPU environment, obtain and approve a trained Cemí SDXL style LoRA, then run `python scripts/cemi_cast.py render --jobs outputs/test/jobs.json --lora /path/to/pytorch_lora_weights.safetensors --limit 3`. Images are not trained/generated as a side effect of cloning or planning. Use `--allow-untrained` only for clearly labeled untrained SDXL baseline tests.

After visual inspection: `python scripts/cemi_cast.py approve --job JC__portrait --note "Face, anatomy, palette and expression manually reviewed"`, then `python scripts/cemi_cast.py export-approved`. Generated art and training weights are ignored by Git by default and are **not** automatically pushed.

Training requires a diverse collection of approved original or author-refined images; original pencil sketches guide identity but cannot, by themselves, teach a finished color grade. A style LoRA does not guarantee exact faces: use approved character references, compatible identity controls and pose conditioning; animate controlled rigs/keyframes rather than independently regenerating every video frame.

**State:** author bible indexed, pipeline scripts committed; no claim that an SDXL LoRA has been trained or that all character renders exist.
