"""Procedural generator layers for the core FX tokens and editorial cards.

A generator layer is ``{"generator": {"type": ..., ...}}``. Generators draw in
screen space at the layer's quantized frame, so they obey the same on-2s/3s
exposure clock as drawn cels. They cover tokens that are geometry or type, not
character drawing: SPIRAL_SIGIL, TEXT_SUPER, SPEED_LINES, TRAIN_STROBE,
SHOCKWAVE_RING, LANE_FIELD, UI_PHONE, plus slates for shots without art.
Drawn spectacle (ribbons, water, smoke) stays hand-made cels.
"""
from __future__ import annotations

from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path
import textwrap

import numpy as np
from PIL import Image, ImageDraw, ImageFont

SUPERSAMPLE = 3
FONT_DIRS = [Path(__file__).resolve().parents[2] / "projects/cemi_episode_01/assets/fonts",
             Path("/usr/share/fonts"), Path("/Library/Fonts"), Path("C:/Windows/Fonts")]
FONT_CANDIDATES = {
    "serif": ["cover_serif.ttf", "cover_serif.otf", "DejaVuSerif.ttf", "Georgia.ttf", "Times New Roman.ttf"],
    "sans": ["ui_sans.ttf", "DejaVuSans.ttf", "Helvetica.ttc", "Arial.ttf"],
    "mono": ["DejaVuSansMono.ttf", "Courier New.ttf"],
}


def _rgba(color, alpha=255):
    if isinstance(color, str):
        c = color.lstrip("#")
        rgb = tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))
        a = int(c[6:8], 16) if len(c) == 8 else alpha
        return rgb + (a,)
    color = list(color)
    return tuple(int(v) for v in color[:3]) + ((int(color[3]),) if len(color) > 3 else (alpha,))


@lru_cache(maxsize=64)
def font(kind: str, size: int):
    """Font lookup: projects/.../assets/fonts first (drop your cover face there)."""
    for name in FONT_CANDIDATES.get(kind, FONT_CANDIDATES["sans"]):
        for base in FONT_DIRS:
            if not base.exists():
                continue
            direct = base / name
            if direct.is_file():
                return ImageFont.truetype(str(direct), size)
            for found in base.rglob(name):
                return ImageFont.truetype(str(found), size)
    return ImageFont.load_default(size=size)


def _seed(*parts):
    return int.from_bytes(hashlib.sha256("|".join(map(str, parts)).encode()).digest()[:4], "little")


# ------------------------------------------------------------------ sigil

def sigil_path(cx, cy, radius, turns=2.25, points=480):
    """Cemí sigil: a spiral opening into a triangle, as one continuous line."""
    path = []
    theta_end = turns * 2 * math.pi
    inner = radius * 0.62
    for i in range(points):
        t = i / (points - 1)
        theta = t * theta_end
        r = inner * t
        path.append((cx + r * math.cos(theta - math.pi / 2), cy + r * math.sin(theta - math.pi / 2)))
    verts = [(cx + radius * math.cos(a), cy + radius * math.sin(a))
             for a in (-math.pi / 2, -math.pi / 2 + 2 * math.pi / 3, -math.pi / 2 + 4 * math.pi / 3)]
    end = path[-1]
    nearest = min(range(3), key=lambda i: (verts[i][0] - end[0]) ** 2 + (verts[i][1] - end[1]) ** 2)
    order = [verts[(nearest + k) % 3] for k in range(4)]
    for a, b in zip(order, order[1:]):
        for i in range(1, 61):
            t = i / 60
            path.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    return path


def _partial(path, fraction):
    if fraction >= 1:
        return path
    lengths = [0.0]
    for (x0, y0), (x1, y1) in zip(path, path[1:]):
        lengths.append(lengths[-1] + math.hypot(x1 - x0, y1 - y0))
    target = lengths[-1] * max(0.0, fraction)
    out = [path[0]]
    for i in range(1, len(path)):
        if lengths[i] <= target:
            out.append(path[i])
        else:
            seg = lengths[i] - lengths[i - 1]
            t = 0 if seg == 0 else (target - lengths[i - 1]) / seg
            out.append((path[i - 1][0] + (path[i][0] - path[i - 1][0]) * t,
                        path[i - 1][1] + (path[i][1] - path[i - 1][1]) * t))
            break
    return out


