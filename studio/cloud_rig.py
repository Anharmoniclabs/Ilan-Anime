"""Geometry gates for cloud-produced character/prop animation.

This checks observable coordinates, not artistic quality. A sparse key-pose
packet can pass geometry while remaining UNFINISHED. Full-frame evidence is
required before claiming an animated action is mechanically verified.
"""
from __future__ import annotations

import math


class RigError(ValueError):
    pass


def _point(value, label):
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise RigError(f"{label} must be an [x,y] point")
    x, y = value
    if any(isinstance(z, bool) or not isinstance(z, (int, float))
           or not math.isfinite(z) for z in (x, y)):
        raise RigError(f"{label} has non-finite coordinates")
    return (float(x), float(y))


def _distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _lerp(a, b, t):
    return (a[0] * (1 - t) + b[0] * t, a[1] * (1 - t) + b[1] * t)


def validate_action(spec):
    """Validate bell mechanics from explicit frame-indexed observed poses.

    Required: shot, fps, frames, poses. Each pose contains pole endpoints,
    hand contact coordinates + normalized pole positions, joint chains,
    and independently specified bell shell and clapper locations.

    Error messages are evidence, not commands to invent in-betweens.
    """
    if spec.get("shot") != "S01-05" or spec.get("fps") != 24 or spec.get("frames") != 168:
        raise RigError("Bell reference is exactly S01-05 / 168 frames / 24 fps")
    poses = spec.get("poses")
    if not isinstance(poses, list) or not poses:
        raise RigError("Missing inspected pose measurements")
    tolerance = spec.get("tolerance_px", 4.0)
    if not isinstance(tolerance, (int, float)) or not 0.1 <= tolerance <= 12:
        raise RigError("Tolerance must be from 0.1 to 12 pixels")
    errors = []
    lengths = {}
    seen = set()
    grip_reference = {}
    regrips = set(spec.get("regrip_frames", []))
    beats = set(spec.get("impact_frames", []))
    observed_beats = set()
    for pose in poses:
        f = pose.get("frame")
        if not isinstance(f, int) or isinstance(f, bool) or not 0 <= f < 168 or f in seen:
            errors.append(f"Invalid or duplicate frame {f}")
            continue
        seen.add(f)
        try:
            a = _point(pose["pole"]["a"], "pole.a")
            b = _point(pose["pole"]["b"], "pole.b")
            length = _distance(a, b)
            if length < 20:
                errors.append(f"f{f}: pole collapsed")
            lengths.setdefault("pole", []).append((f, length))
            bell = pose["bell"]
            pivot = _point(bell["pivot"], "bell.pivot")
            if _distance(pivot, b) > tolerance:
                errors.append(f"f{f}: bell pivot detached from pole endpoint")
            clapper = pose["clapper"]
            hinge = _point(clapper["hinge"], "clapper.hinge")
            if _distance(hinge, _point(bell["clapper_anchor"], "bell.clapper_anchor")) > tolerance:
                errors.append(f"f{f}: clapper hinge detached from bell")
            tip = _point(clapper["tip"], "clapper.tip")
            rim = [_point(p, "bell.rim") for p in bell["rim"]]
            if len(rim) != 2:
                errors.append(f"f{f}: two independently measured rim contacts required")
            else:
                gap = min(_distance(tip, r) for r in rim)
                if f in beats:
                    observed_beats.add(f)
                    if gap > tolerance:
                        errors.append(f"f{f}: clapper did not reach rim at impact")
                elif gap < 0.75:
                    errors.append(f"f{f}: clapper appears stuck to the rim")
            hands = pose.get("hands", {})
            arms = pose.get("arms", {})
            if set(hands) != {"left", "right"} or set(arms) != {"left", "right"}:
                errors.append(f"f{f}: both hands and both joint chains required")
                continue
            for side in ("left", "right"):
                hand = hands[side]
                t = hand["grip_t"]
                if isinstance(t, bool) or not isinstance(t, (int, float)) or not 0 <= t <= 1:
                    errors.append(f"f{f}: {side} invalid pole grip fraction")
                    continue
                pos = _point(hand["point"], f"{side} hand")
                pole_pos = _lerp(a, b, t)
                if _distance(pos, pole_pos) > tolerance:
                    errors.append(f"f{f}: {side} hand slipped off pole")
                if side in grip_reference and abs(t - grip_reference[side]) > 0.02 and f not in regrips:
                    errors.append(f"f{f}: {side} grip changed without a drawn regrip")
                grip_reference[side] = t
                arm = arms[side]
                shoulder = _point(arm["shoulder"], f"{side}.shoulder")
                elbow = _point(arm["elbow"], f"{side}.elbow")
                wrist = _point(arm["wrist"], f"{side}.wrist")
                if _distance(wrist, pos) > tolerance:
                    errors.append(f"f{f}: {side} wrist and hand disagree")
                lengths.setdefault(f"{side}.upper", []).append((f, _distance(shoulder, elbow)))
                lengths.setdefault(f"{side}.lower", []).append((f, _distance(elbow, wrist)))
        except (KeyError, TypeError, ValueError, RigError) as exc:
            errors.append(f"f{f}: malformed action evidence ({exc})")
    if not {0, 167}.issubset(seen):
        errors.append("First and last frames must be measured")
    for name, items in lengths.items():
        if not items:
            continue
        baseline = items[0][1]
        if baseline < 5:
            errors.append(f"{name}: degenerate geometry")
            continue
        for f, length in items[1:]:
            if abs(length / baseline - 1) > (0.03 if name == "pole" else 0.08):
                errors.append(f"f{f}: {name} changed length ({baseline:.1f} to {length:.1f}px)")
    if beats - observed_beats:
        errors.append(f"Impact frames lack measurements: {sorted(beats - observed_beats)}")
    measured = sorted(seen)
    return {
        "shot": "S01-05",
        "ok": not errors,
        "errors": errors,
        "measured_frames": measured,
        "measured_count": len(seen),
        "required_frames": 168,
        "complete_frame_coverage": len(seen) == 168,
        "mechanics_verified": not errors and len(seen) == 168,
        "art_and_acting_approved": False,
        "note": "Geometry cannot validate anatomy, compelling acting, full-resolution drawings, audio or author acceptance.",
    }
