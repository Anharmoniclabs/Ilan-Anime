"""Post stack: the 90s film-transfer finish and global state effects.

Order per frame: era grade -> saturation/PRESS -> halation -> chroma bleed ->
heat shimmer -> harmony cut -> double exposure -> fade -> vignette -> grain ->
flash frames -> gate weave. Every effect is deterministic for (shot id, frame).

Parameters may be a scalar or a list of keys ``[{"frame": f, "value": v}]``.
"""
from __future__ import annotations

from functools import lru_cache
import hashlib
import math

import numpy as np
from PIL import Image, ImageFilter

GRADES = {
    # name: (saturation, gain rgb, lift rgb, gamma)
    "present": (1.0, (1.0, 1.0, 1.0), (0.0, 0.0, 0.0), 1.0),
    "before": (0.85, (0.80, 0.90, 1.05), (0.0, 0.005, 0.015), 1.12),
    "1934": (0.55, (1.05, 1.00, 0.80), (0.02, 0.03, 0.0), 1.0),
    "1957": (1.25, (1.08, 0.98, 0.85), (0.01, 0.0, 0.0), 0.97),
    "1973": (1.15, (1.06, 1.00, 0.88), (0.02, 0.01, 0.0), 0.95),
    "flashback": (0.6, (1.04, 1.02, 0.95), (0.06, 0.05, 0.04), 0.9),
    "classroom": (0.7, (1.02, 0.98, 0.88), (0.04, 0.035, 0.02), 1.0),
    "sodium": (0.95, (1.10, 0.95, 0.78), (0.0, 0.0, 0.01), 1.0),
}

CREAM = np.array([0xED, 0xE6, 0xD6], dtype=np.float32) / 255
NAVY = np.array([0x14, 0x20, 0x2B], dtype=np.float32) / 255
LUMA = np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)


def _seed(*parts) -> int:
    return int.from_bytes(hashlib.sha256("|".join(map(str, parts)).encode()).digest()[:4], "little")


def keyed(value, frame, default=0.0):
    """Scalar, or [{frame, value}] keys with linear interpolation."""
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)
    keys = sorted(value, key=lambda k: k["frame"])
    if not keys:
        return default
    if frame <= keys[0]["frame"]:
        return float(keys[0]["value"])
    if frame >= keys[-1]["frame"]:
        return float(keys[-1]["value"])
    for a, b in zip(keys, keys[1:]):
        if a["frame"] <= frame <= b["frame"]:
            span = b["frame"] - a["frame"]
            t = 0 if span == 0 else (frame - a["frame"]) / span
            if a.get("ease") == "hold":
                t = 0
            return float(a["value"]) + (float(b["value"]) - float(a["value"])) * t
    return default


def camera_shake(shakes, frame, shot_id):
    """CAMERA_SHAKE: random walk with snap; returns (dx, dy, roll)."""
    dx = dy = roll = 0.0
    for i, shake in enumerate(shakes or []):
        start, end = int(shake["start"]), int(shake["end"])
        if not start <= frame < end:
            continue
        amp = float(shake.get("amp", 6))
        decay = 1 - (frame - start) / max(1, end - start) if shake.get("decay", True) else 1
        step = frame // int(shake.get("rate", 2)) * int(shake.get("rate", 2))  # snaps on 2s
        rng = np.random.default_rng(_seed(shot_id, "shake", i, step))
        x, y = rng.uniform(-1, 1, 2)
        dx += x * amp * decay
        dy += y * amp * decay
        roll += float(shake.get("roll", 0)) * rng.uniform(-1, 1) * decay
    return dx, dy, roll


