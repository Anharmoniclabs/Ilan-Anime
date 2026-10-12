"""Frame-pure layer compositor (spec v2, reads v1 compose.py specs).

Everything is a pure function of the integer frame number:

* each layer has its own drawing clock (``rate``: on 1s/2s/3s...), so a held
  drawing never moves between its exposures unless ``smooth`` is set;
* the camera is evaluated on every frame and folded into each layer's affine
  transform, scaled by the layer's ``parallax`` (multiplane), so every layer is
  resampled exactly once;
* rotation and scale happen about the layer ``pivot`` in **source pixels**
  (the v1 compositor ignored scale for pivots and clipped rotated cutouts);
* blend modes: normal, add, screen, multiply, lighten;
* layer tags (``line``, ``shade``, ``highlight``, ``bg``, ``character``) let the
  PRESS state change drawing style instead of only desaturating.

See ``docs/ENGINE.md`` for the full spec format.
"""
from __future__ import annotations

from functools import lru_cache
import hashlib
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

from studio.paths import resolve
from studio.engine import fx as fxlib
from studio.engine import post as postlib

LAYER_DEFAULTS = {"x": 0.0, "y": 0.0, "scale": 1.0, "angle": 0.0, "opacity": 1.0}
CAMERA_DEFAULTS = {"x": 0.0, "y": 0.0, "scale": 1.0, "angle": 0.0}
BLENDS = {"normal", "add", "screen", "multiply", "lighten"}


class SpecError(ValueError):
    """Invalid shot specification."""


def seed_for(*parts) -> int:
    digest = hashlib.sha256("|".join(map(str, parts)).encode()).digest()
    return int.from_bytes(digest[:4], "little")


def _ease(t: float, ease: str | None) -> float:
    if ease == "hold":
        return 0.0
    if ease == "smooth":
        return t * t * (3 - 2 * t)
    if ease == "ease_in":
        return t * t
    if ease == "ease_out":
        return 1 - (1 - t) * (1 - t)
    return t


def interpolate(keys, frame, defaults):
    """Interpolate key dictionaries at ``frame``. Missing fields take defaults.

    The ``ease`` of the earlier key shapes the segment that follows it.
    """
    if not keys:
        return dict(defaults)
    keys = sorted(keys, key=lambda k: k["frame"])
    if frame <= keys[0]["frame"]:
        a = b = keys[0]
    elif frame >= keys[-1]["frame"]:
        a = b = keys[-1]
    else:
        a = keys[0]
        b = keys[-1]
        for key in keys:
            if key["frame"] <= frame:
                a = key
            if key["frame"] >= frame:
                b = key
                break
    span = b["frame"] - a["frame"]
    t = 0.0 if span == 0 else (frame - a["frame"]) / span
    t = _ease(t, a.get("ease"))
    return {k: a.get(k, v) + (b.get(k, v) - a.get(k, v)) * t for k, v in defaults.items()}


def _hex(color, default=(1.0, 1.0, 1.0)):
    if color is None:
        return default
    if isinstance(color, str):
        color = color.lstrip("#")
        return tuple(int(color[i:i + 2], 16) / 255 for i in (0, 2, 4))
    values = list(color)[:3]
    scale = 255.0 if max(values) > 1 else 1.0
    return tuple(v / scale for v in values)


def _affine(matrix):
    """Forward 2x3 -> PIL inverse coefficients."""
    a, b, c, d, e, f = matrix
    det = a * e - b * d
    if abs(det) < 1e-12:
        raise SpecError("Degenerate transform (scale 0)")
    ia, ib, id_, ie = e / det, -b / det, -d / det, a / det
    return (ia, ib, -(ia * c + ib * f), id_, ie, -(id_ * c + ie * f))


def _mul(m1, m2):
    """Compose forward affines: m1 after m2."""
    a1, b1, c1, d1, e1, f1 = m1
    a2, b2, c2, d2, e2, f2 = m2
    return (a1 * a2 + b1 * d2, a1 * b2 + b1 * e2, a1 * c2 + b1 * f2 + c1,
            d1 * a2 + e1 * d2, d1 * b2 + e1 * e2, d1 * c2 + e1 * f2 + f1)


def _rotation(degrees):
    """Visually counter-clockwise rotation in y-down screen space."""
    r = math.radians(degrees)
    return math.cos(r), math.sin(r)


