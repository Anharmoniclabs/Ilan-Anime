"""Deterministic renderer for the drawing IR: tapered cubic-Bézier ink and filled shapes.

No subject geometry lives here. Strokes become filled outline polygons whose
half-width follows the primitive's width profile (taper), drawn at a
supersampled scale and downsampled with Lanczos for antialiasing. SVG output
uses the same polygons, so raster and SVG agree up to resampling.
"""
from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw


def cubic(seg, n=16):
    p0, p1, p2, p3 = (np.asarray(p, dtype=np.float64) for p in seg)
    t = np.linspace(0, 1, n)[:, None]
    return ((1 - t) ** 3) * p0 + 3 * ((1 - t) ** 2) * t * p1 + 3 * (1 - t) * t * t * p2 + t ** 3 * p3


def sample(curve, n=16):
    pts = [cubic(seg, n) if i == 0 else cubic(seg, n)[1:] for i, seg in enumerate(curve)]
    return np.vstack(pts)


def stroke_outline(curve, widths, n=16):
    """Centerline + width profile -> closed outline polygon (N x 2)."""
    pts = sample(curve, n)
    if len(pts) < 2:
        return pts
    d = np.gradient(pts, axis=0)
    norm = np.hypot(d[:, 0], d[:, 1])
    norm[norm < 1e-9] = 1e-9
    normal = np.stack([-d[:, 1] / norm, d[:, 0] / norm], axis=1)
    t = np.linspace(0, 1, len(pts))
    w = np.interp(t, np.linspace(0, 1, len(widths)), widths) / 2
    left, right = pts + normal * w[:, None], pts - normal * w[:, None]
    return np.vstack([left, right[::-1]])


def _rgba(hex_color, opacity=1.0):
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (int(round(255 * opacity)),)


def polygons(drawing):
    """Yield (primitive, polygon) in draw order."""
    if drawing.get("separation_constraints"):
        from studio.drawing.separation import apply_drawing
        drawing, _ = apply_drawing(drawing)
    for prim in drawing["primitives"]:
        if prim["kind"] == "fill":
            yield prim, sample(prim["curve"])
        else:
            yield prim, stroke_outline(prim["curve"], prim["width"])


def render(drawing, supersample=4, base=None):
    """Drawing -> RGBA image. ``base`` (RGBA, canvas-sized) is drawn under, e.g. a cleaned plate."""
    w, h = drawing["canvas"]
    k = supersample
    out = base.convert("RGBA").resize((w * k, h * k), Image.Resampling.LANCZOS) if base is not None \
        else Image.new("RGBA", (w * k, h * k), (0, 0, 0, 0))
    shapes = {}
    for prim, poly in polygons(drawing):
        scaled = [(x * k, y * k) for x, y in poly]
        if prim["kind"] == "fill":
            shapes[prim["id"]] = scaled
        layer = Image.new("RGBA", out.size, (0, 0, 0, 0))
        ImageDraw.Draw(layer).polygon(scaled, fill=_rgba(prim["color"], 1.0))
        alpha = layer.getchannel("A")
        if prim.get("clip"):  # visible only inside an earlier fill (iris inside the eye opening)
            mask = Image.new("L", out.size, 0)
            ImageDraw.Draw(mask).polygon(shapes[prim["clip"]], fill=255)
            alpha = Image.fromarray(np.minimum(np.asarray(alpha), np.asarray(mask)))
        if prim.get("opacity", 1.0) < 1.0:
            alpha = alpha.point(lambda v, o=prim["opacity"]: int(v * o))
        layer.putalpha(alpha)
        out.alpha_composite(layer)
    return out.resize((w, h), Image.Resampling.LANCZOS)


def to_svg(drawing):
    w, h = drawing["canvas"]
    rows = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">']
    for prim, poly in polygons(drawing):
        pts = " ".join(f"{x:.2f},{y:.2f}" for x, y in poly)
        rows.append(f'<polygon id="{prim["id"]}" data-provenance="{prim["provenance"]}" '
                    f'fill="{prim["color"]}" fill-opacity="{prim.get("opacity", 1.0)}" points="{pts}"/>')
    rows.append("</svg>")
    return "\n".join(rows) + "\n"
