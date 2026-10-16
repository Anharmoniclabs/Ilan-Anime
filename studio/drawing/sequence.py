"""Temporal minimum-clearance enforcement across frames of draft drawing IR.

The tool never invents character acting. Every input frame is a separate
existing drawing IR. Outputs are non-destructive frames, corrected IR, paired
comparison video, per-frame numeric evidence and native studio motion specs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess

from PIL import Image, ImageDraw

from studio.drawing import render
from studio.drawing.schema import validate_drawing
from studio.drawing.separation import apply_drawing, SeparationError


def _read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _save(path, obj):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _point(drawing, spec):
    p = next(p for p in drawing["primitives"] if p["id"] == spec["id"])
    return p["curve"][spec["segment"]][spec["point"]]


def gap(drawing, rule):
    a, b = _point(drawing, rule["upper"]), _point(drawing, rule["lower"])
    x, y = rule.get("axis", [0, -1])
    length = math.hypot(x, y)
    if length <= 1e-12:
        raise SeparationError("zero axis")
    return ((a[0] - b[0]) * x + (a[1] - b[1]) * y) / length


def panel(a, b, number, raw_gap, fixed_gap, threshold, kind):
    """RGB review canvas only, never written back as approved artwork."""
    a, b = a.convert("RGBA"), b.convert("RGBA")
    w, h = a.size
    left = Image.new("RGBA", (w, h), "#344454")
    right = left.copy()
    left.alpha_composite(a)
    right.alpha_composite(b)
    im = Image.new("RGB", (w*2, h+64), "#1b2331")
    im.paste(left.convert("RGB"), (0, 45))
    im.paste(right.convert("RGB"), (w, 45))
    d = ImageDraw.Draw(im)
    d.text((12, 14), "BEFORE - original geometry", fill="#ffffff")
    d.text((w+12, 14), "AFTER - corrected geometry", fill="#a3ffe2")
    d.text((12, h+45), f"frame {number:03d} | minimum {threshold:g} | before {raw_gap:.1f} | after {fixed_gap:.1f}", fill="#ffffff")
    d.text((w+12, h+45), f"source kind: {kind}", fill="#bed0dc")
    return im


def _video(out, frames, fps):
    binary = shutil.which("ffmpeg")
    if not binary:
        return False
    command = [binary, "-y", "-hide_banner", "-loglevel", "error", "-framerate",
               str(fps), "-i", str(frames / "%04d.png"), "-vf",
               "pad=ceil(iw/2)*2:ceil(ih/2)*2", "-c:v", "libx264", "-pix_fmt",
               "yuv420p", "-movflags", "+faststart", str(out)]
    p = subprocess.run(command, capture_output=True, text=True, timeout=240)
    if p.returncode:
        raise RuntimeError(f"ffmpeg failed: {p.stderr[:500]}")
    return True


def _graph(rows, minimum, out):
    w, h, margin = 1000, 330, 60
    im = Image.new("RGB", (w, h), "#1b2534")
    d = ImageDraw.Draw(im)
    high = max(minimum+8, *(r["before_min_gap"]+7 for r in rows))
    def xy(i, value):
        return (margin+(w-2*margin)*i/max(1,len(rows)-1),
                h-margin-(h-2*margin)*value/high)
    d.line([(margin, h-margin), (w-margin, h-margin)], fill="#a0b0bf", width=2)
    y = xy(0, minimum)[1]
    d.line([(margin,y),(w-margin,y)], fill="#eacb75", width=2)
    for key, col in [("before_min_gap", "#ff887a"), ("after_min_gap", "#70e2c1")]:
        d.line([xy(i,row[key]) for i,row in enumerate(rows)], fill=col, width=4)
    d.text((margin,10), "FRAME-BY-FRAME CONTROL POINT CLEARANCE", fill="white")
    d.text((margin,32), "red: uncorrected  green: corrected  gold: minimum", fill="#c4d0da")
    im.save(out)


def _motion(rows, rule, output, correct, dims, fps, kind):
    root = "after" if correct else "before"
    frames, point_map = [], {}
    for row in rows:
        idx = row["frame"]
        png = str(output / root / f"{idx:04d}.png")
        ir = _read(output / "corrected_ir" / f"{idx:04d}.drawing.json") if correct else _read(row["source"])
        frames.append(png)
        point_map[png] = {label: _point(ir, ref)
                          for j, pair in enumerate(rule)
                          for label, ref in ((f"pair{j}.upper", pair["upper"]),
                                             (f"pair{j}.lower", pair["lower"]))}
    qa_rules = [{"upper": f"pair{j}.upper", "lower": f"pair{j}.lower",
                 "minimum": pair["minimum"], "axis": pair.get("axis",[0,-1])}
                for j,pair in enumerate(rule)]
    return {"shot":"SEPARATION-TEST-001", "size":list(dims), "frames":len(rows),
            "fps":fps, "status":"exploratory", "source_kind":kind,
            "elements":[{"name":"constrained_layer", "kind":"fx", "rate":1,
                         "sequence":frames, "loop":False, "points":point_map,
                         "separation_constraints":qa_rules}]}


def run(manifest, out):
    manifest, out = Path(manifest).resolve(), Path(out).resolve()
    if out.exists() and any(out.iterdir()):
        raise ValueError(f"refusing to overwrite existing take: {out}")
    data = _read(manifest)
    files, rules, fps = data.get("frames"), data.get("rules"), data.get("fps",24)
    if not isinstance(files, list) or not 1 <= len(files) <= 600:
        raise ValueError("frames must contain 1..600 named drawing IRs")
    if not isinstance(rules, list) or not 1 <= len(rules) <= 512:
        raise ValueError("rules must contain 1..512 explicit paired-point rules")
    if type(fps) is not int or not 1 <= fps <= 60:
        raise ValueError("fps must be 1..60")
    if data.get("approved") is True or data.get("status") in ("author-approved","canonical"):
        raise ValueError("approved sequence cannot be modified")
    kind = data.get("source_kind","unverified-source")
    if kind not in ("synthetic-fixture","unverified-source","production-draft"):
        raise ValueError("unknown source_kind")
    for category in ("before","after","comparison","corrected_ir"):
        (out/category).mkdir(parents=True, exist_ok=True)
    dims, rows = None, []
    for i, entry in enumerate(files):
        if not isinstance(entry, dict) or set(entry) != {"drawing"}:
            raise ValueError(f"frame {i}: need drawing path")
        path = Path(entry["drawing"])
        path = path.resolve() if path.is_absolute() else (manifest.parent/path).resolve()
        d = _read(path)
        # The manifest, not a source IR, owns constraints for this run.
        d.pop("separation_constraints",None)
        validate_drawing(d)
        if d.get("approved") is True or d.get("status") in ("author-approved","canonical"):
            raise ValueError(f"frame {i}: approved drawing cannot be modified")
        if dims is None: dims = tuple(d["canvas"])
        elif dims != tuple(d["canvas"]): raise ValueError("canvas mismatch")
        before = [gap(d,r) for r in rules]
        corrected, adjustments = apply_drawing(d,rules)
        after = [gap(corrected,r) for r in rules]
        for j,r in enumerate(rules):
            if after[j] < r["minimum"]-1e-5:
                raise RuntimeError(f"frame {i}, rule {j}: correction failed")
            oldmid = [(_point(d,r["upper"])[k]+_point(d,r["lower"])[k])/2 for k in (0,1)]
            newmid = [(_point(corrected,r["upper"])[k]+_point(corrected,r["lower"])[k])/2 for k in (0,1)]
            if math.dist(oldmid,newmid)>1e-5:
                raise RuntimeError(f"frame {i}, rule {j}: midpoint changed")
        a = render.render(d,supersample=2)
        b = render.render(corrected,supersample=2)
        a.save(out/"before"/f"{i:04d}.png")
        b.save(out/"after"/f"{i:04d}.png")
        panel(a,b,i,min(before),min(after),rules[0]["minimum"],kind).save(
            out/"comparison"/f"{i:04d}.png")
        _save(out/"corrected_ir"/f"{i:04d}.drawing.json",corrected)
        rows.append({"frame":i,"source":str(path),
                     "source_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
                     "before_gaps":before,"after_gaps":after,
                     "before_min_gap":min(before),"after_min_gap":min(after),
                     "delta":max(x["delta"] for x in adjustments)})
    violations_before = sum(any(row["before_gaps"][j]<r["minimum"]-1e-6
                                for j,r in enumerate(rules)) for row in rows)
    violations_after = sum(any(row["after_gaps"][j]<r["minimum"]-1e-6
                               for j,r in enumerate(rules)) for row in rows)
    _graph(rows, rules[0]["minimum"], out/"measurement.png")
    _save(out/"before-motion.json",_motion(rows,rules,out,False,dims,fps,kind))
    _save(out/"after-motion.json",_motion(rows,rules,out,True,dims,fps,kind))
    videos={part:_video(out/f"{part}.mp4",out/part,fps)
            for part in ("before","after","comparison")}
    report={"frame_count":len(rows),"fps":fps,"source_kind":kind,
            "manifest":str(manifest),"original_violating_frames":violations_before,
            "after_violating_frames":violations_after,
            "max_correction_px":max(r["delta"] for r in rows),
            "max_correction_step_px":max((abs(b["delta"]-a["delta"])
                                           for a,b in zip(rows,rows[1:])),default=0),
            "midpoints_preserved":True,"schema_valid":True,"videos_created":videos,
            "anatomical_quality":"not_assessed","ink_quality":"not_assessed",
            "character_identity":"not_assessed","author_approved":False,
            "frames":rows}
    _save(out/"report.json",report)
    return report


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest",required=True)
    parser.add_argument("--out",required=True)
    args=parser.parse_args(argv)
    report=run(args.manifest,args.out)
    print(json.dumps({k:v for k,v in report.items() if k!="frames"},indent=2))


if __name__=="__main__":
    main()
