"""Blender bridge tests without Blender: PNG-sequence checks/imports and the
in-Blender setup script exercised against a stub of the bpy objects it touches."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

from PIL import Image
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from studio import blender, blender_npr_setup as setup, qa  # noqa: E402


def _sequence(directory, changes, total=12):
    """Write total frames; the picture changes at each frame in ``changes``."""
    directory.mkdir(parents=True, exist_ok=True)
    shade = 0
    for i in range(total):
        if i in changes:
            shade += 40
        Image.new("RGBA", (16, 16), (shade % 256, 80, 120, 255)).save(directory / f"{i:04d}.png")
    return directory


class SequenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)

    def test_check_accepts_stepped_and_flags_ones(self):
        stepped = _sequence(self.tmp / "stepped", {2, 4, 6, 8, 10})
        self.assertTrue(blender.check(stepped, 2)["ok"])
        ones = _sequence(self.tmp / "ones", set(range(1, 12)))
        report = blender.check(ones, 2, start=100)
        self.assertFalse(report["ok"])
        self.assertEqual(report["off_grid_changes"][0], 101)

    def test_import_collapses_holds(self):
        seq = _sequence(self.tmp / "beheto", {4, 8})
        layer = blender.import_sequence(seq, name="beheto", rate=2, tags=["character"], start=24)
        self.assertEqual([(e["start"], e["end"]) for e in layer["exposures"]], [(0, 4), (4, 8), (8, 12)])
        self.assertEqual((layer["rate"], layer["drawing_rate"], layer["in"], layer["out"]), (1, 2, 24, 36))
        self.assertTrue(layer["screen_space"])

    def test_qa_flags_off_grid_layers(self):
        seq = _sequence(self.tmp / "hull", {3, 6})
        layer = blender.import_sequence(seq, name="hull", rate=2)
        spec = {"id": "B-01", "size": [16, 16], "frames": 12, "layers": [layer]}
        self.assertEqual(qa.step_flags(spec)[0]["type"], "off_grid")

    def test_render_reports_missing_blender_file(self):
        with self.assertRaises(blender.BlenderError):
            blender.render(self.tmp / "none.blend", self.tmp / "out", frames="0-10")


# ---------------------------------------------------------------- stub bpy

class Obj:
    def __init__(self, **attrs):
        self.__dict__.update(attrs)


class Modifiers(list):
    def new(self, kind):
        mod = Obj(type=kind, frame_step=0.0, frame_offset=0.0)
        self.append(mod)
        return mod


class Render(Obj):
    ENGINES = {"BLENDER_EEVEE"}  # pretend this build only knows the newer identifier

    def __setattr__(self, name, value):
        if name == "engine" and value not in self.ENGINES:
            raise TypeError(f"enum {value} not found")
        object.__setattr__(self, name, value)


class Thing(dict):
    """Blender ID stand-in: attributes plus custom properties via .get()."""

    def __init__(self, name, kind="MESH", curves=(), layered=False, props=None):
        super().__init__(props or {})
        self.name, self.type = name, kind
        curves = [Obj(modifiers=Modifiers()) for _ in range(curves)] if isinstance(curves, int) else []
        if layered:
            action = Obj(layers=[Obj(strips=[Obj(channelbags=[Obj(fcurves=curves)])])])
        else:
            action = Obj(layers=[], fcurves=curves)
        self.animation_data = Obj(action=action) if curves else None
        self.data = Obj(shape_keys=None)
        self.curves = curves


class SetupScriptTests(unittest.TestCase):
    def scene(self):
        render = Render(fps=30, fps_base=1.001, resolution_x=1920, resolution_y=1080, resolution_percentage=50,
                        film_transparent=False, use_motion_blur=True,
                        image_settings=Obj(file_format="OPEN_EXR", color_mode="RGB", color_depth="16"))
        layer = Obj(name="ViewLayer", use_pass_z=False, use_pass_cryptomatte_object=False,
                    use_pass_cryptomatte_material=False)
        return Obj(render=render, view_settings=Obj(view_transform="AgX", look="Punchy"),
                   eevee=Obj(use_motion_blur=True), view_layers=[layer])

    def test_apply_settings_with_version_guards(self):
        scene = self.scene()
        applied, missing = {}, []
        setup.apply_settings(scene, 1280, 720, applied, missing)
        r = scene.render
        self.assertEqual(applied["engine"], "BLENDER_EEVEE")
        self.assertEqual((r.fps, r.fps_base, r.resolution_x, r.resolution_y), (24, 1.0, 1280, 720))
        self.assertFalse(r.use_motion_blur)
        self.assertFalse(scene.eevee.use_motion_blur)
        self.assertTrue(r.film_transparent)
        self.assertEqual(scene.view_settings.view_transform, "Standard")
        self.assertEqual(r.image_settings.color_mode, "RGBA")
        self.assertTrue(scene.view_layers[0].use_pass_cryptomatte_material)
        self.assertTrue(any("shadow_cascade_size" in m for m in missing))  # EEVEE Next has no cascade setting

    def test_step_animation_respects_camera_and_smooth_flag(self):
        objects = [Thing("hull", curves=2), Thing("beheto", curves=3, layered=True),
                   Thing("Camera", kind="CAMERA", curves=1), Thing("river", curves=1, props={"npr_smooth": True}),
                   Thing("rock")]
        report = {}
        setup.step_animation(objects, 3, 24, "blender", report)
        self.assertEqual(report["stepped_objects"], ["beheto", "hull"])
        self.assertEqual(report["smooth_objects"], ["Camera", "river"])
        mod = objects[1].curves[0].modifiers[0]
        self.assertEqual((mod.type, mod.frame_step, mod.frame_offset), ("STEPPED", 3.0, 24.0))
        setup.step_animation(objects, 3, 24, "blender", {})  # idempotent: no second modifier
        self.assertEqual(len(objects[0].curves[0].modifiers), 1)
        engine_cam = {}
        setup.step_animation([Thing("Cam2", kind="CAMERA", curves=1)], 2, 0, "engine", engine_cam)
        self.assertEqual(engine_cam["stepped_objects"], ["Cam2"])

    def test_render_layers_holds_out_everything_else(self):
        def lc(name, children=()):
            return Obj(name=name, exclude=False, holdout=False, children=list(children))
        beheto, drum, river = lc("beheto"), lc("drum"), lc("river")
        chars = lc("characters", [beheto])
        root = Obj(children=[chars, drum, river])
        seen = []

        class Ops:
            class render:  # noqa: N801 - mirrors bpy.ops.render
                @staticmethod
                def render(animation):
                    seen.append({c.name: c.holdout for c in (chars, beheto, drum, river)})

        scene = Obj(render=Obj(filepath=""), collection=Obj(objects=[]))
        bpy = Obj(context=Obj(view_layer=Obj(name="ViewLayer", layer_collection=root)), ops=Ops)
        report = {}
        setup.render_layers(bpy, scene, "/tmp/out", ["beheto", "drum"], report)
        self.assertEqual(seen[0], {"characters": False, "beheto": False, "drum": True, "river": True})
        self.assertEqual(seen[1], {"characters": True, "beheto": True, "drum": False, "river": True})
        self.assertFalse(any(c.holdout for c in (chars, beheto, drum, river)))  # restored
        self.assertEqual(report["rendered_layers"], ["beheto", "drum"])


class WiringTests(unittest.TestCase):
    def test_skill_and_roles_wired(self):
        skill = ROOT / ".agents/skills/blender-npr-3d-anime/SKILL.md"
        self.assertTrue(skill.is_file())
        self.assertIn("name: blender-npr-3d-anime", skill.read_text())
        roles = json.loads((ROOT / "production/roles.json").read_text())
        for role in ("cg-director", "compositor", "effects-animator"):
            self.assertIn(".agents/skills/blender-npr-3d-anime/SKILL.md", roles[role]["extra_skills"])
            self.assertIn("blender-npr-3d-anime", (ROOT / roles[role]["skill"]).read_text())


if __name__ == "__main__":
    unittest.main()


class ScanTests(unittest.TestCase):
    def test_scan_rebuilds_fills_and_ink(self):
        from PIL import ImageDraw
        from studio import scan
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp)
        img = Image.new("RGBA", (200, 150), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.ellipse([20, 20, 120, 120], fill=(210, 150, 90, 255), outline=(20, 15, 10, 255), width=4)
        d.rectangle([90, 40, 180, 130], fill=(60, 80, 140, 255), outline=(20, 15, 10, 255), width=3)
        img.save(tmp / "cel.png")
        result = scan.scan_file(tmp / "cel.png", tmp / "cel.scan.json", preview=tmp / "prev.png", colors=4)
        self.assertGreaterEqual(result["stats"]["fills"], 2)
        self.assertGreater(result["stats"]["strokes"], 0)
        self.assertGreater(result["fidelity"]["coverage_iou"], 0.97)
        self.assertLess(result["fidelity"]["mean_color_error"], 30)
        roles = {p["role"] for p in result["palette"]}
        self.assertEqual(roles, {"fill", "ink"})
        self.assertTrue(all(len(pt) == 3 for s in result["strokes"] for pt in s["points"]))  # x, y, radius

    def test_thin_gives_one_pixel_lines(self):
        from studio import scan
        mask = np.zeros((20, 40), np.uint8)
        mask[8:13, 5:35] = 1
        skeleton = scan.thin(mask)
        self.assertLessEqual(skeleton[:, 20].sum(), 1)
        self.assertEqual(len(scan.trace_skeleton(skeleton)), 1)
