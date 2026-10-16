"""Motion construction: action plans -> exposure-accurate shot specs.

A motion spec (``motion/<SHOT>.json``) describes a shot the way an animation
supervisor would: elements in draw order, each one a

* ``rigid`` prop (hull, drum, bell, paddle): one drawing, transform keys only;
* ``character``: replacement drawings placed at exact frames (keys,
  breakdowns, in-betweens), never stretched, rotated or scaled to fake acting;
* ``fx``/``secondary``: drawn cycles (wakes, water, hair, cloth) on their own
  clock, optionally travelling with keys;
* ``plate``: background/foreground painting, with parallax.

``parent`` attaches an element to another (passengers ride the hull, the
clapper hangs from the bell). ``contacts`` lock a point on a drawing to an
anchor on another element for a frame range; the checker measures the actual
screen-space distance on every frame, camera and parents included.

``compile`` writes an engine spec. ``check`` returns errors (block the shot)
and warnings (things a reviewer must look at). Neither judges drawing quality.
"""
from __future__ import annotations

import math
from pathlib import Path

from studio.engine.compositor import LAYER_DEFAULTS, Compositor, interpolate
from studio.paths import PROJECT, load_json, resolve, write_json

KINDS = {"rigid", "character", "fx", "secondary", "plate"}
CHARACTER_FORBIDDEN_KEYS = {"scale", "angle"}


class MotionError(ValueError):
    pass


def _drawings(element):
    """Sorted [(frame, drawing, entry)] for a character element."""
    entries = []
    for group in ("poses", "breakdowns", "inbetweens"):
        for entry in element.get(group, []):
            entries.append((int(entry["frame"]), entry["drawing"], dict(entry, group=group)))
    entries.sort(key=lambda item: item[0])
    return entries


def compile_spec(motion: dict) -> dict:
    """Motion spec -> engine spec (layers with exposures, parents, keys)."""
    frames = int(motion["frames"])
    layers = []
    for element in motion["elements"]:
        kind = element.get("kind")
        if kind not in KINDS:
            raise MotionError(f"{element.get('name')}: kind must be one of {sorted(KINDS)}")
        layer = {"name": element["name"], "rate": int(element.get("rate", 3)),
                 "tags": list(element.get("tags", [])),
                 "parallax": float(element.get("parallax", 1.0))}
        for key in ("pivot", "parent", "blend", "opacity", "fit", "in", "out", "effects", "smooth", "loop"):
            if key in element:
                layer[key] = element[key]
        if kind in ("rigid", "plate"):
            layer["source"] = element["source"]
            layer["keys"] = element.get("keys", [])
            if kind == "plate" and "bg" not in layer["tags"]:
                layer["tags"].append("bg")
        elif kind == "character":
            entries = _drawings(element)
            if not entries:
                raise MotionError(f"{element['name']}: character needs drawings (poses/breakdowns/inbetweens)")
            exposures = []
            start = int(element.get("in", 0))
            for i, (frame, drawing, _entry) in enumerate(entries):
                end = entries[i + 1][0] if i + 1 < len(entries) else int(element.get("out", frames))
                exposures.append({"start": frame - start, "end": end - start, "source": drawing})
            layer["source"] = entries[0][1]
            layer["exposures"] = exposures
            layer["keys"] = element.get("keys", [])
            if "character" not in layer["tags"]:
                layer["tags"].append("character")
        else:  # fx / secondary drawn cycles
            if element.get("sequence"):
                layer["sequence"] = element["sequence"]
                layer["loop"] = element.get("loop", True)
            elif element.get("source"):
                layer["source"] = element["source"]
            else:
                raise MotionError(f"{element['name']}: fx needs a drawn sequence or source")
            layer["keys"] = element.get("keys", [])
        if element.get("rate") is not None:
            layer["rate"] = int(element["rate"])
        layers.append(layer)
    return {
        "id": motion["shot"], "size": motion.get("size", [1280, 720]), "frames": frames, "fps": 24,
        "status": motion.get("status", "exploratory"), "stage": "motion",
        "background": motion.get("background_color", [20, 32, 43, 255]),
        "layers": layers, "camera": motion.get("camera", []), "shake": motion.get("shake", []),
        "post": motion.get("post", {}), "audio": motion.get("audio"),
        "contacts": motion.get("contacts", []),
        "truth": "Compiled from a motion spec; exposures and contacts are checked, drawing quality is not.",
    }


