"""Approved drawing -> editable cel layers, rebuilt and measured against the source.

A cel becomes four layers that stack back to the drawing:

* ``flats``   vector fill polygons from ``studio.scan`` (recolorable cel paint);
* ``shade``   grayscale multiply layer = source / flats. It carries the painted
              grain and shading that flat vectors cannot hold, so recoloring the
              flats keeps the artist's texture instead of discarding it;
* ``ink``     vector variable-width strokes from ``studio.scan``;
* ``matte``   the source alpha. The composite is clipped to it, so the cel edge
              is the artist's edge, not a polygon approximation.

``measure`` reports what was lost for both the vector-only rebuild (flats + ink)
and the full layered rebuild. The vector-only numbers are the honest editability
cost; the layered numbers show how much the raster shade layer recovers. Neither
is an artistic approval.
"""
from __future__ import annotations

import time
from pathlib import Path

import numpy as np
from PIL import Image

from studio import scan
from studio.paths import rel, sha256, write_json

try:
    import cv2
except ImportError:  # pragma: no cover - scan reports the missing dependency
    cv2 = None

LAYERS = ("flats", "shade", "ink", "matte")


def _rgba(image):
    return np.asarray(image.convert("RGBA"), dtype=np.float32) / 255


def _subset(data, *, fills=True, strokes=True):
    return {**data, "fills": data["fills"] if fills else [], "strokes": data["strokes"] if strokes else []}


def to_svg(data):
    """Scan dict -> SVG text. Strokes are emitted per segment so line weight varies like the ink."""
    w, h = data["size"]
    colors = {p["id"]: "#%02x%02x%02x" % tuple(int(round(v * 255)) for v in p["rgb"]) for p in data["palette"]}
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
           f'<!-- source {data["source"]} sha256 {data["source_sha256"]} -->', '<g id="flats">']
    for i, fill in enumerate(data["fills"]):
        pts = " ".join(f"{x + 0.5:g},{y + 0.5:g}" for x, y in fill["points"])
        if fill["holdout"]:
            continue  # holdouts are carried by the matte layer
        out.append(f'<polygon id="fill-{i}" points="{pts}" fill="{colors[fill["color"]]}"/>')
    out.append('</g><g id="ink" stroke-linecap="round" fill="none">')
    for i, stroke in enumerate(data["strokes"]):
        color = colors[stroke["color"]]
        segs = "".join(f'<line x1="{x0:g}" y1="{y0:g}" x2="{x1:g}" y2="{y1:g}" stroke-width="{r0 + r1:.2f}"/>'
                       for (x0, y0, r0), (x1, y1, r1) in zip(stroke["points"], stroke["points"][1:]))
        out.append(f'<g id="stroke-{i}" stroke="{color}">{segs}</g>')
    out.append("</g></svg>")
    return "\n".join(out) + "\n"


def build_layers(data, source):
    """Return {name: PIL.Image} for the four cel layers plus ``composite``."""
    src = _rgba(Image.open(source))
    alpha = src[..., 3]
    flats = _rgba(scan.rasterize(_subset(data, strokes=False)))
    ink = scan.rasterize(_subset(data, fills=False))
    # shade = source / flats per pixel (luma ratio), 1.0 = no change; clipped to a sane multiply range
    luma = np.array([0.299, 0.587, 0.114], dtype=np.float32)
    ratio = (src[..., :3] @ luma + 1e-3) / (flats[..., :3] @ luma + 1e-3)
    ratio = np.where((alpha > 0.02) & (flats[..., 3] > 0.02), np.clip(ratio, 0.0, 2.0), 1.0)
    # store ratio/2 so 0..2 fits 0..255; 128 = neutral
    shade = Image.fromarray(np.round(ratio / 2 * 255).astype(np.uint8), "L")
    matte = Image.fromarray(np.round(alpha * 255).astype(np.uint8), "L")
    layers = {"flats": Image.fromarray(np.round(flats * 255).astype(np.uint8), "RGBA"),
              "shade": shade, "ink": ink, "matte": matte}
    layers["composite"] = composite(layers)
    return layers


