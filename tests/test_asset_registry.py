"""Tests for immutable art-asset history and final-use approval gates."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from production.asset_registry import AssetRegistry, AssetRegistryError


AT = "2026-10-12T16:00:00Z"


class AssetRegistryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name).resolve()
        (self.repo / "art").mkdir()
        (self.repo / "art/pose-v1.png").write_bytes(b"stable synthetic drawing v1")
        (self.repo / "art/pose-v2.png").write_bytes(b"stable synthetic drawing v2")
        self.registry = AssetRegistry(self.repo)

    @staticmethod
    def continuity():
        return {"character_ids": ["beheto"], "costume_ids": ["river-v1"],
                "prop_ids": ["drum-v1", "canoe-v1"], "time": "moonless night",
                "location": "lead canoe"}

    @staticmethod
    def provenance(sources=None):
        return {"origin": "replacement drawing pass", "creator": "test-artist",
                "license": "project-owned", "source_assets": sources or [],
                "notes": "Synthetic test fixture, not production artwork."}

    def register(self, **changes):
        values = {"asset_id": "s01-11.beheto-contact", "path": "art/pose-v1.png",
                  "kind": "replacement-cel", "mode": "work-in-progress",
                  "shots": ["S01-11"], "provenance": self.provenance(),
                  "continuity": self.continuity(), "at": AT}
        values.update(changes)
        return self.registry.register(**values)

    @staticmethod
    def approval(kind, approval_id=None, version=1, digest=None, approver_id=None):
        digest = digest or hashlib.sha256(b"stable synthetic drawing v1").hexdigest()
        return {"approval_id": approval_id or f"{kind}-s01-11-v{version}", "type": kind,
                "asset_id": "s01-11.beheto-contact", "version": version,
                "asset_sha256": digest,
                "approver_id": approver_id or ("technical-reviewer" if kind == "technical" else "luis-m-minier"),
                "approver_role": "animation-supervisor" if kind == "technical" else "author",
                "evidence": "Frame-stepped contact, identity, geometry, and art direction.", "at": AT}

    def approve_canonical(self):
        self.registry.transition("s01-11.beheto-contact", 1, "submitted", at=AT)
        self.registry.transition("s01-11.beheto-contact", 1, "technical-approved",
                                 self.approval("technical"), AT)
        self.registry.transition("s01-11.beheto-contact", 1, "author-approved",
                                 self.approval("author"), AT)
        self.registry.transition("s01-11.beheto-contact", 1, "canonical", at=AT)

    def test_register_hash_version_and_persistence(self):
        first = self.register()
        self.assertEqual(1, first["version"])
        self.assertEqual(hashlib.sha256(b"stable synthetic drawing v1").hexdigest(), first["sha256"])
        second = self.register(path="art/pose-v2.png", supersedes={"asset_id": first["asset_id"], "version": 1})
        self.assertEqual(2, second["version"])
        fresh = AssetRegistry(self.repo)
        self.assertEqual([1, 2], [a["version"] for a in fresh.summary()["assets"]])
        self.assertEqual(2, fresh.summary()["event_count"])

    def test_file_hash_verification_detects_changed_art(self):
        self.register()
        self.registry.verify(check_files=True)
        (self.repo / "art/pose-v1.png").write_bytes(b"changed after registration")
        with self.assertRaisesRegex(AssetRegistryError, "hash mismatch"):
            self.registry.verify(check_files=True)

    def test_symlink_cannot_be_registered_or_substituted_after_registration(self):
        target = self.repo / "art/pose-v2.png"
        link = self.repo / "art/linked.png"
        link.symlink_to(target)
        with self.assertRaisesRegex(AssetRegistryError, "symlink"):
            self.register(path="art/linked.png")
        self.register()
        original = self.repo / "art/pose-v1.png"
        original.unlink()
        original.symlink_to(target)
        self.registry.transition("s01-11.beheto-contact", 1, "submitted", at=AT)
        with self.assertRaisesRegex(AssetRegistryError, "unsafe"):
            self.registry.transition("s01-11.beheto-contact", 1, "technical-approved",
                                     self.approval("technical"), AT)

    def test_event_tampering_breaks_chain(self):
        self.register()
        data = json.loads(self.registry.path.read_text())
        data["events"][0]["payload"]["continuity"]["location"] = "different canoe"
        self.registry.path.write_text(json.dumps(data))
        with self.assertRaisesRegex(AssetRegistryError, "hash chain"):
            AssetRegistry(self.repo)

    def test_failed_event_rolls_back_in_memory_and_on_disk(self):
        self.register()
        before = copy.deepcopy(self.registry.data)
        with self.assertRaisesRegex(AssetRegistryError, "canonical"):
            self.registry.link_final("edit-main", "s01-11.beheto-contact", 1, ["S01-11"], AT)
        self.assertEqual(before, self.registry.data)
        self.assertEqual(before, json.loads(self.registry.path.read_text()))

    def test_technical_and_author_approvals_are_distinct(self):
        self.register(initial_state="submitted")
        with self.assertRaisesRegex(AssetRegistryError, "technical"):
            self.registry.transition("s01-11.beheto-contact", 1, "technical-approved",
                                     self.approval("author"), AT)
        self.registry.transition("s01-11.beheto-contact", 1, "technical-approved",
                                 self.approval("technical"), AT)
        with self.assertRaisesRegex(AssetRegistryError, "author"):
            self.registry.transition("s01-11.beheto-contact", 1, "author-approved",
                                     self.approval("technical", "tech-second"), AT)
        self.registry.transition("s01-11.beheto-contact", 1, "author-approved",
                                 self.approval("author"), AT)
        self.assertEqual("author-approved", self.registry.summary()["assets"][0]["state"])

    def test_technical_creator_cannot_approve_own_asset(self):
        self.register(initial_state="submitted")
        approval = self.approval("technical", approver_id="test-artist")
        with self.assertRaisesRegex(AssetRegistryError, "differ from the asset creator"):
            self.registry.transition("s01-11.beheto-contact", 1, "technical-approved", approval, AT)

    def test_author_approval_requires_luis_identity(self):
        self.register(initial_state="submitted")
        self.registry.transition("s01-11.beheto-contact", 1, "technical-approved",
                                 self.approval("technical"), AT)
        approval = self.approval("author", approver_id="not-luis")
        with self.assertRaisesRegex(AssetRegistryError, "luis-m-minier"):
            self.registry.transition("s01-11.beheto-contact", 1, "author-approved", approval, AT)

    def test_approval_digest_must_match_exact_registered_file(self):
        self.register(initial_state="submitted")
        wrong = self.approval("technical", digest="0" * 64)
        with self.assertRaisesRegex(AssetRegistryError, "digest does not match"):
            self.registry.transition("s01-11.beheto-contact", 1, "technical-approved", wrong, AT)

    def test_missing_or_modified_file_blocks_canonical_and_final_link(self):
        original = b"stable synthetic drawing v1"
        path = self.repo / "art/pose-v1.png"
        self.register()
        self.registry.transition("s01-11.beheto-contact", 1, "submitted", at=AT)
        self.registry.transition("s01-11.beheto-contact", 1, "technical-approved",
                                 self.approval("technical"), AT)
        self.registry.transition("s01-11.beheto-contact", 1, "author-approved",
                                 self.approval("author"), AT)
        path.write_bytes(b"modified before canonical")
        with self.assertRaisesRegex(AssetRegistryError, "hash mismatch"):
            self.registry.transition("s01-11.beheto-contact", 1, "canonical", at=AT)
        path.unlink()
        with self.assertRaisesRegex(AssetRegistryError, "missing"):
            self.registry.transition("s01-11.beheto-contact", 1, "canonical", at=AT)
        path.write_bytes(original)
        self.registry.transition("s01-11.beheto-contact", 1, "canonical", at=AT)
        path.write_bytes(b"modified before link")
        with self.assertRaisesRegex(AssetRegistryError, "hash mismatch"):
            self.registry.link_final("picture-lock.s01-11", "s01-11.beheto-contact", 1, ["S01-11"], AT)
        path.unlink()
        with self.assertRaisesRegex(AssetRegistryError, "missing"):
            self.registry.link_final("picture-lock.s01-11", "s01-11.beheto-contact", 1, ["S01-11"], AT)

    def test_file_integrity_is_rechecked_at_both_approval_gates(self):
        path = self.repo / "art/pose-v1.png"
        self.register(initial_state="submitted")
        path.write_bytes(b"modified before technical approval")
        with self.assertRaisesRegex(AssetRegistryError, "hash mismatch"):
            self.registry.transition("s01-11.beheto-contact", 1, "technical-approved",
                                     self.approval("technical"), AT)
        path.write_bytes(b"stable synthetic drawing v1")
        self.registry.transition("s01-11.beheto-contact", 1, "technical-approved",
                                 self.approval("technical"), AT)
        path.unlink()
        with self.assertRaisesRegex(AssetRegistryError, "missing"):
            self.registry.transition("s01-11.beheto-contact", 1, "author-approved",
                                     self.approval("author"), AT)

    def test_unapproved_and_rejected_assets_cannot_enter_final_use(self):
        self.register()
        with self.assertRaisesRegex(AssetRegistryError, "canonical"):
            self.registry.link_final("edit-main", "s01-11.beheto-contact", 1, ["S01-11"], AT)
        self.registry.transition("s01-11.beheto-contact", 1, "rejected", at=AT)
        with self.assertRaisesRegex(AssetRegistryError, "canonical"):
            self.registry.link_final("edit-main", "s01-11.beheto-contact", 1, ["S01-11"], AT)

    def test_canonical_link_requires_author_approval_and_declared_shot(self):
        self.register()
        self.approve_canonical()
        with self.assertRaisesRegex(AssetRegistryError, "declared"):
            self.registry.link_final("wrong-shot", "s01-11.beheto-contact", 1, ["S01-12"], AT)
        result = self.registry.link_final("picture-lock.s01-11", "s01-11.beheto-contact", 1, ["S01-11"], AT)
        self.assertEqual("picture-lock.s01-11", result["use_id"])
        verified = self.registry.verify()["final_uses"]["picture-lock.s01-11"]
        self.assertEqual({"asset_id": "s01-11.beheto-contact", "version": 1,
                          "shots": ["S01-11"]}, verified)
        self.assertEqual(["S01-11"], self.registry.summary()["final_uses"][0]["shots"])
        with self.assertRaisesRegex(AssetRegistryError, "Unlink"):
            self.registry.transition("s01-11.beheto-contact", 1, "rejected", at=AT)
        self.registry.unlink_final("picture-lock.s01-11", "Author requested replacement", AT)
        self.registry.transition("s01-11.beheto-contact", 1, "rejected", at=AT)
        self.assertEqual([], self.registry.summary()["final_uses"])

    def test_continuity_is_required_and_exact(self):
        for field in ("character_ids", "costume_ids", "prop_ids", "time", "location"):
            bad = self.continuity(); del bad[field]
            with self.subTest(field=field), self.assertRaises(AssetRegistryError):
                self.register(continuity=bad)
        bad = self.continuity(); bad["character_ids"] = ["beheto", "beheto"]
        with self.assertRaisesRegex(AssetRegistryError, "duplicate-free"):
            self.register(continuity=bad)

    def test_unsafe_private_or_signed_paths_and_urls_are_rejected(self):
        for path in ("/private/art.png", "../art.png", "art/.secret.png",
                     "https://example.com/art.png", "art/a.png?token=secret", "art\\a.png"):
            with self.subTest(path=path), self.assertRaises(AssetRegistryError):
                self.register(path=path)
        provenance = self.provenance(); provenance["public_source_url"] = "https://example.com/a.png?sig=secret"
        with self.assertRaisesRegex(AssetRegistryError, "public HTTPS"):
            self.register(provenance=provenance)

    def test_provenance_and_supersedes_must_reference_existing_versions(self):
        unknown = {"asset_id": "unknown", "version": 1}
        with self.assertRaisesRegex(AssetRegistryError, "supersedes"):
            self.register(supersedes=unknown)
        with self.assertRaisesRegex(AssetRegistryError, "source asset"):
            self.register(provenance=self.provenance([unknown]))

    def test_examples_parse_and_registry_history_verifies(self):
        root = Path(__file__).resolve().parents[1]
        approval = json.loads((root / "production/examples/approval_record.json").read_text())
        self.assertEqual("author", approval["type"])
        example = AssetRegistry(root, "production/examples/asset_registry.json")
        self.assertEqual("exploratory", example.summary()["assets"][0]["state"])


if __name__ == "__main__":
    unittest.main()