def _point_on_screen(comp: Compositor, layer, frame, point):
    """Screen position (spec pixels, camera applied) of a point in a layer's current drawing."""
    state = comp.layer_state(layer, frame, 0.0)
    if state is None:
        return None
    token, _q, params = state
    image_size = comp.spec_size if token[0] == "gen" else comp._load(token[1], layer["fit"]).size
    m = comp.local_matrix(layer, params, image_size, frame)
    cam = comp.camera(frame)
    k = float(layer["parallax"])
    x, y = point
    sx, sy = m[0] * x + m[1] * y + m[2], m[3] * x + m[4] * y + m[5]
    if k == 0:
        return sx, sy
    cw, ch = comp.spec_size
    z = 1 + (float(cam["scale"]) - 1) * k
    r = math.radians(cam["angle"])
    cr, sr = math.cos(r), math.sin(r)
    dx, dy = sx - cw / 2, sy - ch / 2
    return (cw / 2 + z * (cr * dx + sr * dy + cam["x"] * k),
            ch / 2 + z * (-sr * dx + cr * dy + cam["y"] * k))


def _drawing_points(element):
    """{drawing path: {point name: [x, y]}} from pose entries."""
    points = {}
    for _frame, drawing, entry in _drawings(element):
        if entry.get("points"):
            points.setdefault(drawing, {}).update(entry["points"])
    for drawing, pts in (element.get("points") or {}).items():
        points.setdefault(drawing, {}).update(pts)
    return points


def check(motion: dict, base: Path = PROJECT) -> dict:
    """Validate timing, file existence, character rules and contact locks."""
    errors, warnings = [], []
    frames = int(motion.get("frames", 0))
    if frames <= 0:
        errors.append("frames must be positive")
    names = [e.get("name") for e in motion.get("elements", [])]
    if len(names) != len(set(names)):
        errors.append("element names must be unique")
    acting = environment = 0
    for element in motion.get("elements", []):
        name, kind, rate = element.get("name"), element.get("kind"), int(element.get("rate", 3))
        files = [element.get("source")] + list(element.get("sequence", [])) + \
            [d for _, d, _ in _drawings(element)]
        for path in filter(None, files):
            if not resolve(path, base).is_file():
                errors.append(f"{name}: missing drawing {path}")
        if element.get("parent") and element["parent"] not in names:
            errors.append(f"{name}: parent {element['parent']} is not an element")
        if kind == "character":
            entries = _drawings(element)
            used = {k for key in element.get("keys", []) for k in key if k in CHARACTER_FORBIDDEN_KEYS}
            if used and not element.get("allow_transform_reason"):
                errors.append(f"{name}: character keys use {sorted(used)}; scaling/rotating a drawing is not acting. "
                              "Draw the pose, or set allow_transform_reason for a justified exception.")
            start = int(element.get("in", 0))
            for frame, drawing, entry in entries:
                if not 0 <= frame < frames:
                    errors.append(f"{name}: drawing {drawing} at frame {frame} is outside the shot")
                if (frame - start) % rate and not entry.get("impact"):
                    errors.append(f"{name}: {drawing} lands on frame {frame}, off the {rate}s exposure grid "
                                  "(mark impact:true only for scripted 1-frame hits)")
            if entries and entries[0][0] > start:
                warnings.append(f"{name}: nothing exposed before frame {entries[0][0]}")
            distinct = len({d for _, d, _ in entries})
            if distinct >= 2:
                acting += 1
            else:
                warnings.append(f"{name}: one drawing for the whole shot; acting is missing")
            longest = max((b[0] - a[0] for a, b in zip(entries, entries[1:])), default=0)
            if longest > 48 and not element.get("holds_ok"):
                warnings.append(f"{name}: a {longest}-frame hold; confirm it is intentional (set holds_ok)")
        elif kind in ("fx", "secondary", "rigid"):
            if element.get("sequence") or element.get("keys"):
                environment += 1
        elif kind == "plate" and element.get("keys"):
            warnings.append(f"{name}: keyed plate; camera/plate movement never counts as character acting")
    if not acting:
        warnings.append("no character has two or more drawings: the shot has no acting yet")
    if not environment:
        warnings.append("no environmental or prop action (water, wakes, props) is animated")
    # Shared art/animation minimum-separation gate. CHECK ONLY: never silently
    # warp approved cels or replace missing action drawings with transforms.
    for element in motion.get("elements", []):
        rules = element.get("separation_constraints", [])
        if not rules:
            continue
        from studio.drawing.separation import check_pose_points, SeparationError
        all_points = _drawing_points(element)
        drawings = {d for _, d, _ in _drawings(element)}
        if not drawings:
            drawings = set(all_points)
        if not drawings:
            errors.append(f"{element.get('name')}: separation constraints have no named drawing points")
        for drawing in sorted(drawings):
            try:
                violations = check_pose_points(all_points.get(drawing, {}), rules)
                errors.extend(f"{element.get('name')}: {drawing}: {v}" for v in violations)
            except SeparationError as exc:
                errors.append(f"{element.get('name')}: invalid separation rule: {exc}")
    contact_report = []
    if not errors:
        try:
            spec = compile_spec(motion)
            comp = Compositor(spec, base=base, quality="draft")
            elements = {e["name"]: e for e in motion["elements"]}
            layers = {layer["name"]: layer for layer in comp.layers}
            for contact in motion.get("contacts", []):
                contact_report.append(_check_contact(contact, comp, elements, layers, errors))
        except Exception as exc:  # surface compile/engine problems as errors
            errors.append(f"compile failed: {exc}")
    return {"shot": motion.get("shot"), "errors": errors, "warnings": warnings, "contacts": contact_report,
            "truth": "Passing check means timing, files and contacts are consistent; it does not approve the drawing."}


