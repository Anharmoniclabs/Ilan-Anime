"""Runs *inside* Blender: apply the NPR render contract, step animation, render
element layers. Launched by ``python -m studio blender render``; you rarely
call it directly:

    blender -b scene.blend --python studio/blender_npr_setup.py -- \
        --out renders/blender/S01-11 --frames 0-239 --step 2 --layers hull,drum,beheto

What it enforces (see .agents/skills/blender-npr-3d-anime/SKILL.md):
EEVEE (either Python identifier), Standard view transform, 24 fps, shot canvas
size, motion blur off, transparent film, Z + Cryptomatte passes, legacy-EEVEE
shadow cascade 4096 and AO when those settings exist, PNG RGBA output, and a
Stepped F-curve modifier on every animated object except the camera and
objects marked with the custom property ``npr_smooth`` (environment/camera may
move on 1s). Each layer renders with the other element collections as
holdouts, so occlusion is cut correctly. A JSON report records what was
applied and every setting that did not exist in this Blender version.

Written against the 4.2+ and 5.x Python APIs with version guards; layered
(slotted) actions from 4.4+ are handled.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

ENGINE_IDS = ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE")


def _set(obj, attr, value, applied, missing, label):
    if obj is not None and hasattr(obj, attr):
        try:
            setattr(obj, attr, value)
            applied[label] = value
            return True
        except (TypeError, ValueError, AttributeError) as exc:  # enum not available in this version
            missing.append(f"{label}: {exc}")
            return False
    missing.append(f"{label}: not in this Blender version")
    return False


def apply_settings(scene, width, height, applied, missing):
    render = scene.render
    engine = None
    for engine_id in ENGINE_IDS:
        try:
            render.engine = engine_id
            engine = engine_id
            break
        except (TypeError, ValueError):
            continue
    if engine is None:
        raise RuntimeError("EEVEE is not available in this Blender build")
    applied["engine"] = engine
    _set(scene.view_settings, "view_transform", "Standard", applied, missing, "view_transform")
    _set(scene.view_settings, "look", "None", applied, missing, "look")
    _set(render, "fps", 24, applied, missing, "fps")
    _set(render, "fps_base", 1.0, applied, missing, "fps_base")
    _set(render, "resolution_x", int(width), applied, missing, "resolution_x")
    _set(render, "resolution_y", int(height), applied, missing, "resolution_y")
    _set(render, "resolution_percentage", 100, applied, missing, "resolution_percentage")
    _set(render, "film_transparent", True, applied, missing, "film_transparent")
    eevee = getattr(scene, "eevee", None)
    # Version-dependent settings: each is tried; the report lists the ones this build lacks.
    # Motion blur lives on scene.render in 4.2+ and on scene.eevee before that.
    _set(render, "use_motion_blur", False, applied, missing, "render.use_motion_blur")
    _set(eevee, "use_motion_blur", False, applied, missing, "eevee.use_motion_blur")
    # Legacy EEVEE only (EEVEE Next uses virtual shadow maps and horizon scan; the AO node still works).
    _set(eevee, "shadow_cascade_size", "4096", applied, missing, "eevee.shadow_cascade_size")
    _set(eevee, "use_gtao", True, applied, missing, "eevee.use_gtao")
    image = render.image_settings
    _set(image, "file_format", "PNG", applied, missing, "file_format")
    _set(image, "color_mode", "RGBA", applied, missing, "color_mode")
    _set(image, "color_depth", "8", applied, missing, "color_depth")
    for layer in scene.view_layers:
        for attr in ("use_pass_z", "use_pass_cryptomatte_object", "use_pass_cryptomatte_material"):
            _set(layer, attr, True, applied, missing, f"{layer.name}.{attr}")


def _fcurves(anim_data):
    """F-curves of an AnimData block, legacy or layered (4.4+) actions."""
    if anim_data is None or anim_data.action is None:
        return []
    action = anim_data.action
    layers = getattr(action, "layers", None)
    if layers:
        curves = []
        for layer in layers:
            for strip in layer.strips:
                for bag in getattr(strip, "channelbags", []):
                    curves.extend(bag.fcurves)
        return curves
    return list(getattr(action, "fcurves", []))


def step_animation(objects, step, start, camera_owner, report):
    """Add a Stepped modifier (on ``step``s, aligned to ``start``) to animated objects."""
    stepped, smooth = [], []
    for obj in objects:
        is_camera = getattr(obj, "type", "") == "CAMERA"
        keep_smooth = (is_camera and camera_owner == "blender") or bool(obj.get("npr_smooth", False))
        blocks = [getattr(obj, "animation_data", None)]
        data = getattr(obj, "data", None)
        keys = getattr(data, "shape_keys", None) if data is not None else None
        if keys is not None:
            blocks.append(getattr(keys, "animation_data", None))
        curves = [c for block in blocks for c in _fcurves(block)]
        if not curves:
            continue
        if keep_smooth:
            smooth.append(obj.name)
            continue
        for curve in curves:
            if any(m.type == "STEPPED" for m in curve.modifiers):
                continue
            mod = curve.modifiers.new("STEPPED")
            mod.frame_step = float(step)
            mod.frame_offset = float(start)
        stepped.append(obj.name)
    report["stepped_objects"] = sorted(stepped)
    report["smooth_objects"] = sorted(smooth)


def _layer_collections(view_layer):
    """name -> (layer collection, ancestor names, descendant names)."""
    out = {}

    def walk(lc, ancestors):
        names = []
        for child in lc.children:
            descendants = walk(child, ancestors + [child.name])
            out[child.name] = (child, list(ancestors), descendants)
            names += [child.name] + descendants
        return names
    walk(view_layer.layer_collection, [])
    return out


def render_layers(bpy, scene, out, layers, report):
    """Render each element collection alone; every other collection is a holdout,
    so anything in front cuts the element's alpha and nothing else adds color."""
    view_layer = bpy.context.view_layer
    collections = _layer_collections(view_layer)
    missing = [name for name in layers if name not in collections]
    if missing:
        raise RuntimeError(f"collections not found in view layer {view_layer.name}: {missing}")
    loose = [obj.name for obj in scene.collection.objects if getattr(obj, "type", "") not in ("CAMERA", "LIGHT")]
    if loose:
        report.setdefault("warnings", []).append(
            f"objects directly in the scene collection cannot be held out and appear in every layer: {loose[:8]}")
    original = {name: (lc.exclude, lc.holdout) for name, (lc, _, _) in collections.items()}
    rendered = []
    try:
        for name in layers:
            _, ancestors, descendants = collections[name]
            visible = {name, *ancestors, *descendants}
            for other, (lc, _, _) in collections.items():
                lc.exclude = False
                lc.holdout = other not in visible
            scene.render.filepath = os.path.join(out, name, "####")
            bpy.ops.render.render(animation=True)
            rendered.append(name)
    finally:
        for name, (exclude, holdout) in original.items():
            collections[name][0].exclude = exclude
            collections[name][0].holdout = holdout
    report["rendered_layers"] = rendered


