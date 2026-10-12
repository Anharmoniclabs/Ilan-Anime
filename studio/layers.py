"""Layer preparation: split atlases, clean mattes, register replacement drawings.

* ``split``    cut a pose atlas into equal cells (keeps a common cell size so
               drawings stay comparable);
* ``matte``    decontaminate edge colors, extend opaque color under transparent
               pixels (prevents halos when resampled), snap near-0/near-1 alpha,
               optional 1px choke; reports how much fringe it found;
* ``register`` align each drawing to a reference using only a *locked* region
               (hull, drum, skull, a fixed prop). Translation by FFT phase
               correlation, optional scale search, sub-pixel refine. Writes the
               aligned cels plus a residual report: a large residual means the
               locked object itself was drawn differently and needs a redraw,
               which no shift can fix.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

from studio.paths import rel, write_json


def split(atlas, grid, out_dir, prefix=None):
    """Split ``atlas`` into ``cols x rows`` cells -> numbered RGBA PNGs."""
    cols, rows = (int(v) for v in str(grid).lower().split("x"))
    image = Image.open(atlas).convert("RGBA")
    cw, ch = image.width // cols, image.height // rows
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    prefix = prefix or Path(atlas).stem
    paths = []
    for r in range(rows):
        for c in range(cols):
            cell = image.crop((c * cw, r * ch, (c + 1) * cw, (r + 1) * ch))
            path = out_dir / f"{prefix}_{r * cols + c + 1:02d}.png"
            cell.save(path)
            paths.append(path)
    report = {"atlas": rel(atlas), "grid": f"{cols}x{rows}", "cell_size": [cw, ch],
              "cels": [rel(p) for p in paths],
              "note": "Cells are cut on a uniform grid; registration and matte review still required."}
    write_json(out_dir / f"{prefix}_split.json", report)
    return report


def _extend_colors(rgb, opaque, iterations=6):
    """Bleed opaque colors outward into transparent/semi pixels (edge decontamination)."""
    rgb = rgb.astype(np.float32)
    known = opaque.astype(np.float32)
    acc = rgb * known[..., None]
    for _ in range(iterations):
        if known.all():
            break
        pad_acc = np.pad(acc, ((1, 1), (1, 1), (0, 0)), mode="edge")
        pad_known = np.pad(known, 1, mode="edge")
        s_acc = sum(pad_acc[1 + dy:1 + dy + rgb.shape[0], 1 + dx:1 + dx + rgb.shape[1]]
                    for dy in (-1, 0, 1) for dx in (-1, 0, 1))
        s_known = sum(pad_known[1 + dy:1 + dy + rgb.shape[0], 1 + dx:1 + dx + rgb.shape[1]]
                      for dy in (-1, 0, 1) for dx in (-1, 0, 1))
        newly = (known == 0) & (s_known > 0)
        acc[newly] = s_acc[newly] / s_known[newly][..., None]
        known = np.where(newly, 1.0, known)
        acc = np.where(known[..., None] > 0, acc, 0)
    return np.where(known[..., None] > 0, acc, rgb)


def matte(src, out, low=8, high=247, choke=0):
    """Clean one RGBA drawing. Returns a fringe report."""
    image = Image.open(src).convert("RGBA")
    arr = np.asarray(image).astype(np.float32)
    rgb, alpha = arr[..., :3], arr[..., 3]
    semi = (alpha > low) & (alpha < high)
    opaque = alpha >= high
    before = None
    if semi.any() and opaque.any():
        # fringe = how far edge colors sit from the nearest interior color
        extended = _extend_colors(rgb, opaque)
        before = float(np.abs(rgb[semi] - extended[semi]).mean())
        rgb = np.where(semi[..., None], extended, rgb)
    alpha = np.where(alpha <= low, 0, np.where(alpha >= high, 255, alpha))
    if choke > 0:
        a_img = Image.fromarray(alpha.astype(np.uint8), "L").filter(ImageFilter.MinFilter(2 * int(choke) + 1))
        alpha = np.asarray(a_img).astype(np.float32)
    rgb = _extend_colors(rgb, alpha >= high)  # colors under transparent pixels match the edge
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.dstack([np.clip(rgb, 0, 255), alpha]).astype(np.uint8), "RGBA").save(out)
    return {"source": rel(src), "output": rel(out), "edge_pixels": int(semi.sum()),
            "edge_color_error": None if before is None else round(before, 2), "choke_px": int(choke)}


# --------------------------------------------------------------- register

def _gray(image):
    arr = np.asarray(image.convert("RGBA"), dtype=np.float32) / 255
    luma = arr[..., :3] @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
    return luma * arr[..., 3]  # transparent areas read as 0


def _lock_mask(reference_size, lock=None, box=None):
    w, h = reference_size
    if lock:
        mask = Image.open(lock).convert("L").resize((w, h), Image.Resampling.NEAREST)
        return np.asarray(mask, dtype=np.float32) / 255
    mask = np.zeros((h, w), dtype=np.float32)
    if box:
        x, y, bw, bh = (int(v) for v in box)
        mask[y:y + bh, x:x + bw] = 1
    else:
        mask[:] = 1
    return mask


def _phase_shift(ref, mov, window):
    """(dy, dx) that moves ``mov`` onto ``ref`` (sub-pixel)."""
    a = np.fft.fft2((ref - ref[window > 0].mean()) * window)
    b = np.fft.fft2((mov - mov[window > 0].mean()) * window)
    cross = a * np.conj(b)
    cross /= np.abs(cross) + 1e-9
    corr = np.fft.ifft2(cross).real
    peak = np.unravel_index(np.argmax(corr), corr.shape)
    shifts = []
    for axis, p in enumerate(peak):
        n = corr.shape[axis]
        prev_i = list(peak)
        next_i = list(peak)
        prev_i[axis] = (p - 1) % n
        next_i[axis] = (p + 1) % n
        c0, c1, c2 = corr[tuple(prev_i)], corr[peak], corr[tuple(next_i)]
        denom = c0 - 2 * c1 + c2
        sub = 0.0 if abs(denom) < 1e-12 else 0.5 * (c0 - c2) / denom
        value = p + sub
        if value > n / 2:
            value -= n
        shifts.append(value)
    return shifts[0], shifts[1]


def _transform(image, size, dx, dy, scale, center):
    cx, cy = center
    # output(x,y) -> input: ((x - dx - cx)/s + cx, (y - dy - cy)/s + cy)
    coeffs = (1 / scale, 0, cx - (dx + cx) / scale, 0, 1 / scale, cy - (dy + cy) / scale)
    return image.transform(size, Image.Transform.AFFINE, coeffs, resample=Image.Resampling.BICUBIC,
                           fillcolor=(0, 0, 0, 0))


def _residual(ref_gray, aligned_gray, mask):
    m = mask > 0.5
    if not m.any():
        return 1.0, 0.0
    a, b = ref_gray[m], aligned_gray[m]
    mad = float(np.abs(a - b).mean())
    a0, b0 = a - a.mean(), b - b.mean()
    ncc = float((a0 * b0).sum() / (np.sqrt((a0 ** 2).sum() * (b0 ** 2).sum()) + 1e-9))
    return mad, ncc


def register(reference, cels, out_dir, lock=None, box=None, scales=(1.0,), max_shift=64,
             residual_limit=0.06, ncc_floor=0.85):
    """Align drawings to ``reference`` on the locked region; write cels + report."""
    ref_img = Image.open(reference).convert("RGBA")
    size = ref_img.size
    mask = _lock_mask(size, lock, box)
    ys, xs = np.nonzero(mask > 0.5)
    if not len(xs):
        raise ValueError("lock region is empty")
    center = (float(xs.mean()), float(ys.mean()))
    window = mask * np.outer(np.hanning(size[1]), np.hanning(size[0])).astype(np.float32)
    window = np.maximum(window, mask * 0.25)
    ref_gray = _gray(ref_img)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for cel in cels:
        img = Image.open(cel).convert("RGBA")
        if img.size != size:
            canvas = Image.new("RGBA", size, (0, 0, 0, 0))
            canvas.paste(img, (0, 0))
            img = canvas
        best = None
        for scale in scales:
            scaled = _transform(img, size, 0, 0, scale, center) if scale != 1.0 else img
            dy, dx = _phase_shift(ref_gray, _gray(scaled), window)
            if abs(dx) > max_shift or abs(dy) > max_shift:
                continue
            aligned = _transform(img, size, dx, dy, scale, center)
            mad, ncc = _residual(ref_gray, _gray(aligned), mask)
            if best is None or mad < best["mad"]:
                best = {"dx": dx, "dy": dy, "scale": scale, "mad": mad, "ncc": ncc, "image": aligned}
        name = Path(cel).name
        if best is None:
            results.append({"cel": rel(cel), "status": "failed", "reason": f"shift beyond {max_shift}px"})
            continue
        before_mad, before_ncc = _residual(ref_gray, _gray(img), mask)
        out_path = out_dir / name
        best["image"].save(out_path)
        ok = best["mad"] <= residual_limit and best["ncc"] >= ncc_floor
        results.append({
            "cel": rel(cel), "output": rel(out_path), "dx": round(best["dx"], 2), "dy": round(best["dy"], 2),
            "scale": best["scale"], "residual_before": round(before_mad, 4), "residual_after": round(best["mad"], 4),
            "ncc_after": round(best["ncc"], 4),
            "status": "aligned" if ok else "needs_redraw",
            "reason": None if ok else "locked region still differs after alignment: the object was redrawn "
                                      "differently (geometry/detail), not just displaced",
        })
    report = {"reference": rel(reference), "lock": rel(lock) if lock else None, "box": box,
              "residual_limit": residual_limit, "ncc_floor": ncc_floor, "cels": results,
              "truth": "Alignment fixes displacement only. needs_redraw cels must be redrawn."}
    write_json(out_dir / "registration.json", report)
    return report
