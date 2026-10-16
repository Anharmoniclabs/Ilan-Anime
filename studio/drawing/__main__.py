"""Drawing engine CLI: ``python -m studio.drawing <command> --help``.

Every command writes into a NEW take directory and never overwrites sources.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _new_dir(path):
    path = Path(path)
    if path.exists() and any(path.iterdir()):
        sys.exit(f"error: {path} already has files; use a new take directory")
    path.mkdir(parents=True, exist_ok=True)
    return path


def cmd_extract(a):
    from studio.drawing import reference
    print(json.dumps(reference.extract(a.image, _new_dir(a.out), colors=a.colors)["metrics"], indent=2))


def cmd_face(a):
    from PIL import Image
    from studio.drawing import face, render
    from studio.paths import load_json, write_json
    ident = load_json(a.identity)
    out = _new_dir(a.out)
    src = Image.open(ident["source"]).convert("RGBA")
    plate, _ = face.erase_features(src, ident)
    for name in a.expression:
        img, drawing, authorship = face.compose(ident, face.expression(name), src, plate)
        img.save(out / f"{name}.png")
        write_json(out / f"{name}.drawing.json", {**drawing, "authorship": authorship})
        (out / f"{name}.svg").write_text(render.to_svg(drawing), encoding="utf-8")
        print(out / f"{name}.png")


def cmd_plan(a):
    from PIL import Image
    from studio.drawing import face, model
    from studio.paths import load_json
    out = _new_dir(a.out)
    plan, _ = model.plan_expression(a.line, out, model=a.model)
    print(json.dumps(plan))
    if a.identity:
        ident = load_json(a.identity)
        img, _, _ = face.compose(ident, model.plan_to_expression(plan), Image.open(ident["source"]).convert("RGBA"))
        img.save(out / "face.png")
        print(out / "face.png")


def cmd_flux(a):
    from studio.drawing import flux
    if a.doctor:
        print(json.dumps(flux.doctor(), indent=2))
        return
    if not (a.reference and a.prompt and a.out):
        sys.exit("error: --reference, --prompt and --out are required")
    print(json.dumps(flux.generate(a.reference, a.prompt, a.out, width=a.width, height=a.height,
                                   steps=a.steps, seed=a.seed, timeout=a.timeout), indent=2))


def cmd_gate(a):
    from studio.drawing.review import gate_file
    result = gate_file(a.image)
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["passed"] else 1)


def main(argv=None):
    p = argparse.ArgumentParser(prog="python -m studio.drawing", description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("extract", help="approved cel -> editable flats/shade/ink/matte layers + fidelity metrics")
    s.add_argument("image")
    s.add_argument("--out", required=True)
    s.add_argument("--colors", type=int, default=8)
    s.set_defaults(func=cmd_extract)

    s = sub.add_parser("face", help="draw named expressions from a character identity model")
    s.add_argument("--identity", required=True, help="e.g. production/engineering/canon/amaia-front.identity.json")
    s.add_argument("--expression", nargs="+", default=["neutral", "fear"])
    s.add_argument("--out", required=True)
    s.set_defaults(func=cmd_face)

    s = sub.add_parser("plan", help="Qwen reads one action line and picks expression/intensity/gaze")
    s.add_argument("line")
    s.add_argument("--out", required=True)
    s.add_argument("--identity", help="also draw the planned face")
    s.add_argument("--model", default="qwen2.5-coder:1.5b")
    s.set_defaults(func=cmd_plan)

    s = sub.add_parser("flux", help="optional FLUX.2 Klein backend for new views/poses (slow on CPU)")
    s.add_argument("--doctor", action="store_true", help="only report installed backend files")
    s.add_argument("--reference")
    s.add_argument("--prompt")
    s.add_argument("--out")
    s.add_argument("--width", type=int, default=512)
    s.add_argument("--height", type=int, default=768)
    s.add_argument("--steps", type=int, default=4)
    s.add_argument("--seed", type=int, default=42)
    s.add_argument("--timeout", type=int, default=3600)
    s.set_defaults(func=cmd_flux)

    s = sub.add_parser("gate", help="structural plausibility gate (fails the one-square benchmark)")
    s.add_argument("image")
    s.set_defaults(func=cmd_gate)

    a = p.parse_args(argv)
    a.func(a)


if __name__ == "__main__":
    main()
