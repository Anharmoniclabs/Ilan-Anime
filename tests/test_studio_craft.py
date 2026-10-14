import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image
from studio import craft


class CraftTests(unittest.TestCase):
    def test_nested_engine_errors(self):
        self.assertTrue(craft.failed({"results": [{"ok": False, "error": "bad layer"}]}))
        self.assertTrue(craft.failed({"errors": ["missing media"]}))
        self.assertFalse(craft.failed({"ok": True, "error": None, "errors": []}))

    def test_existing_output_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            marker = Path(tmp) / "keep.txt"
            marker.write_text("original")
            with self.assertRaises(ValueError):
                craft.new_output(tmp)
            self.assertEqual(marker.read_text(), "original")

    def test_invalid_exposures_fail_before_engine_start(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "exposures.json"
            p.write_text(json.dumps({"width": 320, "height": 180, "fps": 24,
                                    "exposures": [{"path": "missing.png", "frames": 0}]}))
            with self.assertRaisesRegex(ValueError, "positive integer"):
                craft.render_cels(p, Path(tmp) / "render")
            self.assertFalse((Path(tmp) / "render").exists())

    def test_recipe_failure_stops_following_calls(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "recipe.json"
            p.write_text(json.dumps({"steps": [{"app": "photocraft", "tool": "doc_new"}] * 3}))
            with patch.object(craft, "Session") as session:
                call = session.return_value.__enter__.return_value.call
                call.side_effect = [{"ok": True}, ValueError("engine error")]
                with self.assertRaisesRegex(ValueError, "engine error"):
                    craft.run_recipe(p, Path(tmp) / "out")
                self.assertEqual(call.call_count, 2)
                status = json.loads((Path(tmp) / "out/status.json").read_text())
                self.assertEqual(status["completed_steps"], 1)
                self.assertEqual(status["status"], "stopped")

    @unittest.skipUnless(os.environ.get("ILAN_CRAFT_INTEGRATION") == "1", "live engines opt-in")
    def test_real_cels_hold_alpha_native_projects_and_timeline(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            Image.new("RGBA", (320, 180), (200, 40, 0, 128)).save(root / "cel-0001.png")
            Image.new("RGBA", (320, 180), (0, 120, 230, 255)).save(root / "cel-0002.png")
            Image.new("RGB", (320, 180), (20, 40, 60)).save(root / "background.png")
            spec = {"width": 320, "height": 180, "fps": 24, "background": "background.png",
                    "exposures": [{"path": "cel-0001.png", "frames": 3},
                                  {"path": "cel-0002.png", "frames": 2}]}
            (root / "manifest.json").write_text(json.dumps(spec))
            out = root / "take"
            result = craft.render_cels(root / "manifest.json", out)
            self.assertEqual(result["status"], "succeeded")
            pixels = []
            for p in sorted((out / "frames").glob("*.png")):
                with Image.open(p) as im:
                    pixels.append(im.convert("RGB").getpixel((10, 10)))
            self.assertEqual(pixels[:3], [pixels[0]] * 3)
            self.assertEqual(pixels[3:], [(0, 120, 230)] * 2)
            self.assertTrue(all(abs(a-b) <= 1 for a,b in zip(pixels[0], (110, 40, 30))))
            with craft.Session("effectcraft", root, root / "reopen-ec") as session:
                project = session.call("open_project", {"path": str(out / "shot.ecproj")})
                self.assertTrue(project["items"])
            with craft.Session("filmcraft", root, root / "reopen-fc") as session:
                session.call("command_run", {"id": "file.open", "params": {"path": str(out / "edit.filmcraft")}})
                timeline = session.call("sequence_inspect", {})
                self.assertEqual(timeline["durationFrames"], 5)


if __name__ == "__main__":
    unittest.main()