def main(argv=None):
    import bpy  # only available inside Blender

    argv = argv if argv is not None else (sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    parser = argparse.ArgumentParser(prog="blender_npr_setup")
    parser.add_argument("--out", required=True)
    parser.add_argument("--frames", required=True, help="start-end inclusive, shot-relative")
    parser.add_argument("--step", type=int, default=2)
    parser.add_argument("--layers", default="", help="comma-separated collection names; empty = whole scene")
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--camera", choices=("blender", "engine"), default="blender")
    parser.add_argument("--no-render", action="store_true")
    args = parser.parse_args(argv)

    scene = bpy.context.scene
    start, end = (int(v) for v in args.frames.split("-"))
    scene.frame_start, scene.frame_end = start, end
    applied, missing = {}, []
    report = {"blender": ".".join(map(str, bpy.app.version)), "file": bpy.data.filepath,
              "frames": [start, end], "step": args.step, "camera_owner": args.camera}
    apply_settings(scene, args.width, args.height, applied, missing)
    step_animation(scene.objects, args.step, start, args.camera, report)
    report.update(applied=applied, unavailable=missing)
    os.makedirs(args.out, exist_ok=True)
    if not args.no_render:
        layers = [name for name in args.layers.split(",") if name]
        if layers:
            render_layers(bpy, scene, args.out, layers, report)
        else:
            scene.render.filepath = os.path.join(args.out, "combined", "####")
            bpy.ops.render.render(animation=True)
            report["rendered_layers"] = ["combined"]
    report["note"] = ("Settings and stepping applied by script; shading, line art and identity are not "
                      "checked here. Run `python -m studio blender check` and `studio qa`.")
    with open(os.path.join(args.out, "blender_render.json"), "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
    print(json.dumps(report))


if __name__ == "__main__":
    main()
