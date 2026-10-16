"""Front-view face construction from a character identity model.

The identity holds measured landmarks (eye corners, lids, iris centers, brow
arcs, mouth) and a palette sampled from approved art. ``construct`` turns a
small set of bounded expression parameters into new brow, eye and mouth
drawings. Every feature moves in coordinated units of the character's own
interocular distance, so the same expression keeps her proportions.

``erase_features`` paints the original features out of the reconstructed face
(OpenCV inpainting) so the new drawing is not a sticker over the old one.

Scope: one view (the identity's ``view``). A different head angle needs its own
identity model; this module refuses nothing silently but does not invent views.
"""
from __future__ import annotations

import numpy as np
from PIL import Image

from studio.drawing.schema import DrawingError, VERSION

try:
    import cv2
except ImportError:  # pragma: no cover
    cv2 = None

K = 0.5523  # cubic circle constant

# expression name -> bounded parameters (all in [-1, 1] except pupil)
EXPRESSIONS = {
    "neutral": {},
    "stern": {"brow_raise": -0.3, "brow_inner": -0.8, "lid_open": -0.2},
    "fear": {"brow_raise": 0.7, "brow_inner": 0.9, "lid_open": 0.8, "pupil": 0.7,
             "mouth_open": 0.55, "mouth_width": -0.15, "mouth_corner": -0.4},
    "surprise": {"brow_raise": 1.0, "brow_inner": 0.2, "lid_open": 1.0, "pupil": 0.85,
                 "mouth_open": 0.8, "mouth_width": -0.35},
    "sorrow": {"brow_raise": 0.2, "brow_inner": 1.0, "lid_open": -0.45, "gaze_y": 0.5,
               "mouth_corner": -0.7},
    "resolve": {"brow_raise": -0.5, "brow_inner": -0.6, "lid_open": -0.35, "mouth_width": 0.1,
                "mouth_corner": -0.15},
}
PARAMS = {"brow_raise": (-1, 1), "brow_inner": (-1, 1), "lid_open": (-1, 1), "gaze_x": (-1, 1),
          "gaze_y": (-1, 1), "pupil": (0.5, 1.2), "mouth_open": (0, 1), "mouth_width": (-1, 1),
          "mouth_corner": (-1, 1)}