def _check_contact(contact, comp, elements, layers, errors):
    """contact = {element, point, anchor: {element, point}, start, end, tolerance}"""
    name = contact["element"]
    tolerance = float(contact.get("tolerance", 3.0))
    points = _drawing_points(elements[name])
    anchor = contact["anchor"]
    anchor_points = _drawing_points(elements[anchor["element"]]) if anchor["element"] in elements else {}
    worst, worst_frame, missing = 0.0, None, []
    for frame in range(int(contact["start"]), int(contact["end"])):
        layer = layers[name]
        state = comp.layer_state(layer, frame, 0.0)
        if state is None:
            missing.append(frame)
            continue
        drawing = state[0][1]
        local = points.get(drawing, {}).get(contact["point"])
        if local is None:
            missing.append(frame)
            continue
        a_layer = layers[anchor["element"]]
        a_state = comp.layer_state(a_layer, frame, 0.0)
        a_local = anchor.get("xy")
        if a_local is None and a_state is not None:
            a_local = anchor_points.get(a_state[0][1], {}).get(anchor["point"]) or \
                (elements[anchor["element"]].get("anchors") or {}).get(anchor["point"])
        if a_local is None:
            missing.append(frame)
            continue
        p = _point_on_screen(comp, layer, frame, local)
        q = _point_on_screen(comp, a_layer, frame, a_local)
        distance = math.hypot(p[0] - q[0], p[1] - q[1])
        if distance > worst:
            worst, worst_frame = distance, frame
    label = f"{name}.{contact['point']} -> {anchor['element']}.{anchor.get('point', 'xy')}"
    if missing:
        errors.append(f"contact {label}: no point data on frames {missing[:5]}{'...' if len(missing) > 5 else ''}")
    if worst > tolerance:
        errors.append(f"contact {label}: drifts {worst:.1f}px at frame {worst_frame} (tolerance {tolerance}px)")
    return {"contact": label, "max_px": round(worst, 2), "worst_frame": worst_frame, "tolerance": tolerance,
            "frames_without_points": len(missing)}


def compile_file(path, out):
    motion = load_json(path)
    report = check(motion)
    if report["errors"]:
        raise MotionError("; ".join(report["errors"]))
    spec = compile_spec(motion)
    write_json(out, spec)
    return spec, report
