"""Scan a drawing into editable 2D: flat cel fills + variable-width ink strokes.

The scan is what Blender rebuilds as a Grease Pencil drawing
(``studio/blender_gp_build.py``), so the picture becomes real, editable 2D in
Blender instead of an image on a plane:

1. **Ink**: dark, thin structures (black-hat contrast + darkness), cleaned of
   specks, thinned to centerlines and traced into polylines. Each point keeps
   the local line half-width from a distance transform, so line weight varies
   like the original ink.
2. **Cel fills**: the remaining color is clustered (k-means in Lab) into a small
   palette, smoothed, small islands merged into their neighbors, and ink pixels
   assigned to the nearest fill so fills run under the lines. Each connected
   region becomes a polygon; fills are ordered largest first (painter's order)
   and dilated 1 px so neighbors overlap instead of cracking.
3. **Holes** that open onto transparency become holdout fills.
4. **Preview + fidelity**: the vectors are rasterized again and compared with the
   source, so a reviewer can see how faithful the rebuild is before any
   Blender time is spent.

A fully painted keyframe scans into posterized flats: that is the cel
separation the art direction still has to approve, not a loss to hide.
Requires numpy, Pillow and OpenCV (``pip install opencv-python-headless``).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from studio.paths import rel, sha256, write_json

try:
    import cv2
except ImportError:  # pragma: no cover - reported at call time
    cv2 = None


class ScanError(RuntimeError):
    pass


def _need_cv2():
    if cv2 is None:
        raise ScanError("scanning needs OpenCV: pip install opencv-python-headless")


# ------------------------------------------------------------------ ink

def ink_mask(rgb, alpha, *, contrast=0.10, dark=0.06, kernel=9, min_area=12):
    """Thin dark structures: local black-hat contrast (closing - image) above ``contrast``.

    Darkness alone never counts as ink (night scenes are dark everywhere); near-black
    pixels only join when they are also locally darker than their surroundings."""
    luma = (rgb @ np.array([0.299, 0.587, 0.114], dtype=np.float32))
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel, kernel))
    closed = cv2.morphologyEx(luma, cv2.MORPH_CLOSE, k)
    blackhat = closed - luma
    mask = ((blackhat > contrast) | ((luma < dark) & (blackhat > contrast * 0.4))) & (alpha > 0.5)
    mask = mask.astype(np.uint8)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    keep = np.zeros(count, dtype=bool)
    keep[1:] = stats[1:, cv2.CC_STAT_AREA] >= min_area
    return keep[labels].astype(np.uint8)


def thin(mask):
    """Zhang-Suen thinning (vectorized). mask: uint8 0/1 -> 1-px skeleton."""
    img = np.pad(mask.astype(np.uint8), 1)
    while True:
        changed = False
        for step in (0, 1):
            p2, p3, p4 = img[:-2, 1:-1], img[:-2, 2:], img[1:-1, 2:]
            p5, p6, p7 = img[2:, 2:], img[2:, 1:-1], img[2:, :-2]
            p8, p9 = img[1:-1, :-2], img[:-2, :-2]
            center = img[1:-1, 1:-1]
            ring = [p2, p3, p4, p5, p6, p7, p8, p9, p2]
            b = sum(n.astype(np.int16) for n in ring[:8])
            a = sum(((ring[i] == 0) & (ring[i + 1] == 1)).astype(np.int16) for i in range(8))
            if step == 0:
                c1, c2 = (p2 * p4 * p6) == 0, (p4 * p6 * p8) == 0
            else:
                c1, c2 = (p2 * p4 * p8) == 0, (p2 * p6 * p8) == 0
            remove = (center == 1) & (b >= 2) & (b <= 6) & (a == 1) & c1 & c2
            if remove.any():
                center[remove] = 0
                changed = True
        if not changed:
            return img[1:-1, 1:-1]


NEIGHBORS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


def trace_skeleton(skeleton):
    """Skeleton pixels -> list of polylines [(y, x), ...] split at ends and junctions."""
    ys, xs = np.nonzero(skeleton)
    pixels = set(zip(ys.tolist(), xs.tolist()))
    neighbors = {p: [(p[0] + dy, p[1] + dx) for dy, dx in NEIGHBORS if (p[0] + dy, p[1] + dx) in pixels]
                 for p in pixels}
    nodes = {p for p, n in neighbors.items() if len(n) != 2}
    used = set()
    paths = []

    def walk(start, nxt):
        path = [start, nxt]
        used.add(frozenset((start, nxt)))
        prev, cur = start, nxt
        while cur not in nodes:
            options = [n for n in neighbors[cur] if n != prev and frozenset((cur, n)) not in used]
            if not options:
                break
            prev, cur = cur, options[0]
            used.add(frozenset((prev, cur)))
            path.append(cur)
        return path

    for node in sorted(nodes):
        for n in neighbors[node]:
            if frozenset((node, n)) not in used:
                paths.append(walk(node, n))
    for p in sorted(pixels):  # closed loops with no junction
        for n in neighbors[p]:
            if frozenset((p, n)) not in used:
                loop = walk(p, n)
                paths.append(loop)
    return paths


def rdp(points, epsilon):
    """Ramer-Douglas-Peucker on an (N, >=2) array; keeps extra columns of kept points."""
    if len(points) < 3:
        return points
    keep = np.zeros(len(points), dtype=bool)
    keep[0] = keep[-1] = True
    stack = [(0, len(points) - 1)]
    xy = points[:, :2]
    while stack:
        i, j = stack.pop()
        if j <= i + 1:
            continue
        a, b = xy[i], xy[j]
        seg = b - a
        norm = np.hypot(*seg)
        mid = xy[i + 1:j]
        if norm < 1e-9:
            dist = np.hypot(*(mid - a).T)
        else:
            dist = np.abs(seg[0] * (mid[:, 1] - a[1]) - seg[1] * (mid[:, 0] - a[0])) / norm
        k = int(np.argmax(dist))
        if dist[k] > epsilon:
            keep[i + 1 + k] = True
            stack += [(i, i + 1 + k), (i + 1 + k, j)]
    return points[keep]


# ----------------------------------------------------------------- fills

def _srgb_to_lab(rgb):
    return cv2.cvtColor(rgb.astype(np.float32), cv2.COLOR_RGB2Lab)


def _mode_filter(labels, k, size=5):
    votes = np.stack([cv2.boxFilter((labels == i).astype(np.float32), -1, (size, size)) for i in range(k)])
    return np.argmax(votes, axis=0).astype(np.int32)


def _fill_unknown(labels, unknown):
    """Assign unknown pixels the label of the nearest known pixel."""
    if not unknown.any():
        return labels
    src = (~unknown).astype(np.uint8)
    _, nearest = cv2.distanceTransformWithLabels(1 - src, cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
    known_ys, known_xs = np.nonzero(src)
    # label index i (1-based) refers to the i-th zero pixel of (1 - src) in scan order = known pixels
    lut = labels[known_ys, known_xs]
    out = labels.copy()
    out[unknown] = lut[nearest[unknown] - 1]
    return out


def flat_regions(rgb, alpha, ink, *, colors=12, min_region=48, seed=0):
    h, w = alpha.shape
    solid = alpha > 0.5
    sample_mask = solid & (ink == 0)
    lab = _srgb_to_lab(rgb)
    samples = lab[sample_mask]
    if len(samples) < colors:
        raise ScanError("not enough visible pixels to scan")
    rng = np.random.default_rng(seed)
    if len(samples) > 60000:
        samples = samples[rng.choice(len(samples), 60000, replace=False)]
    cv2.setRNGSeed(seed)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 40, 0.2)
    _, _, centers = cv2.kmeans(samples.astype(np.float32), colors, None, criteria, 3, cv2.KMEANS_PP_CENTERS)
    dist = ((lab.reshape(-1, 1, 3) - centers.reshape(1, -1, 3)) ** 2).sum(-1)
    labels = np.argmin(dist, axis=1).reshape(h, w).astype(np.int32)
    labels = _fill_unknown(labels, (ink > 0) & solid)
    labels = _mode_filter(labels, colors)
    for _ in range(2):  # merge islands below min_region into neighbors
        small = np.zeros((h, w), dtype=bool)
        for k in range(colors):
            count, comp, stats, _ = cv2.connectedComponentsWithStats((labels == k).astype(np.uint8), connectivity=4)
            tiny = np.zeros(count, dtype=bool)
            tiny[1:] = stats[1:, cv2.CC_STAT_AREA] < min_region
            small |= tiny[comp]
        small &= solid
        if not small.any():
            break
        labels = _fill_unknown(labels, small)
    labels[~solid] = -1
    # palette in sRGB = mean source color per label (what the drawing actually used)
    palette = []
    for k in range(colors):
        m = (labels == k) & (ink == 0)  # ink pixels sit under lines; they'd darken the fill
        if not m.any():
            m = labels == k
        palette.append(np.median(rgb[m], axis=0) if m.any() else np.zeros(3, np.float32))
    return labels, np.array(palette, dtype=np.float32)


def region_polygons(labels, alpha, palette_size, *, epsilon=1.0, dilate=1):
    fills = []
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * dilate + 1, 2 * dilate + 1)) if dilate else None
    transparent = alpha <= 0.5
    for k in range(palette_size):
        mask = (labels == k).astype(np.uint8)
        if not mask.any():
            continue
        if kernel is not None:
            mask = cv2.dilate(mask, kernel) & (~transparent).astype(np.uint8) | mask
        contours, hierarchy = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
        if hierarchy is None:
            continue
        for i, contour in enumerate(contours):
            parent = hierarchy[0][i][3]
            poly = cv2.approxPolyDP(contour, epsilon, True).reshape(-1, 2)
            if len(poly) < 3:
                continue
            area = float(cv2.contourArea(contour))
            if parent == -1:
                fills.append({"color": int(k), "points": poly.tolist(), "area": area, "holdout": False})
            else:  # a hole: only matters if it opens onto transparency
                hole = np.zeros(mask.shape, np.uint8)
                cv2.drawContours(hole, [contour], -1, 1, -1)
                inside = hole.astype(bool)
                if inside.any() and transparent[inside].mean() > 0.5:
                    fills.append({"color": -1, "points": poly.tolist(), "area": area, "holdout": True})
    fills.sort(key=lambda f: (f["holdout"], -f["area"]))  # big first, holdouts last
    return fills


# ------------------------------------------------------------------- scan

def scan_image(path, *, colors=12, min_region=48, ink_colors=2, line_epsilon=0.8, fill_epsilon=1.0,
               min_stroke=2, ink_contrast=0.10, mask=None):
    """Scan ``path`` -> dict (JSON-ready) with palette, fills and ink strokes."""
    _need_cv2()
    image = Image.open(path).convert("RGBA")
    arr = np.asarray(image, dtype=np.float32) / 255
    rgb, alpha = arr[..., :3].copy(), arr[..., 3].copy()
    if mask is not None:
        m = np.asarray(Image.open(mask).convert("L").resize(image.size), dtype=np.float32) / 255
        alpha = np.minimum(alpha, m)
    ink = ink_mask(rgb, alpha, contrast=ink_contrast)
    labels, palette = flat_regions(rgb, alpha, ink, colors=colors, min_region=min_region)
    fills = region_polygons(labels, alpha, len(palette), epsilon=fill_epsilon)

    strokes = []
    if ink.any():
        dt = cv2.distanceTransform(ink, cv2.DIST_L2, 3)
        skeleton = thin(ink)
        raw = []
        degree = cv2.filter2D(skeleton.astype(np.float32), -1, np.ones((3, 3), np.float32),
                              borderType=cv2.BORDER_CONSTANT) - skeleton
        for path_px in trace_skeleton(skeleton):
            if len(path_px) < min_stroke:
                continue
            ends = [path_px[0], path_px[-1]]
            if len(path_px) <= 3 and all(degree[y, x] >= 3 for y, x in ends):
                continue  # connector inside a junction blob; neighbors' round caps cover it
            pts = np.array([[x, y, max(0.5, float(dt[y, x]))] for y, x in path_px], dtype=np.float32)
            color = rgb[[p[0] for p in path_px], [p[1] for p in path_px]].mean(0)
            closed = len(path_px) > 3 and path_px[0] == path_px[-1]
            raw.append((rdp(pts, line_epsilon), color, closed))
        ink_palette = np.array([c for _, c, _ in raw], dtype=np.float32)
        if len(raw) >= ink_colors:
            cv2.setRNGSeed(1)
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.01)
            _, ink_labels, ink_centers = cv2.kmeans(ink_palette, ink_colors, None, criteria, 3,
                                                    cv2.KMEANS_PP_CENTERS)
            ink_labels = ink_labels.ravel()
        else:
            ink_centers, ink_labels = ink_palette, np.arange(len(raw))
        base = len(palette)
        for (pts, _c, closed), lab in zip(raw, ink_labels):
            strokes.append({"color": int(base + lab), "points": np.round(pts, 2).tolist(), "closed": bool(closed)})
        palette = np.vstack([palette, ink_centers]) if len(raw) else palette
        ink_ids = list(range(base, base + len(ink_centers)))
    else:
        ink_ids = []

    entries = [{"id": i, "rgb": [round(float(v), 4) for v in c],
                "role": "ink" if i in ink_ids else "fill"} for i, c in enumerate(palette)]
    return {
        "version": 1, "source": rel(path), "source_sha256": sha256(path), "size": list(image.size),
        "palette": entries, "fills": fills, "strokes": strokes,
        "stats": {"fills": len(fills), "strokes": len(strokes),
                  "stroke_points": int(sum(len(s["points"]) for s in strokes)),
                  "fill_points": int(sum(len(f["points"]) for f in fills)),
                  "ink_coverage": round(float(ink.mean()), 4)},
        "params": {"colors": colors, "min_region": min_region, "ink_colors": ink_colors, "ink_contrast": ink_contrast,
                   "line_epsilon": line_epsilon, "fill_epsilon": fill_epsilon},
    }


def rasterize(scan, supersample=2):
    """Draw a scan back to RGBA (what the Grease Pencil drawing should look like)."""
    w, h = scan["size"]
    k = supersample
    img = Image.new("RGBA", (w * k, h * k), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    colors = {p["id"]: tuple(int(round(v * 255)) for v in p["rgb"]) + (255,) for p in scan["palette"]}
    for fill in scan["fills"]:
        pts = [(x * k + k / 2, y * k + k / 2) for x, y in fill["points"]]
        draw.polygon(pts, fill=(0, 0, 0, 0) if fill["holdout"] else colors[fill["color"]])
    for stroke in scan["strokes"]:
        color = colors[stroke["color"]]
        pts = stroke["points"]
        for (x0, y0, r0), (x1, y1, r1) in zip(pts, pts[1:]):
            width = max(1, int(round((r0 + r1) * k)))
            draw.line([(x0 * k, y0 * k), (x1 * k, y1 * k)], fill=color, width=width)
        for x, y, r in pts:
            rr = r * k
            draw.ellipse([x * k - rr, y * k - rr, x * k + rr, y * k + rr], fill=color)
    return img.resize((w, h), Image.Resampling.LANCZOS)


def fidelity(scan, source):
    """Compare the rebuilt drawing with the source: color error and coverage overlap."""
    src = np.asarray(Image.open(source).convert("RGBA"), dtype=np.float32) / 255
    out = np.asarray(rasterize(scan), dtype=np.float32) / 255
    both = (src[..., 3] > 0.5) & (out[..., 3] > 0.5)
    union = (src[..., 3] > 0.5) | (out[..., 3] > 0.5)
    err = float(np.abs(src[..., :3][both] - out[..., :3][both]).mean() * 255) if both.any() else 255.0
    return {"mean_color_error": round(err, 2), "coverage_iou": round(float(both.sum() / max(1, union.sum())), 4),
            "note": "Error is against the source pixels; flats are expected to differ from painted gradients."}


def scan_file(path, out, *, preview=None, **options):
    scan = scan_image(path, **options)
    scan["fidelity"] = fidelity(scan, path)
    write_json(out, scan)
    if preview:
        Path(preview).parent.mkdir(parents=True, exist_ok=True)
        rasterize(scan).save(preview)
        scan["preview"] = rel(preview)
    return scan
