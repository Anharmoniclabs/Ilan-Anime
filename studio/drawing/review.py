"""Numerical plausibility gates for drawings. A pass is necessary, never sufficient.

These checks catch structural failures (the DRAW-take-002 single brown square
serialized as valid JSON) before anyone spends review time. They do not grade
style, identity or acting; only an independent reviewer and the author can.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

MIN_OCCUPANCY = 0.02   # drawn pixels / canvas pixels
MIN_SHAPES = 8         # distinct connected drawn regions
MIN_COLORS = 3         # distinct quantized colors among drawn pixels


def drawn_mask(image, background=None, tol=12):
    """Pixels that are drawn: opaque, and (if a background color is given/detected) not background."""
    rgba = np.asarray(Image.open(image).convert("RGBA") if not isinstance(image, Image.Image)
                      else image.convert("RGBA"), dtype=np.int16)
    mask = rgba[..., 3] > 127
    if background is None and mask.all():  # opaque preview: treat the corner color as background
        background = rgba[0, 0, :3]
    if background is not None:
        mask &= np.abs(rgba[..., :3] - np.asarray(background, np.int16)).max(-1) > tol
    return mask, rgba


def plausibility(image, background=None):
    """Return {passed, failures, measures}. Fails sparse, single-shape or monochrome drawings."""
    mask, rgba = drawn_mask(image, background)
    occupancy = float(mask.mean())
    import cv2
    count, _labels, stats, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8), connectivity=8)
    shapes = int((stats[1:, cv2.CC_STAT_AREA] >= 16).sum())
    colors = int(len(np.unique((rgba[..., :3][mask] // 32), axis=0))) if mask.any() else 0
    failures = []
    if occupancy < MIN_OCCUPANCY:
        failures.append(f"occupancy {occupancy:.4f} < {MIN_OCCUPANCY}")
    if shapes < MIN_SHAPES and colors < MIN_COLORS * 2:
        failures.append(f"{shapes} drawn regions and {colors} colors: too simple to be a drawing")
    return {"passed": not failures, "failures": failures,
            "measures": {"occupancy": round(occupancy, 4), "regions": shapes, "colors": colors},
            "note": "Structural gate only; does not judge style, identity or acting."}


def gate_file(path, background=None):
    return {"image": str(Path(path)), **plausibility(path, background)}