@lru_cache(maxsize=4)
def grain_plates(width, height, seed, count=24):
    """FILM_GRAIN: a looped bank of 24 baked plates, not per-frame noise."""
    rng = np.random.default_rng(seed)
    plates = []
    for _ in range(count):
        small = rng.normal(0, 1, (height // 2 + 1, width // 2 + 1)).astype(np.float32)
        img = Image.fromarray(np.clip(small * 40 + 128, 0, 255).astype(np.uint8), "L")
        img = img.resize((width, height), Image.Resampling.BILINEAR)
        plates.append(((np.asarray(img, dtype=np.float32) - 128) / 40).astype(np.float16))
    return np.stack(plates)


def shift(image, dx, dy):
    """Sub-pixel translate with edge clamping."""
    if abs(dx) < 1e-4 and abs(dy) < 1e-4:
        return image
    h, w = image.shape[:2]
    ys = np.clip(np.arange(h, dtype=np.float32) - dy, 0, h - 1)
    xs = np.clip(np.arange(w, dtype=np.float32) - dx, 0, w - 1)
    y0, x0 = np.floor(ys).astype(int), np.floor(xs).astype(int)
    y1, x1 = np.minimum(y0 + 1, h - 1), np.minimum(x0 + 1, w - 1)
    fy, fx = (ys - y0)[:, None, None], (xs - x0)[None, :, None]
    top = image[y0][:, x0] * (1 - fx) + image[y0][:, x1] * fx
    bottom = image[y1][:, x0] * (1 - fx) + image[y1][:, x1] * fx
    return top * (1 - fy) + bottom * fy


def _hshift_channel(channel, dx):
    w = channel.shape[1]
    xs = np.clip(np.arange(w, dtype=np.float32) - dx, 0, w - 1)
    x0 = np.floor(xs).astype(int)
    x1 = np.minimum(x0 + 1, w - 1)
    f = xs - x0
    return channel[:, x0] * (1 - f) + channel[:, x1] * f


def _blur(image, radius):
    """Fast soft blur through a downscaled Gaussian."""
    h, w = image.shape[:2]
    factor = 4 if radius >= 8 else 1
    img = Image.fromarray((np.clip(image, 0, 1) * 255).astype(np.uint8))
    if factor > 1:
        img = img.resize((max(1, w // factor), max(1, h // factor)), Image.Resampling.BILINEAR)
    img = img.filter(ImageFilter.GaussianBlur(max(0.5, radius / factor)))
    if factor > 1:
        img = img.resize((w, h), Image.Resampling.BILINEAR)
    return np.asarray(img, dtype=np.float32) / 255


@lru_cache(maxsize=16)
def _grade_lut(name, size=1024):
    sat, gain, lift, gamma = GRADES[name]
    x = np.linspace(0, 1, size, dtype=np.float32)
    return np.stack([np.clip(x ** gamma * gain[c] + lift[c], 0, 1.2) for c in range(3)]).astype(np.float32)


def apply_grade(canvas, name):
    """Per-channel gamma/gain/lift through a 1024-entry LUT, then saturation."""
    sat = GRADES[name][0]
    lut = _grade_lut(name)
    idx = (np.clip(canvas, 0, 1) * 1023 + 0.5).astype(np.int16)
    out = np.empty_like(canvas)
    for c in range(3):
        out[..., c] = lut[c][idx[..., c]]
    if sat != 1.0:
        gray = (out @ LUMA)[..., None]
        out = gray + (out - gray) * sat
    return out


def _grade_at(spec, frame):
    """Return [(name, weight)] for the active grade, crossfading WIPE_ERA swaps."""
    grade = spec.get("grade")
    if grade is None:
        return []
    if isinstance(grade, str):
        return [(grade, 1.0)]
    keys = sorted(grade, key=lambda k: k["frame"])
    current = keys[0]
    previous = None
    for key in keys:
        if key["frame"] <= frame:
            previous, current = current, key
    if previous is not None and previous is not current:
        blend = int(current.get("blend", 0))
        if blend > 0 and frame < current["frame"] + blend:
            t = (frame - current["frame"]) / blend
            return [(previous["grade"], 1 - t), (current["grade"], t)]
    return [(current["grade"], 1.0)]


class PostStack:
    def __init__(self, spec, size, shot_id, frames):
        self.spec = spec or {}
        self.size = size
        self.shot_id = shot_id
        self.frames = frames
        grade = self.spec.get("grade")
        names = [grade] if isinstance(grade, str) else [k.get("grade") for k in (grade or [])]
        for name in names:
            if name not in GRADES:
                raise ValueError(f"Unknown grade {name}; choose from {sorted(GRADES)}")

    def value(self, name, frame, default=0.0):
        return keyed(self.spec.get(name), frame, default)

    def source_frame(self, frame):
        """HARMONY_CUT freezes the picture at the start of its range."""
        for cut in self.spec.get("harmony", []):
            if cut["start"] <= frame < cut["end"]:
                return int(cut["start"])
        return frame

    def apply(self, canvas, frame, compositor=None):
        s = self.spec
        out = canvas
        grades = _grade_at(s, frame)
        if grades:
            out = sum(apply_grade(out, name) * w for name, w in grades)
        press = float(np.clip(self.value("press", frame, 0.0), 0, 1))
        saturation = self.value("saturation", frame, 1.0) * (1 - 0.85 * press)
        if saturation != 1.0:
            gray = (out @ LUMA)[..., None]
            out = gray + (out - gray) * saturation
        halation = self.value("halation", frame, 0.0)
        if halation > 0:
            luma = out @ LUMA
            mask = np.clip((luma - float(s.get("halation_threshold", 0.78))) / 0.15, 0, 1)[..., None]
            glow = _blur(mask * out, self.size[0] * 0.02)
            out = 1 - (1 - out) * (1 - glow * np.array([1.0, 0.35, 0.15], dtype=np.float32) * halation)
        chroma = self.value("chroma", frame, 0.0)
        if chroma > 0:
            px = 0.5 + 1.0 * min(chroma, 1.0)
            luma = out @ LUMA
            edge = np.abs(np.diff(luma, axis=1, prepend=luma[:, :1]))
            weight = np.clip(edge * 6, 0, 1) * min(chroma, 1.0)
            r = _hshift_channel(out[..., 0], px)
            b = _hshift_channel(out[..., 2], -px)
            out = out.copy()
            out[..., 0] += (r - out[..., 0]) * weight
            out[..., 2] += (b - out[..., 2]) * weight
        for shimmer in s.get("heat_shimmer", []):
            if shimmer["start"] <= frame < shimmer["end"]:
                out = _heat_shimmer(out, shimmer, frame)
        for cut in s.get("harmony", []):
            if cut["start"] <= frame < cut["end"]:
                styled = harmony_style(out)
                dissolve = int(cut.get("dissolve", 6))
                t = 1.0 if dissolve <= 0 else min(1.0, (frame - cut["start"] + 1) / dissolve)
                out = out * (1 - t) + styled * t
        for exposure in s.get("double_exposure", []):
            if exposure["start"] <= frame < exposure["end"] and compositor is not None:
                image = compositor._load(exposure["source"], exposure.get("fit", "cover")).convert("RGBA")
                if image.size != tuple(self.size):
                    image = image.resize(tuple(self.size), Image.Resampling.BILINEAR)
                arr = np.asarray(image, dtype=np.float32) / 255
                a = arr[..., 3:4] * float(exposure.get("opacity", 0.3))
                out = arr[..., :3] * a + out * (1 - a)
        for fade in s.get("fade", []):
            if fade["start"] <= frame < fade["end"]:
                t = (frame - fade["start"] + 1) / max(1, fade["end"] - fade["start"])
                t = t if fade.get("dir", "out") == "out" else 1 - t
                target = {"black": (0, 0, 0), "white": (1, 1, 1), "navy": tuple(NAVY), "cream": tuple(CREAM)}
                color = np.array(target.get(fade.get("to", "black"), (0, 0, 0)), dtype=np.float32)
                out = out * (1 - t) + color * t
        vignette = self.value("vignette", frame, 0.0)
        if vignette > 0:
            out = out * _vignette(self.size, vignette)
        grain = self.value("grain", frame, 0.0)
        if grain > 0:
            plates = grain_plates(self.size[0], self.size[1], _seed(self.shot_id, "grain"))
            plate = plates[frame % len(plates)].astype(np.float32)[..., None]
            luma = (out @ LUMA)[..., None]
            weight = 4 * luma * (1 - luma) + 0.25
            out = out + plate * grain * 0.045 * weight
        # hard flash frames override everything (no grain/vignette on a flash)
        for flash in s.get("flash", []):
            if flash["frame"] <= frame < flash["frame"] + int(flash.get("frames", 1)):
                if flash.get("mode", "white") == "white":
                    out = np.ones_like(out)
                else:
                    luma = (out @ LUMA)[..., None]
                    out = CREAM * (1 - luma) + NAVY * luma
        return out

    def weave_offset(self, frame):
        weave = self.value("weave", frame, 0.0)
        return gate_weave(self.shot_id, frame, weave) if weave > 0 else (0.0, 0.0)


def gate_weave(shot_id, frame, amount):
    """GATE_WEAVE: smooth random walk under 1.5 Hz, +/- 0.5-1.5 px."""
    rng = np.random.default_rng(_seed(shot_id, "weave"))
    freqs = rng.uniform(0.25, 1.4, (2, 3))
    phases = rng.uniform(0, 2 * math.pi, (2, 3))
    t = frame / 24.0
    amp = 0.5 + min(float(amount), 1.0)
    dx = amp * float(np.sin(2 * math.pi * freqs[0] * t + phases[0]).mean())
    dy = 0.6 * amp * float(np.sin(2 * math.pi * freqs[1] * t + phases[1]).mean())
    return dx, dy


@lru_cache(maxsize=8)
def _vignette_cached(w, h, amount_q):
    amount = amount_q / 1000
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    r = ((x - w / 2) / (w / 2)) ** 2 + ((y - h / 2) / (h / 2)) ** 2
    return (1 - amount * np.clip(r / 2, 0, 1) ** 1.5)[..., None].astype(np.float32)


def _vignette(size, amount):
    return _vignette_cached(size[0], size[1], int(round(amount * 1000)))


def harmony_style(image):
    """HARMONY_CUT look: 3-tone posterize, pastel, hatching, cream border."""
    luma = image @ LUMA
    levels = np.digitize(luma, [0.33, 0.62])
    poster = np.zeros_like(image)
    for level in range(3):
        mask = levels == level
        if mask.any():
            poster[mask] = image[mask].mean(0)
    pastel = poster * 0.55 + CREAM * 0.45
    h, w = luma.shape
    y, x = np.mgrid[0:h, 0:w]
    hatch = ((x + y) % 7 == 0) & (levels == 0)
    pastel[hatch] *= 0.72
    border = max(4, int(min(h, w) * 0.03))
    pastel[:border] = CREAM
    pastel[-border:] = CREAM
    pastel[:, :border] = CREAM
    pastel[:, -border:] = CREAM
    return pastel


def _heat_shimmer(image, spec, frame):
    """HEAT_SHIMMER: low-frequency horizontal wobble inside a region."""
    h, w = image.shape[:2]
    x0, y0, rw, rh = spec.get("region", [0, 0, w, h])
    x0, y0 = int(x0), int(y0)
    x1, y1 = min(w, x0 + int(rw)), min(h, y0 + int(rh))
    strength = float(spec.get("strength", 0.5)) * 3.0
    region = image[y0:y1, x0:x1]
    rows = np.arange(y1 - y0, dtype=np.float32)
    offsets = strength * np.sin(2 * math.pi * (rows / 60.0 + frame / 24.0 * 0.8))
    out = image.copy()
    xs = np.arange(x1 - x0, dtype=np.float32)
    for i, off in enumerate(offsets):
        src = np.clip(xs - off, 0, x1 - x0 - 1)
        i0 = np.floor(src).astype(int)
        i1 = np.minimum(i0 + 1, x1 - x0 - 1)
        f = (src - i0)[:, None]
        out[y0 + i, x0:x1] = region[i, i0] * (1 - f) + region[i, i1] * f
    return out