def gen_sigil(g, q, size):
    w, h = size
    k = SUPERSAMPLE
    cx, cy = g.get("center", [w / 2, h / 2])
    radius = float(g.get("radius", h * 0.22))
    start, draw = int(g.get("start", 0)), max(1, int(g.get("draw_frames", 72)))
    fraction = min(1.0, max(0.0, (q - start) / draw))
    out = Image.new("RGBA", size, (0, 0, 0, 0))
    if fraction <= 0:
        return out
    width = max(1, int(round(float(g.get("width", 2)) * h / 720)))
    pad = int(radius * 1.15) + width * 2
    x0, y0 = int(cx) - pad, int(cy) - pad
    box = Image.new("RGBA", (2 * pad * k, 2 * pad * k), (0, 0, 0, 0))
    pts = _partial(sigil_path((cx - x0) * k, (cy - y0) * k, radius * k), fraction)
    ImageDraw.Draw(box).line(pts, fill=_rgba(g.get("color", "#C9A24A")), width=width * k, joint="curve")
    out.paste(box.resize((2 * pad, 2 * pad), Image.Resampling.BOX), (x0, y0))
    return out


# ------------------------------------------------------------------- type

def _tracked(draw, xy, text, fnt, fill, tracking):
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=fnt, fill=fill)
        x += draw.textlength(ch, font=fnt) + tracking
    return x


def _measure(draw, text, fnt, tracking):
    return sum(draw.textlength(ch, font=fnt) for ch in text) + tracking * max(0, len(text) - 1)


def gen_text(g, q, size):
    """TEXT_SUPER: serif caps with wide tracking; small caps for time stamps."""
    w, h = size
    lines = g["text"] if isinstance(g["text"], list) else str(g["text"]).split("\n")
    reveal = int(g.get("reveal_frames", 0))
    start = int(g.get("start", 0))
    if q < start:
        return Image.new("RGBA", size, (0, 0, 0, 0))
    total = sum(len(line) for line in lines)
    shown = total if reveal <= 0 else int(total * min(1.0, (q - start + 1) / reveal))
    px = int(g.get("size", 42) * h / 720)
    fnt = font(g.get("font", "serif"), px)
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    tracking = float(g.get("tracking", 0.25)) * px
    leading = px * float(g.get("leading", 1.35))
    cx, cy = g.get("position", [w / 2, h / 2])
    y = cy - leading * len(lines) / 2
    fill = _rgba(g.get("color", "#EDE6D6"))
    for line in lines:
        visible = line[:max(0, shown)]
        shown -= len(line)
        text = visible.upper() if g.get("caps", True) else visible
        width = _measure(draw, text if text else " ", fnt, tracking)
        align = g.get("align", "center")
        x = cx - width / 2 if align == "center" else (cx if align == "left" else cx - width)
        _tracked(draw, (x, y), text, fnt, fill, tracking)
        y += leading
    return img


def gen_slate(g, q, size):
    """Animatic slate for a shot without art: ID, timing, camera and action."""
    w, h = size
    img = Image.new("RGBA", size, _rgba(g.get("background", "#14202B")))
    draw = ImageDraw.Draw(img)
    big, small = font("sans", int(34 * h / 720)), font("sans", int(22 * h / 720))
    cream, gold, gray = _rgba("#EDE6D6"), _rgba("#C9A24A"), _rgba("#8A8F94")
    margin = int(56 * w / 1280)
    draw.text((margin, margin), g.get("shot", ""), font=big, fill=gold)
    draw.text((margin, margin + int(46 * h / 720)), g.get("header", ""), font=small, fill=gray)
    y = margin + int(100 * h / 720)
    chars = max(30, int((w - 2 * margin) / (small.size * 0.52)))
    for para in str(g.get("action", "")).split("\n"):
        for line in textwrap.wrap(para, chars)[:14]:
            draw.text((margin, y), line, font=small, fill=cream)
            y += int(small.size * 1.45)
    note = g.get("note", "NO ART YET - animatic slate, not production picture")
    note_w = draw.textlength(note, font=small)
    draw.text((w - margin - note_w, margin), note, font=small, fill=gray)
    return img


