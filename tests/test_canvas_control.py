"""Full-scene canvas editor tests; use rendered actual layers, not bell overlays."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from studio.canvas_control import CanvasSession, CanvasError


class FullCanvasControlTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.project = self.root / "projects" / "cemi_episode_01"
        self.spec_root = self.project / "data" / "shots"
        self.spec_root.mkdir(parents=True)
        assets = self.project / "assets"
        assets.mkdir()
        Image.new("RGBA", (160, 90), "#283b55").save(assets / "background.png")
        Image.new("RGBA", (30, 40), "#b87a51").save(assets / "character.png")
        Image.new("RGBA", (25, 15), "#e4b868").save(assets / "bell.png")
        self.spec = {
            "id": "S01-05", "size": [160, 90], "frames": 48, "fps": 24,
            "status": "candidate", "stage": "motion", "background": [14, 24, 31, 255],
            "layers": [
                {"name": "night", "source": "assets/background.png", "fit": "none",
                 "rate": 1, "tags": ["bg"], "parallax": 0.5},
                {"name": "amaia", "source": "assets/character.png", "fit": "none",
                 "rate": 2, "tags": ["character"], "keys": [{"frame": 0, "x": 45, "y": 20}]},
                {"name": "bell", "source": "assets/bell.png", "fit": "none",
                 "rate": 1, "tags": ["prop"], "keys": [{"frame": 0, "x": 103, "y": 8}]},
            ],
            "camera": [{"frame": 0, "x": 0, "y": 0, "scale": 1, "angle": 0}],
        }
        self.source = self.spec_root / "S01-05.json"
        self.source.write_text(json.dumps(self.spec))
        self.session = CanvasSession(project=self.project, repo=self.root)

    def test_128_shot_api_is_generic_and_path_bounded(self):
        self.assertEqual(self.session.shots(), ["S01-05"])
        with self.assertRaises(CanvasError):
            self.session.select("../../secrets")
        self.assertEqual(self.session.select("S01-05")["frames"], 48)
        self.assertEqual([x["name"] for x in self.session.state()["layers"]],
                         ["night", "amaia", "bell"])

    def test_whole_frame_camera_and_all_layer_transform_keying(self):
        self.session.select("S01-05")
        original = self.source.read_bytes()
        before, geom = self.session.preview(0)
        self.assertEqual(before[:8], bytes((137, 80, 78, 71, 13, 10, 26, 10)))
        self.assertEqual(len(geom), 3)
        self.assertEqual(len(next(x for x in geom if x["name"] == "bell")["translation_basis"]), 2)
        # Held character drawing on 2s: editing frame 13 targets frame 12.
        self.session.edit({"target": "layer", "layer": "amaia",
                           "frame": 13, "property": "y", "value": 24})
        self.assertTrue(any(k["frame"] == 12 for k in self.session.spec["layers"][1]["keys"]))
        self.assertFalse(any(k["frame"] == 13 for k in self.session.spec["layers"][1]["keys"]))
        self.session.edit({"target": "camera", "frame": 12, "property": "x", "value": 15})
        self.session.edit({"target": "layer", "layer": "night", "frame": 12,
                           "property": "parallax", "value": 0.8})
        self.session.edit({"target": "layer", "layer": "bell", "frame": 12,
                           "property": "y", "value": 18})
        self.session.edit({"target": "layer", "layer": "amaia", "frame": 12,
                           "property": "x", "value": 59})
        self.session.reorder("bell", -1)
        after, geo = self.session.preview(12)
        self.assertNotEqual(before, after)
        self.assertEqual(len(geo), 3)
        self.assertEqual(self.source.read_bytes(), original)
        shot = self.session.spec
        self.assertEqual([l["name"] for l in shot["layers"]], ["night", "bell", "amaia"])
        self.assertEqual(next(k["x"] for k in shot["camera"] if k["frame"] == 12), 15)
        self.assertEqual(next(k["x"] for k in shot["layers"][-1]["keys"] if k["frame"] == 12), 59)

    def test_character_distortion_block_and_fail_closed_edits(self):
        self.session.select("S01-05")
        for prop, val in (("scale", 1.1), ("angle", 9)):
            with self.assertRaisesRegex(CanvasError, "not acting"):
                self.session.edit({"target": "layer", "layer": "amaia",
                                   "frame": 10, "property": prop, "value": val})
        for data in [
            {"target": "layer", "layer": "bell", "frame": 50, "property": "x", "value": 8},
            {"target": "camera", "frame": 5, "property": "scale", "value": 0},
            {"target": "layer", "layer": "bell", "frame": 4, "property": "x", "value": float("nan")},
            {"target": "layer", "layer": "../../bad", "frame": 0, "property": "x", "value": 1},
        ]:
            with self.assertRaises(CanvasError):
                self.session.edit(data)
        with self.assertRaises(CanvasError):
            self.session.save()

    def test_episode_inventory_scans_all_shots_without_motion_claims(self):
        self.session.select("S01-05")
        inventory = self.session.inventory()
        self.assertEqual(inventory["shot_count"], 1)
        self.assertEqual(inventory["shots_without_character_action_evidence"], 1)
        self.assertEqual(inventory["shots_with_missing_files"], 0)
        self.assertEqual(inventory["shots"][0]["layers"], 3)
        self.assertEqual(inventory["shots"][0]["motion_evidence"], "not demonstrated")
        self.assertFalse(inventory["author_approved"])

    def test_painted_alpha_bounds_not_full_transparent_registration(self):
        cel = Image.new("RGBA", (30, 40), (0, 0, 0, 0))
        cel.paste((184, 120, 81, 255), (4, 5, 14, 20))
        cel.save(self.project / "assets" / "character.png")
        self.session.select("S01-05")
        _, geometry = self.session.preview(0)
        amaia = next(item for item in geometry if item["name"] == "amaia")
        self.assertEqual(amaia["painted_source_bounds"], [4, 5, 14, 20])
        self.assertTrue(amaia["alpha_registered"])
        self.assertLess(amaia["bounds"]["right"] - amaia["bounds"]["left"], 30 * .5)

    def test_all_shot_sampled_compositor_preflight_reports_rendered_frames(self):
        self.session.select("S01-05")
        started = self.session.start_episode_audit()
        self.assertEqual(started["total"], 1)
        self.session._audit_thread.join(timeout=15)
        report = self.session.episode_audit()
        self.assertEqual(report["state"], "completed")
        self.assertEqual(report["completed"], 1)
        self.assertEqual(report["render_failures"], 0, report["shots"])
        self.assertGreaterEqual(report["rendered_samples"], 3)
        self.assertEqual(report["shots"][0]["state"], "sampled_render_pass")
        self.assertFalse(report["author_approved"])

    def test_full_shot_video_is_frame_verified_and_cache_invalidates(self):
        from unittest.mock import patch

        written = []
        class FakeWriter:
            def __init__(self, out, size, mode, fps):
                self.path, self.size, self.mode, self.fps = Path(out), size, mode, fps
            def __enter__(self):
                return self
            def write(self, image):
                written.append((image.size, image.mode))
            def __exit__(self, *_):
                self.path.write_bytes(b"FAKE-MP4-FOR-TESTS")

        self.session.select("S01-05")
        with patch("studio.canvas_control.Writer", FakeWriter), patch(
            "studio.canvas_control.probe_frames", return_value=48
        ) as probe:
            meta = self.session.render_review()
            self.assertEqual(meta["frames"], 48)
            self.assertEqual(meta["decoded_frames"], 48)
            self.assertEqual(meta["fps"], 24)
            self.assertEqual(len(written), 48)
            self.assertTrue(all(mode == "RGB" for _, mode in written))
            self.assertEqual(self.session.video_bytes(), b"FAKE-MP4-FOR-TESTS")
            self.assertFalse(meta["author_approved"])
            self.session.render_review()
            self.assertEqual(len(written), 48, "same revision uses cached video")
            probe.assert_called_once()
        self.session.edit({"target": "camera", "frame": 10, "property": "x", "value": 5})
        with self.assertRaisesRegex(CanvasError, "stale or missing"):
            self.session.video_bytes()

    def test_video_review_rejects_truncated_decode(self):
        from unittest.mock import patch
        class FakeWriter:
            def __init__(self, out, size, mode, fps):
                self.out = Path(out)
            def __enter__(self):
                return self
            def write(self, image):
                pass
            def __exit__(self, *_):
                self.out.write_bytes(b"partial")
        self.session.select("S01-05")
        with patch("studio.canvas_control.Writer", FakeWriter), patch(
            "studio.canvas_control.probe_frames", return_value=47
        ):
            with self.assertRaisesRegex(CanvasError, "review incomplete"):
                self.session.render_review()
        with self.assertRaises(CanvasError):
            self.session.video_bytes()

    def test_new_take_contains_actual_full_canvas_spec_and_audit(self):
        self.session.select("S01-05")
        self.session.edit({"target": "camera", "frame": 24, "property": "scale", "value": 1.1})
        self.session.edit({"target": "layer", "layer": "bell", "frame": 24,
                           "property": "opacity", "value": .5})
        audit = self.session.audit(sample=12)
        self.assertGreaterEqual(len(audit["samples"]), 4)
        self.assertEqual(audit["status"], "technical_preflight_only")
        output = self.session.save()
        spec_path = Path(output["spec"])
        self.assertTrue(spec_path.is_file())
        draft = json.loads(spec_path.read_text())
        self.assertEqual(draft["status"], "exploratory")
        self.assertFalse(draft["author_approved"])
        self.assertEqual(len(draft["layers"]), 3)
        self.assertEqual(json.loads(self.source.read_text()), self.spec)
        self.assertTrue(Path(output["audit"]).is_file())


if __name__ == "__main__":
    unittest.main()