class Compositor:
    """Render frames of one shot specification."""

    def __init__(self, spec: dict, base: Path | None = None, quality: str = "final", scale: float = 1.0):
        """``scale`` renders a proportionally smaller frame (e.g. 0.5 for previews)."""
        if quality not in ("draft", "final"):
            raise SpecError("quality must be draft or final")
        if not 0 < float(scale) <= 1:
            raise SpecError("scale must be in (0, 1]")
        self.resample = Image.Resampling.BILINEAR if quality == "draft" else Image.Resampling.BICUBIC
        self.spec = spec
        self.base = Path(base) if base else None
        self.spec_size = tuple(int(v) for v in spec.get("size", [1280, 720]))
        self.out_scale = float(scale)
        self.size = tuple(max(2, int(round(v * self.out_scale / 2)) * 2) for v in self.spec_size)
        self.frames = int(spec["frames"])
        self.shot_id = spec.get("id", "shot")
        background = spec.get("background", [20, 32, 43, 255])
        self.background = np.array(_hex(background[:3] if not isinstance(background, str) else background),
                                   dtype=np.float32)
        self.layers = [self._normalize(layer, i) for i, layer in enumerate(spec.get("layers", []))]
        self._by_name = {layer["name"]: layer for layer in self.layers}
        if len(self._by_name) != len(self.layers):
            raise SpecError("layer names must be unique")
        self.post = postlib.PostStack(spec.get("post", {}), self.size, self.shot_id, self.frames)
        self._images: dict = {}
        self._layer_cache: dict = {}
        self._validate()

    # ------------------------------------------------------------------ spec
    def _normalize(self, layer, index):
        layer = dict(layer)
        layer.setdefault("name", f"layer{index}")
        if layer.pop("fit_canvas", False):
            layer.setdefault("fit", "stretch")
        layer.setdefault("fit", "none")
        layer.setdefault("rate", 3)
        layer.setdefault("blend", "normal")
        layer.setdefault("parallax", 0.0 if layer.get("screen_space") else 1.0)
        layer.setdefault("tags", [])
        return layer

    def _validate(self):
        if self.frames <= 0:
            raise SpecError("frames must be positive")
        if self.spec_size[0] % 2 or self.spec_size[1] % 2:
            raise SpecError("size must be even for yuv420p delivery")
        for layer in self.layers:
            if layer["blend"] not in BLENDS:
                raise SpecError(f"{layer['name']}: unknown blend {layer['blend']}")
            if int(layer["rate"]) < 1:
                raise SpecError(f"{layer['name']}: rate must be >= 1")
            if not any(k in layer for k in ("source", "sequence", "exposures", "generator")):
                raise SpecError(f"{layer['name']}: needs source, sequence, exposures or generator")
            if layer.get("generator") and layer["generator"].get("type") not in fxlib.GENERATORS:
                raise SpecError(f"{layer['name']}: unknown generator {layer['generator'].get('type')}")

    # ---------------------------------------------------------------- images
    def _load(self, path, fit):
        key = (path, fit)
        if key not in self._images:
            full = resolve(path, self.base)
            if not full.is_file():
                raise SpecError(f"Missing image: {path}")
            image = Image.open(full).convert("RGBA")
            if fit != "none":
                image = _fit(image, self.spec_size, fit)
            if image.getchannel("A").getextrema() == (255, 255):
                image = image.convert("RGB")  # opaque plate: cheaper resampling, no matte
            self._images[key] = image
        return self._images[key]

    # ---------------------------------------------------------------- frames
    def layer_state(self, layer, frame, press):
        """Return (drawing source or generator key, quantized local frame, keys) or None."""
        start = int(layer.get("in", 0))
        end = int(layer.get("out", self.frames))
        if not start <= frame < end:
            return None
        rate = int(layer["rate"])
        if press >= 0.8 and ("character" in layer["tags"] or "line" in layer["tags"]):
            rate = max(rate, 6)  # PRESS: drawings slow to holds
        local = frame - start
        q = local // rate * rate
        source = layer.get("source")
        if layer.get("sequence"):
            bank = layer["sequence"]
            index = local // rate
            index = index % len(bank) if layer.get("loop") else min(index, len(bank) - 1)
            source = bank[index]
        for exposure in layer.get("exposures", []):
            if exposure["start"] <= q < exposure["end"]:
                source = exposure["source"]
                break
        key_frame = local if layer.get("smooth") else q
        params = interpolate(layer.get("keys", []), key_frame, LAYER_DEFAULTS)
        if layer.get("generator"):
            return ("gen", q), q, params
        if not source:
            return None
        return ("img", source), q, params

    def _press(self, frame):
        return float(np.clip(self.post.value("press", frame, 0.0), 0.0, 1.0))

    def camera(self, frame):
        cam = interpolate(self.spec.get("camera", []), frame, CAMERA_DEFAULTS)
        dx, dy, droll = postlib.camera_shake(self.spec.get("shake", []), frame, self.shot_id)
        cam["x"] += dx
        cam["y"] += dy
        cam["angle"] += droll
        return cam

    def _image_size(self, layer):
        if layer.get("generator"):
            return self.spec_size
        source = layer.get("source") or (layer.get("sequence") or [None])[0] or \
            (layer.get("exposures") or [{}])[0].get("source")
        return self._load(source, layer["fit"]).size

    def local_matrix(self, layer, params, image_size, frame, depth=0):
        """Layer -> spec-canvas affine, including any ``parent`` chain (no camera)."""
        w, h = image_size
        px, py = layer.get("pivot", [w / 2, h / 2])
        s = float(params["scale"])
        cos_r, sin_r = _rotation(params["angle"])
        # layer: canvas = (x,y) + pivot + R*s*(src - pivot)
        a, b = s * cos_r, s * sin_r
        d, e = -s * sin_r, s * cos_r
        tx = params["x"] + px - (a * px + b * py)
        ty = params["y"] + py - (d * px + e * py)
        m = (a, b, tx, d, e, ty)
        parent_name = layer.get("parent")
        if parent_name:
            if depth > 8:
                raise SpecError("parent chain too deep or cyclic")
            parent = self._by_name.get(parent_name)
            if parent is None:
                raise SpecError(f"{layer['name']}: unknown parent {parent_name}")
            local = frame - int(parent.get("in", 0))
            rate = int(parent["rate"])
            key_frame = local if parent.get("smooth") else local // rate * rate
            pparams = interpolate(parent.get("keys", []), key_frame, LAYER_DEFAULTS)
            # Child coordinates are relative to the parent's untransformed image.
            pm = self.local_matrix(parent, pparams, self._image_size(parent), frame, depth + 1)
            m = _mul(pm, m)
        return m

    def _matrix(self, layer, image_size, params, cam, press, frame=0):
        layer_m = self.local_matrix(layer, params, image_size, frame)
        k = float(layer["parallax"])
        if press > 0 and k != 0:
            k = 1 + (k - 1) * (1 - press)  # PRESS collapses depth
        o = self.out_scale
        out_m = (o, 0.0, 0.0, 0.0, o, 0.0)
        if k == 0:
            return _mul(out_m, layer_m)
        cw, ch = self.spec_size
        cx, cy = cw / 2, ch / 2
        z = 1 + (float(cam["scale"]) - 1) * k
        cr, sr = _rotation(cam["angle"])
        # camera: out = C + z*(Rc(in - C) + cam*k)
        ca, cb, cd, ce = z * cr, z * sr, -z * sr, z * cr
        ctx = cx + z * cam["x"] * k - (ca * cx + cb * cy)
        cty = cy + z * cam["y"] * k - (cd * cx + ce * cy)
        return _mul(out_m, _mul((ca, cb, ctx, cd, ce, cty), layer_m))

    def _render_layer(self, layer, state, params, cam, press, frame):
        token, q, _ = state
        image = None
        if token[0] == "gen":
            token = ("gen", fxlib.state(layer["generator"], q))
            image_size = self.spec_size
        else:
            image = self._load(token[1], layer["fit"])
            image_size = image.size
        m = self._matrix(layer, image_size, params, cam, press, frame)
        rounded = tuple(round(v, 4) for v in m)
        matrix_key = (layer["name"], token, rounded, round(params["opacity"], 4), round(press, 3))
        cached = self._layer_cache.get(layer["name"])
        if cached and cached[0] == matrix_key:
            return cached[1]
        if image is None:
            image = fxlib.render(layer["generator"], q, self.spec_size, layer, self)
        a, b, c, d, e, f = m
        w, h = self.size
        integer = (abs(a - 1) < 1e-9 and abs(e - 1) < 1e-9 and abs(b) < 1e-9 and abs(d) < 1e-9
                   and abs(c - round(c)) < 1e-6 and abs(f - round(f)) < 1e-6)
        if image.mode == "RGB":
            covered = _covers(m, image.size, self.size)
            if integer:
                out = Image.new("RGB", self.size)
                out.paste(image, (int(round(c)), int(round(f))))
            else:
                out = image.transform(self.size, Image.Transform.AFFINE, _affine(m),
                                      resample=self.resample)
            rgb = np.asarray(out, dtype=np.float32) * (1 / 255)
            if covered:
                alpha = np.ones((h, w, 1), dtype=np.float32)
            else:
                mask = Image.new("L", image.size, 255)
                if integer:
                    full = Image.new("L", self.size, 0)
                    full.paste(mask, (int(round(c)), int(round(f))))
                else:
                    full = mask.transform(self.size, Image.Transform.AFFINE, _affine(m),
                                          resample=Image.Resampling.BILINEAR, fillcolor=0)
                alpha = np.asarray(full, dtype=np.float32)[..., None] * (1 / 255)
        else:
            covered = False
            if integer:
                out = Image.new("RGBA", self.size, (0, 0, 0, 0))
                out.paste(image, (int(round(c)), int(round(f))))
            else:
                out = image.transform(self.size, Image.Transform.AFFINE, _affine(m),
                                      resample=self.resample, fillcolor=(0, 0, 0, 0))
            box = out.getchannel("A").getbbox()
            if box is None:
                self._layer_cache[layer["name"]] = (matrix_key, None)
                return None
            if layer.get("effects") or (press > 0 and layer["tags"]):
                box = (0, 0, w, h)  # effects and PRESS styles need the whole layer
            arr = np.asarray(out.crop(box), dtype=np.float32) * (1 / 255)
            rgb, alpha = arr[..., :3], arr[..., 3:4]
        scale = float(params["opacity"]) * float(layer.get("opacity", 1.0))
        if scale != 1.0:
            alpha = alpha * scale
        opaque = image.mode == "RGB" and covered and scale == 1.0
        if image.mode == "RGB":
            box = (0, 0, w, h)
        rgb, alpha = _press_style(layer, rgb, alpha, press)
        if press > 0 and ("shade" in layer["tags"] or "highlight" in layer["tags"] or "line" in layer["tags"]):
            opaque = False
        result = (rgb, alpha, opaque, box)
        self._layer_cache[layer["name"]] = (matrix_key, result)
        return result

    def draw_array(self, frame: int) -> np.ndarray:
        """Composite frame -> float32 RGB array in [0, 1] (before post)."""
        frame = int(frame)
        source_frame = self.post.source_frame(frame)
        press = self._press(source_frame)
        cam = self.camera(source_frame)
        canvas = np.empty((self.size[1], self.size[0], 3), dtype=np.float32)
        canvas[...] = self.background
        for layer in self.layers:
            state = self.layer_state(layer, source_frame, press)
            if state is None:
                continue
            rendered = self._render_layer(layer, state, state[2], cam, press, source_frame)
            if rendered is None:
                continue
            rgb, alpha, opaque, (x0, y0, x1, y1) = rendered
            if opaque and layer["blend"] == "normal" and not layer.get("effects"):
                canvas = rgb.copy()
                continue
            if layer.get("effects"):
                canvas = _apply_effects_before(layer, canvas, alpha)
                canvas = _blend(canvas, rgb, alpha, layer["blend"])
                canvas = _apply_effects_after(layer, canvas, rgb, alpha)
            else:
                region = canvas[y0:y1, x0:x1]
                canvas[y0:y1, x0:x1] = _blend(region, rgb, alpha, layer["blend"])
        return canvas

    def draw(self, frame: int) -> Image.Image:
        """Composite + post -> RGB PIL image."""
        canvas = self.draw_array(frame)
        canvas = self.post.apply(canvas, int(frame), self)
        image = Image.fromarray((np.clip(canvas, 0, 1) * 255 + 0.5).astype(np.uint8), "RGB")
        dx, dy = self.post.weave_offset(int(frame))
        if dx or dy:
            # GATE_WEAVE: sub-pixel frame shift; a 0.4% overscan hides the edges.
            w, h = self.size
            z = 1.004
            image = image.transform(self.size, Image.Transform.AFFINE,
                                    (1 / z, 0, w / 2 - w / (2 * z) - dx, 0, 1 / z, h / 2 - h / (2 * z) - dy),
                                    resample=Image.Resampling.BILINEAR)
        return image


