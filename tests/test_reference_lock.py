"""Reference-lock manifests and script generation do not require Blender."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from studio import reference_lock  # noqa: E402


class ReferenceLockTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.source = self.tmp / "storefront.png"
        Image.new("RGB", (32, 18), (20, 40, 60)).save(self.source)
        self.out = self.tmp / "reference"
        reference_lock.init(self.source, self.out)
        self.manifest_path = self.out / "manifest.json"

    def read_manifest(self):
        return json.loads(self.manifest_path.read_text(encoding="utf-8"))

    def write_manifest(self, manifest):
        self.manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    def test_valid_manifest(self):
        report = reference_lock.validate(self.manifest_path)
        self.assertTrue(report["valid"])
        self.assertEqual(report["workflow"], "camera_locked")
        self.assertEqual(report["layers"], 1)

    def test_changed_source_sha_is_rejected(self):
        source = self.out / self.read_manifest()["source"]["path"]
        source.write_bytes(source.read_bytes() + b"changed")
        with self.assertRaisesRegex(reference_lock.ReferenceLockError, "SHA-256 mismatch"):
            reference_lock.validate(self.manifest_path)

    def test_wrong_source_dimensions_are_rejected(self):
        manifest = self.read_manifest()
        manifest["source"]["width"] = 31
        self.write_manifest(manifest)
        with self.assertRaisesRegex(reference_lock.ReferenceLockError, "dimensions"):
            reference_lock.validate(self.manifest_path)

    def test_duplicate_layer_id_is_rejected(self):
        manifest = self.read_manifest()
        duplicate = dict(manifest["layers"][0], depth=1.0)
        manifest["layers"].append(duplicate)
        manifest["workflow"] = "2.5d"
        manifest["camera"] = {"mode": "perspective", "locked": False}
        duplicate["id"] = manifest["layers"][0]["id"]
        self.write_manifest(manifest)
        with self.assertRaisesRegex(reference_lock.ReferenceLockError, "duplicate layer id"):
            reference_lock.validate(self.manifest_path)

    def test_invalid_layer_mode_is_rejected(self):
        manifest = self.read_manifest()
        manifest["layers"][0]["mode"] = "generated_geometry"
        self.write_manifest(manifest)
        with self.assertRaisesRegex(reference_lock.ReferenceLockError, "invalid layer mode"):
            reference_lock.validate(self.manifest_path)

    def test_default_manifest_is_one_approved_backplate(self):
        manifest = self.read_manifest()
        layer = manifest["layers"][0]
        self.assertEqual(manifest["workflow"], "camera_locked")
        self.assertEqual(manifest["camera"], {"mode": "orthographic", "locked": True})
        self.assertEqual(len(manifest["layers"]), 1)
        self.assertEqual((layer["mode"], layer["parallax"], layer["approved"]),
                         ("backplate", 0.0, True))
        self.assertEqual((manifest["source"]["width"], manifest["source"]["height"]), (32, 18))
        self.assertEqual(manifest["source"]["provenance"]["method"], "copied")

    def test_blender_script_has_engine_fallback_and_locked_camera(self):
        script_path = self.out / "build_scene.py"
        reference_lock.blender_script(self.manifest_path, script_path)
        script = script_path.read_text(encoding="utf-8")
        self.assertIn('("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE")', script)
        self.assertIn("camera.lock_location = (True, True, True)", script)
        self.assertIn("camera.lock_rotation = (True, True, True)", script)
        self.assertIn("bpy.ops.wm.save_as_mainfile", script)

    def test_mask_dimensions_are_verified(self):
        manifest = self.read_manifest()
        mask = self.out / "assets" / "mask.png"
        Image.new("L", (32, 18), 255).save(mask)
        layer = manifest["layers"][0]
        layer["mask"] = mask.relative_to(self.out).as_posix()
        layer["mask_sha256"] = hashlib.sha256(mask.read_bytes()).hexdigest()
        self.write_manifest(manifest)
        self.assertTrue(reference_lock.validate(self.manifest_path)["valid"])
        Image.new("L", (16, 9), 255).save(mask)
        layer["mask_sha256"] = hashlib.sha256(mask.read_bytes()).hexdigest()
        self.write_manifest(manifest)
        with self.assertRaisesRegex(reference_lock.ReferenceLockError, "mask dimensions"):
            reference_lock.validate(self.manifest_path)

    def test_depth_order_is_checked_for_explicit_parallax_layers(self):
        manifest = self.read_manifest()
        manifest["workflow"] = "2.5d"
        manifest["camera"] = {"mode": "perspective", "locked": False}
        front = dict(manifest["layers"][0], id="front", depth=-1.0, parallax=1.0, mode="card")
        manifest["layers"].append(front)
        self.write_manifest(manifest)
        with self.assertRaisesRegex(reference_lock.ReferenceLockError, "ordered back-to-front"):
            reference_lock.validate(self.manifest_path)


if __name__ == "__main__":
    unittest.main()
