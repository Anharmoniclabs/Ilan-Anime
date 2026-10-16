"""Minimum signed-separation constraint shared by artwork and animation.

Scalar rule: delta=max(0, minimum-(upper-lower));
             upper'=upper+delta/2, lower'=lower-delta/2.
In 2D, apply the same correction along a normalized, explicit axis pointing
from lower toward upper. Screen-space 'up' is (0,-1), not (0,1).

Do not apply to approved assets or infer what anatomical pairs should move.
A renderer may opt in using drawing['separation_constraints']; motion QA
reports violations without modifying any actual drawing.
"""
from __future__ import annotations

import copy
import math
from typing import Mapping


class SeparationError(ValueError):
    """Malformed or unsatisfiable separation requirement."""


def _number(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise SeparationError(f"{name}: expected finite numeric value")
    return float(value)


def scalar_pair(upper, lower, minimum):
    """Exact symmetric one-dimensional projection; preserves pair midpoint."""
    u, l = _number(upper, "upper"), _number(lower, "lower")
    m = _number(minimum, "minimum")
    if m < 0:
        raise SeparationError("minimum cannot be negative")
    delta = max(0.0, m - (u - l))
    return u + delta / 2, l - delta / 2, delta


def vector_pair(upper, lower, minimum, axis=(0.0, -1.0)):
    """Enforce the signed gap along an arbitrary oriented axis in 2D."""
    if not isinstance(upper, (list, tuple)) or len(upper) != 2:
        raise SeparationError("upper must be [x,y]")
    if not isinstance(lower, (list, tuple)) or len(lower) != 2:
        raise SeparationError("lower must be [x,y]")
    if not isinstance(axis, (list, tuple)) or len(axis) != 2:
        raise SeparationError("axis must be [x,y]")
    ux, uy = (_number(v, "upper") for v in upper)
    lx, ly = (_number(v, "lower") for v in lower)
    ax, ay = (_number(v, "axis") for v in axis)
    length = math.hypot(ax, ay)
    if length < 1e-12:
        raise SeparationError("axis must be nonzero")
    ax, ay = ax / length, ay / length
    m = _number(minimum, "minimum")
    if m < 0:
        raise SeparationError("minimum cannot be negative")
    gap = (ux - lx) * ax + (uy - ly) * ay
    delta = max(0.0, m - gap)
    return ([ux + ax * delta / 2, uy + ay * delta / 2],
            [lx - ax * delta / 2, ly - ay * delta / 2], delta)


def _get_point(primitives, spec):
    if not isinstance(spec, Mapping) or set(spec) != {"id", "segment", "point"}:
        raise SeparationError("point ref must contain exactly id, segment, point")
    ident, segment, index = spec["id"], spec["segment"], spec["point"]
    if type(segment) is not int or type(index) is not int or not 0 <= index <= 3:
        raise SeparationError("segment must be int and point must be 0..3")
    matches = [p for p in primitives if p.get("id") == ident]
    if len(matches) != 1 or not 0 <= segment < len(matches[0]["curve"]):
        raise SeparationError(f"unknown curve control point: {spec}")
    return matches[0], segment, index


def apply_drawing(drawing, rules=None):
    """Apply bounded pair rules to a fresh copy of the drawing IR.

    Example rule:
    {"upper":{"id":"fabric.panel","segment":0,"point":1},
     "lower":{"id":"fabric.panel","segment":1,"point":2},
     "minimum":8,"axis":[0,-1]}

    Shared endpoints of a single Bézier primitive move together to preserve
    continuity. Rejects changes that violate the drawing schema. Never mutates
    input geometry or artwork marked author-approved/canonical.
    """
    from studio.drawing.schema import validate_drawing

    result = copy.deepcopy(drawing)
    embedded = result.pop("separation_constraints", [])
    rules = embedded if rules is None else rules
    if not isinstance(rules, list) or len(rules) > 512:
        raise SeparationError("separation_constraints must be a list of <=512 rules")
    if rules and (result.get("status") in ("author-approved", "canonical")
                  or result.get("approved") is True):
        raise SeparationError("refusing to correct author-approved geometry")
    validate_drawing(result)
    reports = []
    for rule in rules:
        if not isinstance(rule, dict) or set(rule) not in (
            {"upper", "lower", "minimum"}, {"upper", "lower", "minimum", "axis"}
        ):
            raise SeparationError("rule needs upper, lower, minimum, optional axis")
        up, ui, uj = _get_point(result["primitives"], rule["upper"])
        lo, li, lj = _get_point(result["primitives"], rule["lower"])
        if up is lo and ui == li and uj == lj:
            raise SeparationError("pair cannot reference the same point")
        old_u, old_l = list(up["curve"][ui][uj]), list(lo["curve"][li][lj])
        new_u, new_l, delta = vector_pair(
            old_u, old_l, rule["minimum"], rule.get("axis", [0, -1])
        )
        for prim, origin, dest in ((up, old_u, new_u), (lo, old_l, new_l)):
            for segment in prim["curve"]:
                for idx in (0, 3):
                    if list(segment[idx]) == origin:
                        segment[idx] = list(dest)
        up["curve"][ui][uj] = new_u
        lo["curve"][li][lj] = new_l
        reports.append({"upper": rule["upper"], "lower": rule["lower"],
                        "minimum": rule["minimum"], "axis": rule.get("axis", [0, -1]),
                        "delta": round(delta, 7)})
    validate_drawing(result)
    return result, reports


def check_pose_points(points: Mapping, rules):
    """Non-destructive per-pose QA. Rejects missing points and insufficient gaps."""
    violations = []
    for i, rule in enumerate(rules):
        if not isinstance(rule, dict) or set(rule) not in (
            {"upper", "lower", "minimum"}, {"upper", "lower", "minimum", "axis"}
        ):
            raise SeparationError(f"rule {i}: needs upper, lower, minimum, optional axis")
        a, b = rule["upper"], rule["lower"]
        if not isinstance(a, str) or not isinstance(b, str):
            raise SeparationError(f"rule {i}: point names must be strings")
        if a not in points or b not in points:
            violations.append(f"rule {i}: missing point {a if a not in points else b}")
            continue
        _, _, delta = vector_pair(
            points[a], points[b], rule["minimum"], rule.get("axis", [0, -1])
        )
        if delta > 1e-6:
            violations.append(f"rule {i}: {a}/{b} need {delta:.3f}px more separation")
    return violations