def composite(layers, *, use_shade=True, use_matte=True):
    """Stack cel layers: flats x shade, ink over, clipped to matte."""
    flats = _rgba(layers["flats"])
    rgb = flats[..., :3]
    if use_shade:
        rgb = np.clip(rgb * (np.asarray(layers["shade"], dtype=np.float32) / 255 * 2)[..., None], 0, 1)
    a = flats[..., 3]
    ink = _rgba(layers["ink"])
    ia = ink[..., 3:4]
    rgb = ink[..., :3] * ia + rgb * (1 - ia)
    a = np.maximum(a, ink[..., 3])
    if use_matte:
        a = np.asarray(layers["matte"], dtype=np.float32) / 255
    out = np.dstack([rgb, a])
    return Image.fromarray(np.round(out * 255).astype(np.uint8), "RGBA")


def _edges(rgba):
    gray = (rgba[..., :3] @ np.array([0.299, 0.587, 0.114], np.float32)) * rgba[..., 3]
    return cv2.Canny(np.round(gray * 255).astype(np.uint8), 40, 120) > 0


def _edge_f1(src, out, tol=2):
    a, b = _edges(src), _edges(out)
    if not a.any() and not b.any():
        return 1.0
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * tol + 1, 2 * tol + 1))
    da, db = cv2.dilate(a.astype(np.uint8), k) > 0, cv2.dilate(b.astype(np.uint8), k) > 0
    precision = (b & da).sum() / max(1, b.sum())
    recall = (a & db).sum() / max(1, a.sum())
    return float(2 * precision * recall / max(1e-9, precision + recall))


def measure(source, rebuilt):
    """Source vs rebuilt RGBA: color error on shared opaque pixels, alpha IoU, edge F1 (2 px)."""
    src, out = _rgba(Image.open(source) if not isinstance(source, Image.Image) else source), _rgba(rebuilt)
    sa, oa = src[..., 3] > 0.5, out[..., 3] > 0.5
    both, union = sa & oa, sa | oa
    err = np.abs(src[..., :3][both] - out[..., :3][both]) * 255 if both.any() else np.array([255.0])
    return {"mean_color_error": round(float(err.mean()), 2),
            "p95_color_error": round(float(np.percentile(err.max(axis=-1), 95)), 2),
            "alpha_iou": round(float(both.sum() / max(1, union.sum())), 4),
            "edge_f1_2px": round(_edge_f1(src, out), 4)}


def extract(source, out_dir, *, colors=8, **scan_options):
    """Extract one cel into ``out_dir``: scan.json, drawing.svg, layer PNGs, composite, metrics."""
    source, out_dir = Path(source), Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    data = scan.scan_image(source, colors=colors, **scan_options)
    write_json(out_dir / "scan.json", data)
    (out_dir / "drawing.svg").write_text(to_svg(data), encoding="utf-8")
    layers = build_layers(data, source)
    paths = {}
    for name, image in layers.items():
        paths[name] = out_dir / f"{name}.png"
        image.save(paths[name])
    vector_only = composite(layers, use_shade=False, use_matte=False)
    vector_only.save(out_dir / "vector-only.png")
    report = {
        "kind": "reconstruction",
        "note": "Extracted from approved source pixels; not a newly drawn or model-authored drawing.",
        "source": rel(source), "source_sha256": sha256(source), "size": data["size"],
        "layers": {name: {"path": rel(paths[name]), "sha256": sha256(paths[name])} for name in LAYERS},
        "svg": rel(out_dir / "drawing.svg"), "composite": rel(paths["composite"]),
        "stats": data["stats"], "params": data["params"],
        "metrics": {"vector_only": measure(source, vector_only), "layered": measure(source, layers["composite"])},
        "seconds": round(time.perf_counter() - started, 2),
    }
    write_json(out_dir / "extract.json", report)
    return report


def contact_sheet(rows, out, *, cell=(220, 220), labels=("source", "vector-only", "layered")):
    """rows: list of tuples of image paths (same order as ``labels``) -> one PNG on mid-gray."""
    cw, ch = cell
    sheet = Image.new("RGBA", (cw * len(labels), ch * len(rows)), (128, 128, 128, 255))
    for r, paths in enumerate(rows):
        for c, path in enumerate(paths):
            image = Image.open(path).convert("RGBA")
            image.thumbnail((cw - 8, ch - 8), Image.Resampling.LANCZOS)
            sheet.alpha_composite(image, (c * cw + (cw - image.width) // 2, r * ch + (ch - image.height) // 2))
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(out)
    return out
