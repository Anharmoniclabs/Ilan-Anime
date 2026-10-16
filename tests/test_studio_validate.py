import copy
import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from production.asset_registry import AssetRegistry
from production.host_handoff import HandoffRegistry
from production.runtime import Ledger
from production.studio_validate import (
    StudioValidationError, _qa_release_shots, episode_release_evidence, validate_art_contract,
    validate_role_contracts, validate_studio,
)


class StudioValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parents[1]

    def test_repository_architecture_is_coherent_but_episode_truth_remains_unfinished(self):
        report = validate_studio(self.root)
        self.assertEqual([], report["errors"])
        self.assertTrue(report["architecture_valid"])
        self.assertFalse(report["episode_ready"])
        self.assertGreaterEqual(report["roles"], 30)
        self.assertEqual(128, report["shots"])
        self.assertIn("never proves visual quality", report["truth"])

    def test_role_contract_rejects_self_review(self):
        roles = json.loads((self.root / "production/roles.json").read_text())
        roles = copy.deepcopy(roles)
        records = roles.get("roles", roles)
        records["storyboard"]["reviewer"] = "storyboard"
        with self.assertRaisesRegex(StudioValidationError, "independent"):
            validate_role_contracts(self.root, roles)

    def test_art_contract_rejects_wrong_author(self):
        contract = json.loads((self.root / "production/art_direction.json").read_text())
        contract = copy.deepcopy(contract)
        contract["promotion"]["author_id"] = "fake-approver"
        with self.assertRaisesRegex(StudioValidationError, "luis-m-minier"):
            validate_art_contract(contract)

    def test_manifest_labels_cannot_claim_episode_release(self):
        shots = [{"id": "S01-01", "animation_status": "approved", "voice_status": "approved"}]
        ready, evidence = episode_release_evidence(self.root, shots)
        self.assertFalse(ready)
        self.assertTrue(evidence["missing"])
        with tempfile.TemporaryDirectory() as directory:
            ready, evidence = episode_release_evidence(Path(directory), shots)
        self.assertFalse(ready)
        self.assertIn("canonical production asset registry", evidence["missing"])

    def test_fake_named_qa_task_cannot_satisfy_release(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "production/runs/r/tasks/show-qa"
            output.mkdir(parents=True)
            report = output / "report.json"
            report.write_text("{}")
            digest = hashlib.sha256(report.read_bytes()).hexdigest()
            task = {
                "id": "show-qa", "role": "worker", "state": "author-approved",
                "require_host_bindings": False, "requires_author_approval": True,
                "author_approver": "luis-m-minier", "art_direction_mode": "STORY_FRAME",
                "depends_on": ["show-edit", "show-final-manifest", "show-pipeline-contract"],
                "shots": ["S01"], "output_dir": "production/runs/r/tasks/show-qa",
                "author_review": {"author": "luis-m-minier", "decision": "approve"},
                "result": {"pipeline_id": "show", "artifacts": [report.relative_to(root).as_posix()],
                           "release_asset_sha256s": ["a" * 64],
                           "qa_report": {"path": report.relative_to(root).as_posix(), "sha256": digest}},
            }
            self.assertEqual(set(), _qa_release_shots(task, {"S01"}, {"S01": {"a" * 64}}, root))
            task.update(role="quality-review", require_host_bindings=True)
            self.assertEqual({"S01"}, _qa_release_shots(task, {"S01"}, {"S01": {"a" * 64}}, root))

    def test_real_bound_qa_submission_can_satisfy_release_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "production").mkdir()
            shutil.copy(self.root / "production/roles.json", root / "production/roles.json")
            (root / "final").mkdir()
            (root / "final/picture.bin").write_bytes(b"final picture")
            (root / "final/audio.bin").write_bytes(b"final audio")
            registry = AssetRegistry(root)
            digests = []
            for asset_id, path, kind in (("s01.picture", "final/picture.bin", "final-picture"),
                                         ("s01.audio", "final/audio.bin", "final-audio")):
                record = registry.register(
                    asset_id=asset_id, path=path, kind=kind, mode="production", shots=["S01"],
                    provenance={"origin": "test", "creator": "artist", "license": "project-owned",
                                "source_assets": [], "notes": "release integration fixture"},
                    continuity={"character_ids": [], "costume_ids": [], "prop_ids": [],
                                "time": "test", "location": "test"}, initial_state="submitted")
                digests.append(record["sha256"])
                technical = {"approval_id": f"{asset_id}.technical", "type": "technical",
                             "asset_id": asset_id, "version": 1, "asset_sha256": record["sha256"],
                             "approver_id": "reviewer", "approver_role": "quality-review",
                             "evidence": "verified", "at": "2026-10-12T00:00:00Z"}
                author = {"approval_id": f"{asset_id}.author", "type": "author",
                          "asset_id": asset_id, "version": 1, "asset_sha256": record["sha256"],
                          "approver_id": "luis-m-minier", "approver_role": "author",
                          "evidence": "approved", "at": "2026-10-12T00:00:00Z"}
                registry.transition(asset_id, 1, "technical-approved", technical)
                registry.transition(asset_id, 1, "author-approved", author)
                registry.transition(asset_id, 1, "canonical")
                registry.link_final(f"{asset_id}.use", asset_id, 1, ["S01"])

            ledger = Ledger(root, "release")
            dependencies = {"show-edit": "editor", "show-final-manifest": "asset-manager",
                            "show-pipeline-contract": "pipeline-td"}
            for task_id, role in dependencies.items():
                ledger.add({"id": task_id, "role": role, "shots": ["S01"], "objective": "fixture",
                            "inputs": [], "output_dir": f"production/runs/release/tasks/{task_id}",
                            "depends_on": []})
                ledger.dispatch(task_id, f"{task_id}-worker")
                ledger.submit({"task_id": task_id, "role": role, "status": "submitted",
                               "artifacts": [], "evidence": ["fixture"], "blockers": []})
                reviewer = ledger.roles[role]["reviewer"]
                ledger.review(task_id, reviewer, f"{task_id}-reviewer", "approve", "fixture")
            ledger.add({"id": "show-qa", "role": "quality-review", "shots": ["S01"],
                        "objective": "release QA", "inputs": [],
                        "output_dir": "production/runs/release/tasks/show-qa",
                        "depends_on": list(dependencies), "require_host_bindings": True,
                        "requires_author_approval": True, "author_approver": "luis-m-minier",
                        "art_direction_mode": "STORY_FRAME"})
            prompt = ledger.dispatch("show-qa", "qa-worker")
            self.assertIn("release_asset_sha256s", prompt)
            HandoffRegistry(root, "release").bind_creator(
                "show-qa", "chatgpt-work", "/root/real-qa-creator")
            report = root / "production/runs/release/tasks/show-qa/report.json"
            report.write_text("{}")
            report_path = report.relative_to(root).as_posix()
            ledger.submit({"task_id": "show-qa", "role": "quality-review", "status": "submitted",
                           "artifacts": [report_path], "evidence": ["viewed final picture and audio"],
                           "blockers": [], "host_agent_id": "/root/real-qa-creator",
                           "pipeline_id": "show", "release_asset_sha256s": digests,
                           "qa_report": {"path": report_path,
                                         "sha256": hashlib.sha256(report.read_bytes()).hexdigest()}})
            HandoffRegistry(root, "release").bind_reviewer(
                "show-qa", "producer", "chatgpt-work", "/root/real-qa-reviewer")
            ledger.review("show-qa", "producer", "/root/real-qa-reviewer", "approve", "reviewed")
            ledger.author_review("show-qa", "luis-m-minier", "approve", "approved exact QA")
            ready, evidence = episode_release_evidence(root, [{"id": "S01"}])
            self.assertTrue(ready, evidence)


if __name__ == "__main__": unittest.main()