# ------------------------------------------------------------ cel-like FX

def gen_speed_lines(g, q, size):
    """SPEED_LINES: 2-drawing loop (drawing index from the layer clock)."""
    w, h = size
    k = SUPERSAMPLE
    rate = int(g.get("rate", 2))
    drawing = (q // rate) % int(g.get("drawings", 2))
    rng = np.random.default_rng(_seed(g.get("seed", "speed"), drawing))
    img = Image.new("RGBA", (w * k, h * k), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    color = _rgba(g.get("color", "#EDE6D6"), int(255 * float(g.get("opacity", 0.8))))
    density = int(g.get("density", 60))
    direction = g.get("direction", "radial")
    cx, cy = (v * k for v in g.get("center", [w / 2, h / 2]))
    for _ in range(density):
        if direction == "radial":
            a = rng.uniform(0, 2 * math.pi)
            r0 = rng.uniform(0.35, 0.6) * max(w, h) * k
            r1 = r0 + rng.uniform(0.3, 0.7) * max(w, h) * k
            pts = [(cx + r0 * math.cos(a), cy + r0 * math.sin(a)), (cx + r1 * math.cos(a), cy + r1 * math.sin(a))]
        elif direction == "horizontal":
            y = rng.uniform(0, h * k)
            x0 = rng.uniform(-0.2, 0.8) * w * k
            pts = [(x0, y), (x0 + rng.uniform(0.2, 0.6) * w * k, y)]
        else:
            x = rng.uniform(0, w * k)
            y0 = rng.uniform(-0.2, 0.8) * h * k
            pts = [(x, y0), (x, y0 + rng.uniform(0.2, 0.6) * h * k)]
        draw.line(pts, fill=color, width=max(1, int(rng.uniform(1, 3) * k)))
    return img.resize(size, Image.Resampling.LANCZOS)


def gen_train_strobe(g, q, size):
    """TRAIN_STROBE: 8-10 window-light bars crossing the frame at 24 fps."""
    w, h = size
    bars = int(g.get("bars", 9))
    speed = float(g.get("speed", w / 18))
    bar_w = float(g.get("bar_width", w / 22))
    gap = float(g.get("gap", w / 28))
    color = _rgba(g.get("color", "#F2B866"), int(255 * float(g.get("opacity", 0.35))))
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    skew = float(g.get("skew", 0.25)) * h
    offset = (q - int(g.get("start", 0))) * speed - bars * (bar_w + gap)
    for i in range(bars):
        x = offset + i * (bar_w + gap)
        draw.polygon([(x, 0), (x + bar_w, 0), (x + bar_w + skew, h), (x + skew, h)], fill=color)
    return img


def gen_ring(g, q, size):
    """SHOCKWAVE_RING: cel-drawn expanding rings."""
    w, h = size
    k = 2
    img = Image.new("RGBA", (w * k, h * k), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx, cy = g.get("center", [w / 2, h / 2])
    start, speed = int(g.get("start", 0)), float(g.get("speed", 14))
    count, spacing = int(g.get("rings", 3)), int(g.get("spacing", 6))
    life = float(g.get("life", 36))
    drawn = False
    for i in range(count):
        age = q - start - i * spacing
        if age < 0 or age > life:
            continue
        r = age * speed
        alpha = int(255 * (1 - age / life))
        width = max(1, int(float(g.get("width", 3)) * k))
        draw.ellipse([(cx - r) * k, (cy - r) * k, (cx + r) * k, (cy + r) * k],
                     outline=_rgba(g.get("color", "#C9A24A"), alpha), width=width)
        drawn = True
    if not drawn:
        return Image.new("RGBA", size, (0, 0, 0, 0))
    return img.resize(size, Image.Resampling.BOX)


def gen_lanes(g, q, size):
    """LANE_FIELD: n screen-space bands, each its own hue; glows never overlap."""
    w, h = size
    hues = g.get("colors", ["#E3B04B", "#F5F0E1", "#9BD16A", "#E0533D", "#7FB7D6", "#9A7FD1"])
    n = int(g.get("lanes", len(hues)))
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    band = h / n
    alpha = int(255 * float(g.get("opacity", 0.28)))
    for i in range(n):
        y0 = i * band + band * 0.18
        y1 = (i + 1) * band - band * 0.18
        wobble = math.sin((q + i * 7) / 9) * band * 0.04
        draw.rectangle([0, y0 + wobble, w, y1 + wobble], fill=_rgba(hues[i % len(hues)], alpha))
    return img


def gen_phone(g, q, size):
    """UI_PHONE: chat bubbles typed on at their frames (neutral sans)."""
    w, h = size
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    fnt = font("sans", int(g.get("size", 24) * h / 720))
    x_left, x_right = w * 0.28, w * 0.72
    y = h * 0.18
    for msg in g.get("messages", []):
        at = int(msg.get("at", 0))
        if q < at:
            break
        typed = int(len(msg["text"]) * min(1.0, (q - at + 1) / max(1, int(msg.get("type_frames", 12)))))
        text = textwrap.fill(msg["text"][:typed], 32)
        box = draw.multiline_textbbox((0, 0), text or " ", font=fnt)
        bw, bh = box[2] - box[0] + 28, box[3] - box[1] + 22
        right = msg.get("side", "left") == "right"
        x = x_right - bw if right else x_left
        draw.rounded_rectangle([x, y, x + bw, y + bh], radius=16,
                               fill=_rgba("#1F4FD8" if right else "#E9E9EB"))
        draw.multiline_text((x + 14, y + 9), text, font=fnt, fill=_rgba("#FFFFFF" if right else "#111111"))
        y += bh + 14
    return img


def gen_solid(g, q, size):
    return Image.new("RGBA", size, _rgba(g.get("color", "#14202B")))


def gen_gradient(g, q, size):
    w, h = size
    top = np.array(_rgba(g.get("top", "#14202B")), dtype=np.float32)
    bottom = np.array(_rgba(g.get("bottom", "#000000")), dtype=np.float32)
    t = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
    arr = np.broadcast_to(top * (1 - t) + bottom * t, (h, w, 4))
    return Image.fromarray(arr.astype(np.uint8), "RGBA")


GENERATORS = {
    "sigil": gen_sigil, "text": gen_text, "slate": gen_slate, "speed_lines": gen_speed_lines,
    "train_strobe": gen_train_strobe, "ring": gen_ring, "lanes": gen_lanes, "phone": gen_phone,
    "solid": gen_solid, "gradient": gen_gradient,
}

def state(generator, q):
    """Smallest value that determines a generator's drawing (cache key)."""
    kind, q = generator["type"], int(q)
    if kind in ("solid", "gradient", "slate"):
        return 0
    if kind == "sigil":
        start, draw = int(generator.get("start", 0)), max(1, int(generator.get("draw_frames", 72)))
        return min(max(q - start, -1), draw)
    if kind == "text":
        start, reveal = int(generator.get("start", 0)), int(generator.get("reveal_frames", 0))
        if q < start:
            return -1
        return 0 if reveal <= 0 else min(q - start, reveal)
    if kind == "speed_lines":
        return (q // int(generator.get("rate", 2))) % int(generator.get("drawings", 2))
    if kind == "ring":
        start = int(generator.get("start", 0))
        life = float(generator.get("life", 36)) + int(generator.get("rings", 3)) * int(generator.get("spacing", 6))
        return min(max(q - start, -1), int(life) + 1)
    return q


_CACHE: dict = {}


def render(generator, q, size, layer=None, compositor=None):
    """Render (and memoize the latest drawing per layer) a generator layer."""
    kind = generator["type"]
    key = (json.dumps(generator, sort_keys=True), state(generator, q), tuple(size))
    slot = (layer.get("name") if layer else kind, id(compositor))
    hit = _CACHE.get(slot)
    if hit and hit[0] == key:
        return hit[1]
    image = GENERATORS[kind](generator, int(q), tuple(size))
    if len(_CACHE) > 256:
        _CACHE.clear()
    _CACHE[slot] = (key, image)
    return image
