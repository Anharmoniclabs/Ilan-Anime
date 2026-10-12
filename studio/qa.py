"""Automated review flags and targeted repair tasks.

Measures what can be measured and hands the rest to a human/agent reviewer:

* ``boil``: between consecutive drawings of a character layer, interior color
  changes much more than the silhouette does -> the drawing was re-rendered
  rather than re-posed (texture crawl at playback);
* ``lock_drift``: a region declared fixed (hull, drum, skull) moves between
  consecutive rendered frames beyond tolerance, after removing camera motion;
* ``contact``: motion-spec contact locks that drift (from ``motion.check``);
* ``matte``: drawings with contaminated edge colors (halos when composited);
* ``freeze``: picture frozen longer than allowed outside scripted holds;
* ``frames``: rendered length differs from the spec;
* ``no_acting``: no character drawing changes (animatic holds included).

Each flag carries frames/timecodes and becomes a revision task for the role
that owns the fix. Passing QA means "no measured defect", never "approved".
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from studio.engine import Compositor
from studio.layers import _phase_shift
from studio.paths import PROJECT, rel, resolve, timecode, write_json

OWNER = {"no_acting": "key-animator", "boil": "key-animator", "lock_drift": "key-animator", "contact": "key-animator",
         "matte": "cleanup-artist", "freeze": "animation-supervisor", "frames": "compositor"}


def _rgba(path, base):
    return np.asarray(Image.open(resolve(path, base)).convert("RGBA"), dtype=np.float32) / 255


def acting_flags(spec):
    """A shot whose characters never change drawing has no acting, whatever the camera does."""
    if spec.get("stage") == "animatic":
        return [{"type": "no_acting", "layer": None, "frame": 0,
                 "detail": "animatic hold: keyframe/slate under a camera move; the scripted action still "
                           "needs registered replacement drawings"}]
    acting = [layer["name"] for layer in spec.get("layers", []) if "character" in layer.get("tags", [])
              and len({e["source"] for e in layer.get("exposures", [])} | set(layer.get("sequence", []))) >= 2]
    if not acting:
        return [{"type": "no_acting", "layer": None, "frame": 0,
                 "detail": "no character layer changes drawing; camera or layer motion is not acting"}]
    return []


def boil_flags(spec, base=PROJECT, ratio_limit=2.5, interior_limit=0.06):
    flags = []
    for layer in spec.get("layers", []):
        if "character" not in layer.get("tags", []) or not layer.get("exposures"):
            continue
        exposures = layer["exposures"]
        for a, b in zip(exposures, exposures[1:]):
            if a["source"] == b["source"]:
                continue
            A, B = _rgba(a["source"], base), _rgba(b["source"], base)
            if A.shape != B.shape:
                flags.append({"type": "boil", "layer": layer["name"], "frame": b["start"],
                              "detail": "drawings differ in size; register them to a common canvas"})
                continue
            both = (A[..., 3] > 0.9) & (B[..., 3] > 0.9)
            xor = ((A[..., 3] > 0.5) != (B[..., 3] > 0.5)).mean()
            if not both.any():
                continue
            interior = float(np.abs(A[..., :3][both] - B[..., :3][both]).mean())
            ratio = interior / max(xor, 1e-3)
            if interior > interior_limit and ratio > ratio_limit:
                flags.append({"type": "boil", "layer": layer["name"], "frame": b["start"],
                              "metric": {"interior_change": round(interior, 4), "silhouette_change": round(float(xor), 4)},
                              "detail": f"{Path(a['source']).name} -> {Path(b['source']).name}: interior re-rendered "
                                        "more than the pose changed"})
    return flags


def matte_flags(spec, base=PROJECT, limit=20.0):
    from studio.layers import _extend_colors
    flags, seen = [], set()
    for layer in spec.get("layers", []):
        paths = [layer.get("source")] + layer.get("sequence", []) + [e["source"] for e in layer.get("exposures", [])]
        for path in filter(None, paths):
            if path in seen:
                continue
            seen.add(path)
            arr = _rgba(path, base) * 255
            alpha = arr[..., 3]
            semi, opaque = (alpha > 8) & (alpha < 247), alpha >= 247
            if not semi.any() or not opaque.any() or opaque.all():
                continue
            extended = _extend_colors(arr[..., :3], opaque)
            err = float(np.abs(arr[..., :3][semi] - extended[semi]).mean())
            if err > limit:
                flags.append({"type": "matte", "layer": layer["name"], "frame": None,
                              "metric": {"edge_color_error": round(err, 2)},
                              "detail": f"{path}: edge colors off by {err:.1f}/255; run `studio layers matte`"})
    return flags


def lock_drift_flags(comp: Compositor, locks, tolerance=1.0, step=1):
    """locks: [{"name", "box": [x,y,w,h] (spec px), "start", "end", "moves_with": optional}]"""
    flags = []
    for lock in locks:
        x, y, w, h = (int(round(v * comp.out_scale)) for v in lock["box"])
        start, end = int(lock.get("start", 0)), int(lock.get("end", comp.frames))
        prev = None
        worst = (0.0, None)
        for frame in range(start, end, step):
            arr = comp.draw_array(frame)[y:y + h, x:x + w] @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
            if prev is not None:
                window = np.outer(np.hanning(arr.shape[0]), np.hanning(arr.shape[1])).astype(np.float32)
                dy, dx = _phase_shift(prev, arr, window)
                cam_a, cam_b = comp.camera(frame - step), comp.camera(frame)
                cdx = (cam_b["x"] - cam_a["x"]) * comp.out_scale
                cdy = (cam_b["y"] - cam_a["y"]) * comp.out_scale
                drift = float(np.hypot(-dx - cdx, -dy - cdy)) / comp.out_scale
                if drift > worst[0]:
                    worst = (drift, frame)
                if drift > tolerance:
                    flags.append({"type": "lock_drift", "layer": lock["name"], "frame": frame,
                                  "metric": {"drift_px": round(drift, 2), "tolerance": tolerance},
                                  "detail": f"locked region '{lock['name']}' moved {drift:.1f}px without a camera move"})
            prev = arr
    return flags


def freeze_flags(comp: Compositor, limit=72, allowed=()):
    """Runs of identical composited frames longer than ``limit`` (scripted holds excluded)."""
    flags, run_start, prev = [], 0, None
    for frame in range(comp.frames + 1):
        cur = None if frame == comp.frames else comp.draw_array(frame)
        same = prev is not None and cur is not None and np.array_equal(prev, cur)
        if not same:
            length = frame - run_start
            if prev is not None and length > limit and not any(a <= run_start < b for a, b in allowed):
                flags.append({"type": "freeze", "layer": None, "frame": run_start,
                              "metric": {"frames": length},
                              "detail": f"picture frozen {length} frames from frame {run_start}"})
            run_start = frame
        prev = cur
    return flags


def review(spec, *, base=PROJECT, motion=None, render=None, out_dir, scale=0.5, freeze_limit=72):
    """Run all checks; write qa_report.json, a flagged-frame sheet and revision task stubs."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    flags = acting_flags(spec) + boil_flags(spec, base) + matte_flags(spec, base)
    comp = Compositor(spec, base=base, quality="draft", scale=scale)
    flags += lock_drift_flags(comp, spec.get("locks", []))
    holds = [(h["start"], h["end"]) for h in spec.get("post", {}).get("harmony", [])]
    holds += [(h["start"], h["end"]) for h in spec.get("holds", [])]
    flags += freeze_flags(comp, freeze_limit, holds)
    if motion is not None:
        from studio.motion import check
        report = check(motion, base)
        for message in report["errors"]:
            if message.startswith("contact"):
                frame = None
                if "at frame" in message:
                    frame = int(message.split("at frame")[1].split()[0])
                flags.append({"type": "contact", "layer": message.split()[1].split(".")[0], "frame": frame,
                              "detail": message})
    if render is not None:
        from studio.engine.io import probe_frames
        decoded = probe_frames(render)
        if decoded != spec["frames"]:
            flags.append({"type": "frames", "layer": None, "frame": None,
                          "detail": f"render has {decoded} frames, spec {spec['frames']}"})
    for flag in flags:
        flag["timecode"] = None if flag.get("frame") is None else timecode(flag["frame"])
        flag["owner"] = OWNER[flag["type"]]
    sheet = _flag_sheet(comp, flags, out_dir / "flagged_frames.jpg")
    tasks = revision_tasks(spec["id"], flags)
    report = {"shot": spec["id"], "flags": flags, "flag_count": len(flags), "sheet": rel(sheet) if sheet else None,
              "revision_tasks": tasks,
              "not_checked": ["drawing quality", "identity/likeness", "acting intent", "style finish"],
              "truth": "Zero flags means no measured defect; a reviewer must still watch it at speed."}
    write_json(out_dir / "qa_report.json", report)
    return report


