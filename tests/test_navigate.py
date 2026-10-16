import tempfile
import unittest
from pathlib import Path

from studio.navigate import inspect_file, render_html
from studio.paths import sha256


class NavigatorTests(unittest.TestCase):
    def test_restored_media_cannot_inherit_old_hash_approval(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            media = root / "shot.mp4"
            media.write_bytes(b"original")
            expected = sha256(media)
            media.write_bytes(b"restored different render")
            self.assertEqual("hash_mismatch", inspect_file(root, "shot.mp4", expected)["state"])
            self.assertEqual("missing", inspect_file(root, "absent.mp4")["state"])
            self.assertEqual("outside_repository", inspect_file(root, "../outside.mp4")["state"])
            media.write_text("version https://git-lfs.github.com/spec/v1\noid sha256:abc\n")
            self.assertEqual("lfs_pointer", inspect_file(root, "shot.mp4")["state"])

    def test_script_is_escaped_in_navigator(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            item = {"path": None, "state": "unassigned"}
            row = {"shot": "S01-01", "frames": 24, "start_frame": 0,
                   "recorded_status": "draft", "spec": "missing.json",
                   "script": "<script>alert(1)</script>", "remaining_actions": [],
                   "missing_drawings": [], "voice_status": "not_recorded",
                   **{key: item for key in ("artwork", "motion", "native", "review")}}
            report = {key: {} for key in ("format", "motion_counts", "artwork_counts", "automation")}
            report.update(shots=[row], shot_count=1, frames=24)
            html = render_html(report, root, root)
            self.assertNotIn("<script>alert(1)</script>", html)
            self.assertIn("&lt;script&gt;", html)
