"""ChatGPT cloud handoff tests: source binding, imports, refusal, and rig geometry."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from studio import cloud
from studio.cloud_rig import validate_action


class CloudTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        for path, data in {
            cloud.EPISODE: {
                "fps": 24, "width": 1280, "height": 720,
                "shots": [
                    {"id": "S01-05", "start_frame": 792, "frames": 168,
                     "script": "- **Action:** Soldier raises bell and strikes it.",
                     "keyframes": ["assets/keyframes/S01-05A.png"]},
                    {"id": "S01-06", "start_frame": 960, "frames": 240,
                     "script": "- **Action:** Children reach into the blue.",
                     "keyframes": []},
                ]},
            cloud.SHOT_INDEX: {"shots": [
                {"shot": "S01-05", "path": "art/bell.png", "sha256": "f" * 64,
                 "dimensions": [1672, 941], "selected_moment": "bell close-up"},
            ]},
            cloud.ART_DIRECTION: {},
            cloud.AUTHOR_DECISIONS: {},
        }.items():
            dest = self.root / path
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(json.dumps(data))
        self.addCleanup(self.tmp.cleanup)

    def test_packet_uses_real_episode_numbers_not_guesses(self):
        p = cloud.plan("S01", self.root)
        self.assertEqual((p["shot_count"], p["frames"], p["seconds"]), (2, 408, 17))
        self.assertEqual(p["shots"][0]["start_frame"], 792)
        self.assertIn("Soldier raises bell", p["shots"][0]["required_action"])
        self.assertEqual(p["shots"][0]["reference"]["source_hash_matches"], False)
        self.assertEqual(p["shots"][0]["reference"]["state"], "exploratory-reference-not-animation")
        self.assertFalse(p["final_eligible"])

    def test_prepare_is_idempotent_and_detects_source_changes(self):
        cloud.prepare("S01", self.root)
        self.assertTrue(cloud.prepare("S01", self.root)["unchanged"])
        self.assertEqual(cloud.status("S01", self.root)["received"], 0)
        path = self.root / cloud.ART_DIRECTION
        path.write_text('{"changed":true}')
        with self.assertRaisesRegex(cloud.CloudError, "differs"):
            cloud.prepare("S01", self.root)
        self.assertFalse(cloud.prepare("S01", self.root, refresh=True)["unchanged"])

    def test_ingest_rejects_wrong_fps_and_never_promotes(self):
        cloud.prepare("S01", self.root)
        clip = self.root / "clip.mp4"
        clip.write_bytes(b"synthetic-test-clip")
        with patch.object(cloud, "_media_probe", return_value={
            "fps": "25", "frames": 168, "size": [1280, 720], "has_audio": False,
        }):
            with self.assertRaisesRegex(cloud.CloudError, "Frame-exact"):
                cloud.ingest("S01", "S01-05", clip, self.root)
        with patch.object(cloud, "_media_probe", return_value={
            "fps": "24", "frames": 168, "size": [1280, 720], "has_audio": False,
        }):
            receipt = cloud.ingest("S01", "S01-05", clip, self.root)
            again = cloud.ingest("S01", "S01-05", clip, self.root)
        self.assertEqual(receipt["sha256"], again["sha256"])
        self.assertFalse(receipt["author_approved"])
        self.assertFalse(receipt["final_eligible"])
        self.assertEqual(cloud.status("S01", self.root)["received"], 1)
        with self.assertRaisesRegex(cloud.CloudError, "incomplete scene"):
            cloud.assemble_draft("S01", self.root / "out.mp4", self.root)

    def test_ingest_rejects_changed_clip_revision(self):
        cloud.prepare("S01-05", self.root)
        clip = self.root / "clip.mp4"
        clip.write_bytes(b"clip-one")
        with patch.object(cloud, "_media_probe", return_value={
            "fps": "24", "frames": 168, "size": [1280, 720], "has_audio": False,
        }):
            cloud.ingest("S01-05", "S01-05", clip, self.root)
            clip.write_bytes(b"clip-two")
            with self.assertRaisesRegex(cloud.CloudError, "different submission"):
                cloud.ingest("S01-05", "S01-05", clip, self.root)

    def test_full_bell_reference_has_exact_frame_mechanics(self):
        from production.cloud.examples.bell_blockout import build
        evidence, review = build()
        self.assertEqual(len(evidence["poses"]), 168)
        self.assertEqual(review["measured_count"], 168)
        self.assertTrue(review["mechanics_verified"], review["errors"])
        self.assertFalse(review["art_and_acting_approved"])

    def test_scene_names_reject_traversal(self):
        with self.assertRaises(cloud.CloudError):
            cloud.plan("../../etc", self.root)

    def test_bell_sparse_poses_cannot_claim_complete_mechanics(self):
        def pose(frame, impact=False):
            return {
                "frame": frame,
                "pole": {"a": [0, 0], "b": [100, 0]},
                "hands": {
                    "left": {"point": [25, 0], "grip_t": .25},
                    "right": {"point": [75, 0], "grip_t": .75}},
                "arms": {
                    "left": {"shoulder": [25, -80], "elbow": [25, -40], "wrist": [25, 0]},
                    "right": {"shoulder": [75, -80], "elbow": [75, -40], "wrist": [75, 0]}},
                "bell": {"pivot": [100, 0], "clapper_anchor": [100, 20],
                         "rim": [[90, 45], [110, 45]]},
                "clapper": {"hinge": [100, 20], "tip": [110, 45] if impact else [100, 39]},
            }
        spec = {"shot": "S01-05", "fps": 24, "frames": 168,
                "impact_frames": [167], "poses": [pose(0), pose(167, impact=True)]}
        result = validate_action(spec)
        self.assertTrue(result["ok"], result["errors"])
        self.assertFalse(result["mechanics_verified"])
        self.assertFalse(result["complete_frame_coverage"])
        spec["poses"][1]["hands"]["left"]["point"] = [35, 0]
        self.assertFalse(validate_action(spec)["ok"])


if __name__ == "__main__":
    unittest.main()