def expression(name=None, **overrides):
    values = {"brow_raise": 0.0, "brow_inner": 0.0, "lid_open": 0.0, "gaze_x": 0.0, "gaze_y": 0.0,
              "pupil": 1.0, "mouth_open": 0.0, "mouth_width": 0.0, "mouth_corner": 0.0}
    if name is not None:
        if name not in EXPRESSIONS:
            raise DrawingError(f"unknown expression {name!r}; choose from {sorted(EXPRESSIONS)}")
        values.update(EXPRESSIONS[name])
    for key, value in overrides.items():
        if key not in PARAMS:
            raise DrawingError(f"unknown expression parameter {key!r}")
        lo, hi = PARAMS[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not lo <= value <= hi:
            raise DrawingError(f"{key}={value!r} outside [{lo}, {hi}]")
        values[key] = float(value)
    return values


# ------------------------------------------------------------------ geometry helpers

def _p(v):
    return [round(float(v[0]), 3), round(float(v[1]), 3)]


def _quad_to_cubic(a, c, b):
    a, c, b = (np.asarray(x, float) for x in (a, c, b))
    return [_p(a), _p(a + 2 / 3 * (c - a)), _p(b + 2 / 3 * (c - b)), _p(b)]


def _through(a, m, b):
    """Quadratic through a, m (at t=.5), b -> one cubic segment."""
    a, m, b = (np.asarray(x, float) for x in (a, m, b))
    return _quad_to_cubic(a, 2 * m - (a + b) / 2, b)


def _circle(c, r):
    cx, cy = c
    pts = [(cx + r, cy), (cx, cy + r), (cx - r, cy), (cx, cy - r)]
    segs = []
    for i in range(4):
        a, b = np.array(pts[i]), np.array(pts[(i + 1) % 4])
        ta = np.array([-(a[1] - cy), a[0] - cx]) / r
        tb = np.array([-(b[1] - cy), b[0] - cx]) / r
        segs.append([_p(a), _p(a + K * r * ta), _p(b - K * r * tb), _p(b)])
    return segs


def _closed(top, bottom_reversed):
    """Two cubic segments sharing endpoints -> closed fill curve."""
    return [top, bottom_reversed]


def _prim(pid, kind, curve, color, *, width=None, opacity=1.0, clip=None):
    prim = {"id": pid, "kind": kind, "curve": curve, "color": color, "provenance": "procedural",
            "opacity": opacity}
    if width is not None:
        prim["width"] = width
    if clip:
        prim["clip"] = clip
    return prim


# ------------------------------------------------------------------ construction

def construct(identity, expr, canvas=None):
    """Identity + expression params -> drawing IR (brows, eyes, mouth) in source pixel space."""
    L = {k: np.asarray(v, float) for k, v in identity["landmarks"].items()}
    C = identity["palette"]
    D = float(np.linalg.norm(L["eye_r.iris"] - L["eye_l.iris"]))  # interocular unit
    up = np.array([0.0, -1.0])
    prims = []

    for side, sgn in (("l", -1), ("r", 1)):  # sgn: direction from face center toward this side
        # ---- brow: raise whole brow, then lift/drop the inner end (worry vs. anger)
        outer, peak, inner = L[f"brow_{side}.outer"], L[f"brow_{side}.peak"], L[f"brow_{side}.inner"]
        lift = up * expr["brow_raise"] * 0.09 * D
        inner_n = inner + lift + up * expr["brow_inner"] * 0.11 * D + np.array([sgn * expr["brow_inner"] * 0.02 * D, 0])
        peak_n = peak + lift + up * expr["brow_inner"] * 0.03 * D
        outer_n = outer + lift - up * max(0.0, expr["brow_inner"]) * 0.02 * D
        prims.append(_prim(f"face.brow.{side}", "stroke", [_through(outer_n, peak_n, inner_n)], C["brow"],
                           width=[0.04 * D, 0.10 * D, 0.11 * D, 0.08 * D]))

        # ---- eye opening: corners fixed to the skull, lids open/close
        oc, ic = L[f"eye_{side}.outer"], L[f"eye_{side}.inner"]
        top, bot = L[f"eye_{side}.top"], L[f"eye_{side}.bottom"]
        mid = (oc + ic) / 2
        top_n = top + up * expr["lid_open"] * 0.07 * D
        bot_n = bot - up * max(0.0, expr["lid_open"]) * 0.025 * D
        upper = _through(oc, top_n, ic)
        lower = _through(ic, bot_n, oc)
        eye_id = f"face.eye.{side}.white"
        prims.append(_prim(eye_id, "fill", _closed(upper, lower), C["eye_white"]))

        # iris + pupil, clipped to the opening; gaze shifts within the socket
        iris_r = 0.125 * D
        gaze = np.array([expr["gaze_x"] * 0.06 * D, expr["gaze_y"] * 0.04 * D])
        iris_c = L[f"eye_{side}.iris"] + gaze
        prims.append(_prim(f"face.eye.{side}.iris", "fill", _circle(iris_c, iris_r), C["iris"], clip=eye_id))
        prims.append(_prim(f"face.eye.{side}.iris_shadow", "fill",
                           _circle(iris_c + np.array([0, -0.35 * iris_r]), iris_r * 0.85), C["iris_dark"],
                           opacity=0.55, clip=eye_id))
        prims.append(_prim(f"face.eye.{side}.pupil", "fill", _circle(iris_c, iris_r * 0.42 * expr["pupil"]),
                           C["pupil"], clip=eye_id))
        prims.append(_prim(f"face.eye.{side}.highlight", "fill",
                           _circle(iris_c + np.array([-0.3 * iris_r, -0.4 * iris_r]), iris_r * 0.24),
                           "#ffffff", clip=eye_id))

        # ---- ink: heavy upper lash line with outer flick, light lower lid, lid crease
        flick = oc + np.array([sgn * 0.06 * D, -0.035 * D])
        prims.append(_prim(f"face.eye.{side}.lash", "stroke",
                           [_through(oc, top_n + up * 0.01 * D, ic)], C["ink"],
                           width=[0.09 * D, 0.14 * D, 0.10 * D, 0.04 * D]))
        prims.append(_prim(f"face.eye.{side}.flick", "stroke", [_through(oc + (ic - oc) * 0.05, (oc + flick) / 2, flick)],
                           C["ink"], width=[0.06 * D, 0.01 * D]))
        prims.append(_prim(f"face.eye.{side}.lower", "stroke",
                           [_through(oc + (ic - oc) * 0.15, bot_n, ic - (ic - oc) * 0.2)], C["ink_soft"],
                           width=[0.005 * D, 0.03 * D, 0.005 * D], opacity=0.8))
        crease_top = top_n + up * (0.07 + 0.03 * max(0.0, expr["lid_open"])) * D
        prims.append(_prim(f"face.eye.{side}.crease", "stroke",
                           [_through(oc + (mid - oc) * 0.25 + up * 0.04 * D, crease_top, ic + up * 0.03 * D)],
                           C["ink_soft"], width=[0.005 * D, 0.025 * D, 0.005 * D], opacity=0.7))

    # ---- mouth: corners stay on the jaw, width/corner/opening change together
    ml, mr = L["mouth.l"], L["mouth.r"]
    center = (ml + mr) / 2
    half = (mr - ml) / 2 * (1 + expr["mouth_width"] * 0.18)
    corner_drop = -up * (-expr["mouth_corner"]) * 0.05 * D  # negative corner -> corners pulled down
    ml_n, mr_n = center - half + corner_drop, center + half + corner_drop
    opening = expr["mouth_open"] * 0.22 * D
    if opening > 0.5:
        top_mid = center + up * opening * 0.25
        bot_mid = center - up * opening
        mouth_id = "face.mouth.interior"
        prims.append(_prim(mouth_id, "fill", _closed(_through(ml_n, top_mid, mr_n), _through(mr_n, bot_mid, ml_n)),
                           C["mouth_dark"]))
        prims.append(_prim("face.mouth.teeth", "fill",
                           _closed(_through(ml_n, top_mid, mr_n), _through(mr_n, top_mid - up * opening * 0.3, ml_n)),
                           C["teeth"], clip=mouth_id, opacity=0.9))
        prims.append(_prim("face.mouth.lower_lip", "fill",
                           _closed(_through(mr_n - half * 0.15, bot_mid - up * 0.005 * D, ml_n + half * 0.15),
                                   _through(ml_n + half * 0.15, bot_mid - up * 0.12 * D, mr_n - half * 0.15)),
                           C.get("lip_lower", C["lip_shadow"]), opacity=0.85))
        prims.append(_prim("face.mouth.upper_line", "stroke", [_through(ml_n, top_mid + up * 0.01 * D, mr_n)],
                           C["ink"], width=[0.015 * D, 0.045 * D, 0.045 * D, 0.015 * D]))
        prims.append(_prim("face.mouth.lower_line", "stroke",
                           [_through(ml_n + half * 0.25, bot_mid - up * 0.01 * D, mr_n - half * 0.25)],
                           C["ink_soft"], width=[0.005 * D, 0.025 * D, 0.005 * D], opacity=0.6))
    else:
        bend = center + up * 0.01 * D
        prims.append(_prim("face.mouth.line", "stroke", [_through(ml_n, bend, mr_n)], C["ink"],
                           width=[0.015 * D, 0.05 * D, 0.05 * D, 0.015 * D]))
    lip = L["mouth.bottom"] - up * opening * 0.9
    prims.append(_prim("face.mouth.lower_lip_shade", "stroke",
                       [_through(center - half * 0.45 - up * (opening + 0.06 * D), lip, center + half * 0.45 - up * (opening + 0.06 * D))],
                       C["lip_shadow"], width=[0.01 * D, 0.05 * D, 0.01 * D], opacity=0.5))

    w, h = canvas or identity["canvas"]
    return {"version": VERSION, "canvas": [int(w), int(h)], "character": identity["character"],
            "view": identity["view"], "expression": {k: round(v, 3) for k, v in expr.items()},
            "primitives": prims}


def feature_mask(identity, size, grow=1.0):
    """Mask (uint8 0/255) covering original brows, eyes and mouth, for inpainting."""
    L = {k: np.asarray(v, float) for k, v in identity["landmarks"].items()}
    D = float(np.linalg.norm(L["eye_r.iris"] - L["eye_l.iris"]))
    m = np.zeros((size[1], size[0]), np.uint8)
    pad = 0.06 * D * grow
    for side in ("l", "r"):
        brow = np.array([L[f"brow_{side}.outer"], L[f"brow_{side}.peak"], L[f"brow_{side}.inner"]])
        cv2.polylines(m, [np.round(brow).astype(np.int32)], False, 255, thickness=int(round(0.2 * D * grow)))
        pts = np.array([L[f"eye_{side}.outer"], L[f"eye_{side}.top"], L[f"eye_{side}.inner"], L[f"eye_{side}.bottom"]])
        c = pts.mean(0)
        hull = c + (pts - c) * 1.0 + np.sign(pts - c) * pad
        hull[1] += [0, -0.09 * D * grow]  # lid crease above
        cv2.fillPoly(m, [np.round(hull).astype(np.int32)], 255)
    mouth = np.array([L["mouth.l"], L["mouth.top"], L["mouth.r"], L["mouth.bottom"]])
    c = mouth.mean(0)
    cv2.fillPoly(m, [np.round(c + (mouth - c) * 1.15 + np.sign(mouth - c) * pad).astype(np.int32)], 255)
    m = cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    # keep the erase inside the face: past the brow ends lies hair, and inpainting
    # there drags dark curls across the skin
    x_lo = int(L["brow_l.outer"][0] + 0.04 * D)
    x_hi = int(L["brow_r.outer"][0] - 0.04 * D)
    m[:, :max(0, x_lo)] = 0
    m[:, x_hi:] = 0
    return m


def erase_features(image, identity, radius=6):
    """Inpaint the original features away -> clean face plate (RGBA in, RGBA out).

    The mask is grown so no dark brow/lash residue seeds the fill, then the
    painted grain of a clean cheek patch is added back so the erased area is not
    an airbrushed blur next to textured skin."""
    rgba = np.asarray(image.convert("RGBA"))
    mask = cv2.dilate(feature_mask(identity, image.size),
                      cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
    rgb = cv2.inpaint(np.ascontiguousarray(rgba[..., :3]), mask, radius, cv2.INPAINT_NS).astype(np.float32)
    cheek = identity.get("skin_patch")
    if cheek:
        x0, y0, x1, y1 = cheek
        patch = rgba[y0:y1, x0:x1, :3].astype(np.float32)
        grain = patch - cv2.GaussianBlur(patch, (0, 0), 2.0)  # high-pass texture only, no color
        reps = (rgb.shape[0] // grain.shape[0] + 1, rgb.shape[1] // grain.shape[1] + 1, 1)
        tiled = np.tile(grain, reps)[:rgb.shape[0], :rgb.shape[1]]
        soft = cv2.GaussianBlur(mask.astype(np.float32) / 255, (0, 0), 2.0)[..., None]
        rgb = rgb + tiled * soft
    rgb = np.clip(rgb, 0, 255).astype(np.uint8)
    return Image.fromarray(np.dstack([rgb, rgba[..., 3]]), "RGBA"), mask


# ------------------------------------------------------------------ source-guided features

def _quad(a, m, b, n=64):
    a, m, b = (np.asarray(x, float) for x in (a, m, b))
    c = 2 * m - (a + b) / 2
    t = np.linspace(0, 1, n)[:, None]
    return (1 - t) ** 2 * a + 2 * (1 - t) * t * c + t * t * b


def warp_feature(source, old3, new3, band, *, dark_luma, light_luma):
    """Bend the source pixels of a stroke-like feature (brow, closed lips) from one curve to another.

    old3/new3: (outer, middle, inner) points. ``band``: half-thickness in px of the
    feature around its curve. Alpha comes from source darkness, so the artist's
    own hair texture and taper are kept. Returns an RGBA layer. This is a
    transformation of source art, recorded as ``source-warped``, not new drawing."""
    src = np.asarray(source.convert("RGBA")).astype(np.float32)
    h, w = src.shape[:2]
    old, new = _quad(*old3), _quad(*new3)
    lo = np.floor(np.minimum(old.min(0), new.min(0)) - band * 2).astype(int).clip(0)
    hi = np.ceil(np.maximum(old.max(0), new.max(0)) + band * 2).astype(int)
    hi = np.minimum(hi, [w - 1, h - 1])
    ys, xs = np.mgrid[lo[1]:hi[1] + 1, lo[0]:hi[0] + 1].astype(np.float32)
    pix = np.stack([xs, ys], -1)
    d = np.linalg.norm(pix[..., None, :] - new[None, None], axis=-1)
    t = d.argmin(-1)
    dist = d.min(-1)
    offset = old[t] - new[t]  # inverse map: output pixel -> where it was in the source
    map_x = (xs + offset[..., 0]).astype(np.float32)
    map_y = (ys + offset[..., 1]).astype(np.float32)
    crop = cv2.remap(src, map_x, map_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    luma = crop[..., :3] @ np.array([0.299, 0.587, 0.114], np.float32)
    alpha = np.clip((light_luma - luma) / max(1.0, light_luma - dark_luma), 0, 1)
    endfade = np.minimum(t, len(new) - 1 - t) / 4.0  # soften the cut at both ends of the feature
    alpha *= np.clip((band - dist) / 2.0 + 0.5, 0, 1) * np.clip(endfade, 0, 1)
    layer = np.zeros((h, w, 4), np.float32)
    layer[lo[1]:hi[1] + 1, lo[0]:hi[0] + 1, :3] = crop[..., :3]
    layer[lo[1]:hi[1] + 1, lo[0]:hi[0] + 1, 3] = alpha * 255
    return Image.fromarray(layer.astype(np.uint8), "RGBA")


def brow_curves(identity, expr):
    """Old and new (outer, peak, inner) brow points, using the same rules as ``construct``."""
    L = {k: np.asarray(v, float) for k, v in identity["landmarks"].items()}
    D = float(np.linalg.norm(L["eye_r.iris"] - L["eye_l.iris"]))
    up = np.array([0.0, -1.0])
    out = {}
    for side, sgn in (("l", -1), ("r", 1)):
        outer, peak, inner = L[f"brow_{side}.outer"], L[f"brow_{side}.peak"], L[f"brow_{side}.inner"]
        lift = up * expr["brow_raise"] * 0.09 * D
        inner_n = inner + lift + up * expr["brow_inner"] * 0.11 * D + np.array([sgn * expr["brow_inner"] * 0.02 * D, 0])
        peak_n = peak + lift + up * expr["brow_inner"] * 0.03 * D
        outer_n = outer + lift - up * max(0.0, expr["brow_inner"]) * 0.02 * D
        out[side] = ((outer, peak, inner), (outer_n, peak_n, inner_n))
    return out, D


def compose(identity, expr, source=None, plate=None):
    """Full V2 face: clean plate + source-warped brows/closed lips + procedural eyes/open mouth.

    Returns (image, drawing_ir, authorship) where authorship lists each feature's origin."""
    source = source or Image.open(identity["source"]).convert("RGBA")
    if plate is None:
        plate, _ = erase_features(source, identity)
    canvas = plate.copy()
    authorship = {}
    skin = float(np.dot(_hex(identity["palette"]["skin"]), [0.299, 0.587, 0.114]))
    curves, D = brow_curves(identity, expr)
    for side, (old3, new3) in curves.items():
        layer = warp_feature(source, old3, new3, band=0.10 * D, dark_luma=10, light_luma=skin * 0.92)
        canvas.alpha_composite(layer)
        authorship[f"face.brow.{side}"] = "source-warped"
    drawing = construct(identity, expr)
    keep = []
    for prim in drawing["primitives"]:
        if prim["id"].startswith("face.brow."):
            continue  # brows come from the artist's pixels above
        if prim["id"].startswith("face.mouth.") and expr["mouth_open"] * 0.22 * D <= 0.5:
            continue  # closed mouth: use the artist's lips below
        keep.append(prim)
        authorship[prim["id"]] = "procedural"
    if expr["mouth_open"] * 0.22 * D <= 0.5:
        L = {k: np.asarray(v, float) for k, v in identity["landmarks"].items()}
        up = np.array([0.0, -1.0])
        ml, mr, top, bot = L["mouth.l"], L["mouth.r"], L["mouth.top"], L["mouth.bottom"]
        center = (ml + mr) / 2
        half = (mr - ml) / 2 * (1 + expr["mouth_width"] * 0.18)
        drop = -up * (-expr["mouth_corner"]) * 0.05 * D
        lips_mid = (top + bot) / 2
        # warp a full-lip band, keyed on lip darkness vs skin so both lips come along
        layer = warp_feature(source, (ml, lips_mid, mr), (center - half + drop, lips_mid, center + half + drop),
                             band=float(np.linalg.norm(bot - top)) * 0.75, dark_luma=20, light_luma=skin * 1.02)
        canvas.alpha_composite(layer)
        authorship["face.mouth"] = "source-warped"
    drawing["primitives"] = keep
    from studio.drawing import render
    image = render.render(drawing, base=canvas)
    return image, drawing, authorship


def _hex(c):
    c = c.lstrip("#")
    return np.array([int(c[i:i + 2], 16) for i in (0, 2, 4)], float)
