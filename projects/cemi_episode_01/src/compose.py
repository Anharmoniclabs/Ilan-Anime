"""Compatibility wrapper: the compositor now lives in ``studio.engine``.

    python src/compose.py data/bell_rig_example.json --out renders/bell.mp4 [--draft]

Same spec format as before, plus spec v2 features (pivot-correct scale and
rotation without clipping, multiplane parallax, blend modes, FX generators and
the post stack). See docs/ENGINE.md.
"""
from pathlib import Path
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parents[1]))

from studio.engine import Compositor, interpolate  # noqa: E402,F401
from studio.render import export_shot  # noqa: E402


def export(spec, out, draft=False):
    return export_shot(spec, Path(out), draft=draft, base=ROOT)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("spec")
    parser.add_argument("--out", required=True)
    parser.add_argument("--draft", action="store_true")
    args = parser.parse_args()
    export(json.loads(Path(args.spec).read_text()), Path(args.out), args.draft)
