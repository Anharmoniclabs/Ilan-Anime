"""Versioned drawing IR: identity models (canonical, pose-independent) and drawings (frame-local).

A *drawing* is an ordered list of primitives. Each primitive has a stable
component id (``face.brow.left``) so poses can be put in correspondence, and a
``provenance`` saying who authored it:

* ``source``      pixels/vectors extracted from approved art;
* ``procedural``  built by engine code from an identity model + parameters;
* ``model``       geometry or parameters chosen by a language/vision model.

Validation is strict and bounded: the IR is data, never code.
"""
from __future__ import annotations

import math
import re

VERSION = 1
PROVENANCE = {"source", "procedural", "model"}
KINDS = {"stroke", "fill"}
ID_RE = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z0-9_]+)*$")
HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")
MAX_PRIMITIVES = 2000
MAX_SEGMENTS = 400        # cubic segments per primitive
MAX_TOTAL_SEGMENTS = 40000
MAX_WIDTH = 64.0


class DrawingError(ValueError):
    pass


def _num(value, lo, hi, what):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise DrawingError(f"{what}: not a finite number: {value!r}")
    if not lo <= value <= hi:
        raise DrawingError(f"{what}: {value} outside [{lo}, {hi}]")
    return float(value)


def _point(p, w, h, what):
    if not isinstance(p, (list, tuple)) or len(p) != 2:
        raise DrawingError(f"{what}: point must be [x, y]")
    margin = max(w, h)
    return (_num(p[0], -margin, w + margin, what + ".x"), _num(p[1], -margin, h + margin, what + ".y"))


def validate_drawing(drawing):
    """Raise DrawingError on any malformed field; return the drawing on success."""
    if not isinstance(drawing, dict) or drawing.get("version") != VERSION:
        raise DrawingError(f"drawing must be a dict with version {VERSION}")
    size = drawing.get("canvas")
    if not (isinstance(size, list) and len(size) == 2 and all(isinstance(v, int) and 16 <= v <= 8192 for v in size)):
        raise DrawingError("canvas must be [w, h] integers in 16..8192")
    w, h = size
    prims = drawing.get("primitives")
    if not isinstance(prims, list) or not prims:
        raise DrawingError("primitives must be a non-empty list")
    if len(prims) > MAX_PRIMITIVES:
        raise DrawingError(f"too many primitives: {len(prims)} > {MAX_PRIMITIVES}")
    seen, fills_seen, total = set(), set(), 0
    for i, prim in enumerate(prims):
        where = f"primitives[{i}]"
        if not isinstance(prim, dict):
            raise DrawingError(f"{where}: must be an object")
        pid = prim.get("id")
        if not isinstance(pid, str) or not ID_RE.match(pid):
            raise DrawingError(f"{where}: invalid id {pid!r} (lowercase dotted, e.g. face.brow.left)")
        if pid in seen:
            raise DrawingError(f"{where}: duplicate id {pid}")
        seen.add(pid)
        if prim.get("kind") not in KINDS:
            raise DrawingError(f"{pid}: kind must be one of {sorted(KINDS)}")
        if prim.get("provenance") not in PROVENANCE:
            raise DrawingError(f"{pid}: provenance must be one of {sorted(PROVENANCE)}")
        if not isinstance(prim.get("color"), str) or not HEX_RE.match(prim["color"]):
            raise DrawingError(f"{pid}: color must be #rrggbb")
        _num(prim.get("opacity", 1.0), 0, 1, pid + ".opacity")
        segs = prim.get("curve")
        if not isinstance(segs, list) or not segs:
            raise DrawingError(f"{pid}: curve must be a non-empty list of cubic segments")
        if len(segs) > MAX_SEGMENTS:
            raise DrawingError(f"{pid}: {len(segs)} segments > {MAX_SEGMENTS}")
        total += len(segs)
        for j, seg in enumerate(segs):
            if not isinstance(seg, list) or len(seg) != 4:
                raise DrawingError(f"{pid}.curve[{j}]: cubic segment needs 4 points")
            pts = [_point(p, w, h, f"{pid}.curve[{j}][{k}]") for k, p in enumerate(seg)]
            if j and pts[0] != tuple(float(v) for v in segs[j - 1][3]):
                raise DrawingError(f"{pid}.curve[{j}]: does not start where previous segment ends")
        clip = prim.get("clip")
        if clip is not None and clip not in fills_seen:
            raise DrawingError(f"{pid}: clip {clip!r} must name an earlier fill")
        if prim["kind"] == "fill":
            fills_seen.add(pid)
            if tuple(segs[0][0]) != tuple(segs[-1][3]):
                raise DrawingError(f"{pid}: fill must be closed")
        else:
            widths = prim.get("width")
            if not (isinstance(widths, list) and len(widths) >= 2):
                raise DrawingError(f"{pid}: stroke width profile needs >= 2 values")
            for k, v in enumerate(widths):
                _num(v, 0, MAX_WIDTH, f"{pid}.width[{k}]")
    if total > MAX_TOTAL_SEGMENTS:
        raise DrawingError(f"total segments {total} > {MAX_TOTAL_SEGMENTS}")
    return drawing


def validate_identity(identity):
    """Identity models hold named landmarks in source-image pixels plus sampled palette."""
    for key in ("character", "view", "source", "source_sha256", "landmarks", "palette", "status"):
        if key not in identity:
            raise DrawingError(f"identity missing {key}")
    if identity["status"] not in {"candidate", "author-approved"}:
        raise DrawingError("identity status must be candidate or author-approved")
    for name, p in identity["landmarks"].items():
        if not ID_RE.match(name):
            raise DrawingError(f"bad landmark name {name!r}")
        _point(p, 10000, 10000, "landmark " + name)
    for name, c in identity["palette"].items():
        if not HEX_RE.match(c):
            raise DrawingError(f"palette {name}: bad color {c!r}")
    return identity