def _flag_sheet(comp, flags, path, limit=12):
    frames = sorted({f["frame"] for f in flags if f.get("frame") is not None})[:limit]
    if not frames:
        return None
    tiles = []
    for frame in frames:
        tile = comp.draw(frame)
        draw = ImageDraw.Draw(tile)
        labels = ", ".join(sorted({f["type"] for f in flags if f.get("frame") == frame}))
        draw.rectangle([0, 0, tile.width, 22], fill=(0, 0, 0))
        draw.text((6, 4), f"f{frame} {timecode(frame)} {labels}", fill=(255, 200, 80))
        tiles.append(tile)
    w, h = tiles[0].size
    cols = min(3, len(tiles))
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (w * cols, h * rows), (10, 10, 10))
    for i, tile in enumerate(tiles):
        sheet.paste(tile, ((i % cols) * w, (i // cols) * h))
    sheet.save(path, quality=85)
    return path


def revision_tasks(shot_id, flags):
    """Group flags by owning role into ledger task stubs (coordinator adds ids/paths/deps)."""
    grouped = {}
    for flag in flags:
        grouped.setdefault(flag["owner"], []).append(flag)
    tasks = []
    for role, items in sorted(grouped.items()):
        where = "; ".join(f"{f['type']}@{f['timecode'] or 'n/a'}: {f['detail']}" for f in items[:12])
        tasks.append({"role": role, "shots": [shot_id],
                      "objective": f"Repair only the flagged defects in {shot_id}, then rerender for review: {where}",
                      "acceptance_criteria": ["Each listed flag is fixed or explained with evidence",
                                              "No new drawing replaces acting with warps or camera moves",
                                              "Rerun `python -m studio qa` and attach the new report"],
                      "flags": items})
    return tasks