# ---------------------------------------------------------------- helpers

def _fit(image, size, mode):
    w, h = size
    if mode == "stretch":
        return image.resize((w, h), Image.Resampling.LANCZOS)
    scale = (max if mode == "cover" else min)(w / image.width, h / image.height)
    resized = image.resize((max(1, round(image.width * scale)), max(1, round(image.height * scale))),
                           Image.Resampling.LANCZOS)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.paste(resized, ((w - resized.width) // 2, (h - resized.height) // 2))
    return out


def _covers(m, src_size, canvas_size):
    """True when the transformed source fully covers the canvas (no matte needed)."""
    inv = _affine(m)
    sw, sh = src_size
    cw, ch = canvas_size
    for x, y in ((0, 0), (cw, 0), (0, ch), (cw, ch)):
        u = inv[0] * x + inv[1] * y + inv[2]
        v = inv[3] * x + inv[4] * y + inv[5]
        if not (0 <= u <= sw and 0 <= v <= sh):
            return False
    return True


def _blend(canvas, rgb, alpha, mode):
    if mode == "normal":
        return rgb * alpha + canvas * (1 - alpha)
    if mode == "add":
        return np.minimum(canvas + rgb * alpha, 1.0)
    if mode == "screen":
        return 1 - (1 - canvas) * (1 - rgb * alpha)
    if mode == "multiply":
        return canvas * (1 - alpha) + canvas * rgb * alpha
    if mode == "lighten":
        return np.maximum(canvas, rgb * alpha + canvas * (1 - alpha))
    raise SpecError(f"unknown blend {mode}")


def _blur_alpha(alpha, radius):
    if radius <= 0:
        return alpha
    img = Image.fromarray((np.clip(alpha[..., 0], 0, 1) * 255).astype(np.uint8), "L")
    small = img.resize((max(1, img.width // 4), max(1, img.height // 4)), Image.Resampling.BILINEAR)
    small = small.filter(ImageFilter.GaussianBlur(max(0.5, radius / 4)))
    big = small.resize(img.size, Image.Resampling.BILINEAR)
    return (np.asarray(big, dtype=np.float32) / 255.0)[..., None]


def _apply_effects_before(layer, canvas, alpha):
    for effect in layer.get("effects", []):
        if effect.get("type") == "transmitted_light":
            darken = float(effect.get("darken", 0.35)) * float(effect.get("strength", 1.0))
            canvas = canvas * (1 - darken)
    return canvas


def _apply_effects_after(layer, canvas, rgb, alpha):
    for effect in layer.get("effects", []):
        kind = effect.get("type")
        if kind == "transmitted_light":
            color = np.array(_hex(effect.get("color", "#7FB7D6")), dtype=np.float32)
            strength = float(effect.get("strength", 1.0))
            halo = _blur_alpha(alpha, float(effect.get("halo", 24)))
            canvas = np.minimum(canvas + rgb * alpha * strength * 0.5 + halo * color * strength * 0.6, 1.0)
        elif kind == "light_figure":
            color = np.array(_hex(effect.get("rim", "#E3B04B")), dtype=np.float32)
            rim_px = int(effect.get("rim_px", 2))
            a_img = Image.fromarray((alpha[..., 0] * 255).astype(np.uint8), "L")
            eroded = np.asarray(a_img.filter(ImageFilter.MinFilter(2 * rim_px + 1)), dtype=np.float32)[..., None] / 255
            rim = np.clip(alpha - eroded, 0, 1)
            canvas = np.minimum(canvas + rim * color * float(effect.get("strength", 1.0)), 1.0)
        elif kind == "glow":
            color = np.array(_hex(effect.get("color", "#F2B866")), dtype=np.float32)
            halo = _blur_alpha(alpha, float(effect.get("radius", 20)))
            canvas = 1 - (1 - canvas) * (1 - halo * color * float(effect.get("strength", 0.5)))
    return canvas


def _press_style(layer, rgb, alpha, press):
    """PRESS as a style state (episode script section 4)."""
    if press <= 0:
        return rgb, alpha
    tags = layer["tags"]
    if "shade" in tags:
        alpha = alpha * max(0.0, 1 - press / 0.3)
    if "highlight" in tags:
        alpha = alpha * max(0.0, 1 - press / 0.6)
    if "line" in tags and press >= 0.6:
        rgb = np.broadcast_to(np.array(_hex("#2B2F33"), dtype=np.float32), rgb.shape).copy()
        a_img = Image.fromarray((np.clip(alpha[..., 0], 0, 1) * 255).astype(np.uint8), "L")
        unified = a_img.filter(ImageFilter.MaxFilter(3)).point(lambda v: 255 if v > 96 else 0)
        alpha = np.asarray(unified, dtype=np.float32)[..., None] / 255.0
    if "bg" in tags and press >= 0.6:
        mix = min(1.0, (press - 0.6) / 0.2)
        top = rgb[: max(1, rgb.shape[0] // 8)].reshape(-1, 3).mean(0)
        bottom = rgb[-max(1, rgb.shape[0] // 8):].reshape(-1, 3).mean(0)
        t = np.linspace(0, 1, rgb.shape[0], dtype=np.float32)[:, None, None]
        gradient = top * (1 - t) + bottom * t
        gray = gradient.mean(-1, keepdims=True)
        gradient = gray + (gradient - gray) * 0.3
        rgb = rgb * (1 - mix) + np.broadcast_to(gradient, rgb.shape) * mix
    return rgb, alpha
