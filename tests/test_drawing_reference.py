import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from studio.paths import ROOT

try:
    import cv2  # noqa: F401
except ImportError:  # pragma: no cover
    cv2 = None


def _fixture(path):
    """Synthetic cel: textured brown blade with a dark outline on transparency."""
    img = Image.new("RGBA", (160, 120), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((20, 20, 140, 100), fill=(90, 60, 40, 255), outline=(20, 15, 15, 255), width=3)
    arr = np.asarray(img).copy()
    rng = np.random.default_rng(0)
    grain = rng.integers(-12, 12, arr.shape[:2])
    inside = arr[..., 3] > 0
    arr[..., :3][inside] = np.clip(arr[..., :3][inside].astype(int) + grain[inside, None], 0, 255)
    Image.fromarray(arr.astype(np.uint8), "RGBA").save(path)


@unittest.skipIf(cv2 is None, "OpenCV not installed")
class ReferenceExtractTest(unittest.TestCase):
    def test_extract_round_trip_layers_and_metrics(self):
        from studio.drawing import reference
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "cel.png"
            _fixture(src)
            report = reference.extract(src, Path(tmp) / "out", colors=4)
            self.assertEqual(report["kind"], "reconstruction")
            self.assertEqual(report["size"], [160, 120])
            for name in reference.LAYERS:
                self.assertTrue((ROOT / report["layers"][name]["path"]).is_file()
                                or Path(report["layers"][name]["path"]).is_file())
            lay, vec = report["metrics"]["layered"], report["metrics"]["vector_only"]
            self.assertEqual(lay["alpha_iou"], 1.0)  # matte is the source alpha by construction
            self.assertLessEqual(lay["mean_color_error"], vec["mean_color_error"])
            self.assertLess(lay["mean_color_error"], 6)
            self.assertGreater(vec["alpha_iou"], 0.9)

    def test_svg_is_well_formed_and_records_source(self):
        from studio import scan
        from studio.drawing import reference
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "cel.png"
            _fixture(src)
            data = scan.scan_image(src, colors=4)
            svg = reference.to_svg(data)
            root = ET.fromstring(svg)
            self.assertEqual(root.get("width"), "160")
            self.assertIn(data["source_sha256"], svg)
            ids = {g.get("id") for g in root}
            self.assertTrue({"flats", "ink"} <= ids)

    def test_recolored_flats_keep_shade_texture(self):
        from studio import scan
        from studio.drawing import reference
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "cel.png"
            _fixture(src)
            layers = reference.build_layers(scan.scan_image(src, colors=4), src)
            flats = np.asarray(layers["flats"]).copy()
            flats[..., :3][flats[..., 3] > 0] = (40, 70, 120)  # recolor every fill
            layers["flats"] = Image.fromarray(flats, "RGBA")
            out = np.asarray(reference.composite(layers), dtype=np.float32)
            inside = np.asarray(Image.open(src))[..., 3] > 0
            self.assertGreater(out[..., 2][inside].mean(), out[..., 0][inside].mean())  # now blue
            self.assertGreater(out[..., 2][inside].std(), 2.0)  # grain survived the recolor


@unittest.skipIf(cv2 is None, "OpenCV not installed")
class PlausibilityGateTest(unittest.TestCase):
    def test_one_brown_square_benchmark_fails(self):
        from studio.drawing.review import plausibility
        img = Image.new("RGB", (1280, 720), (254, 254, 254))
        ImageDraw.Draw(img).rectangle((46, 46, 105, 104), fill=(63, 30, 13), outline=(23, 32, 43))
        result = plausibility(img)
        self.assertFalse(result["passed"])

    def test_recorded_draw_take_002_preview_fails(self):
        from studio.drawing.review import gate_file
        preview = ROOT / "production/artist-takes/DRAW-take-002/preview.png"
        if not preview.is_file():
            self.skipTest("local DRAW-take-002 evidence not present")
        self.assertFalse(gate_file(preview)["passed"])

    def test_approved_paddle_cel_passes_structural_gate(self):
        from studio.drawing.review import plausibility
        sheet = ROOT / "episode-01/assets/cels/paddle-sheet.png"
        if not sheet.is_file():
            self.skipTest("approved paddle sheet not present")
        img = Image.open(sheet).convert("RGBA")
        cel = img.crop((0, 0, img.width // 4, img.height // 2))
        # cel is a single prop, so judge it on occupancy + color richness, not region count
        self.assertTrue(plausibility(cel)["passed"], plausibility(cel))


if __name__ == "__main__":
    unittest.main()
