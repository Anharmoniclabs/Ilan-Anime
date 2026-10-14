"""Demand scheduling, real ledger transitions, hash gates and cloud handoff.

The worker outputs in these tests are synthetic fixtures, not generated art.
"""
from copy import deepcopy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image

from production.asset_registry import AssetRegistry
from production.runtime import Ledger
from studio import demand
from studio.paths import ROOT, sha256, write_json
from studio.runner import CodexRunner, RunnerError


class DemandTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        for path in (*demand.DOCS, "production/roles.json", "production/policy.json",
                     "production/WORKER_CONTRACT.md", "docs/IMAGE_DEMAND.md", "AGENTS.md"):
            dst = self.root / path
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / path, dst)
        self.picture(demand.STYLE)
        self.anchor = f"{demand.PROJECT}/assets/keyframes/S01-02.png"
        self.picture(self.anchor)
        shots = [{"id": f"S01-{i:02}", "script": f"Action {i}: moonless river, wooden paddle",
                  "frames": 72, "keyframes": ["assets/keyframes/S01-02.png"] if i == 2 else []}
                 for i in range(1, 5)]
        write_json(self.root / demand.EPISODE, {"shots": shots, "fps": 24})

    def picture(self, path, color="navy"):
        dst = self.root / path
        dst.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (160, 90), color).save(dst)
        return dst

    def packet(self, **kwargs):
        return demand.prepare(self.root, "S01-01", **kwargs)

    def output(self, packet):
        out = f"production/runs/{packet['run']}/tasks/image"
        self.picture(f"{out}/candidate.png")
        report = {"candidate_sha256": sha256(self.root / out / "candidate.png"),
                  "references": {r["snapshot"]: r["sha256"] for r in packet["references"]},
                  "checks": {k: "Synthetic evidence for test only" for k in demand.CHECKS},
                  "continuity": {"character_ids": [], "costume_ids": [], "prop_ids": ["paddle"],
                                 "time": "night", "location": "river"}}
        write_json(self.root / out / "continuity.json", report)
        return {"task_id": "image", "role": "layout-artist", "status": "submitted",
                "artifacts": [f"{out}/candidate.png", f"{out}/continuity.json"],
                "evidence": ["Synthetic fixture"], "blockers": []}

    def execute_fixture(self, packet, decision="approve"):
        runner = demand.ImageTurnRunner(packet, root=self.root)
        def session(prompt, schema, out, label, **kwargs):
            if label == "worker":
                return "test-creator", self.output(packet), None
            return "test-reviewer", {"decision": decision, "evidence": "Synthetic review",
                                     "repair_notes": []}, None
        with patch.object(runner, "_codex", side_effect=session):
            runner.loop(max_tasks=1)
        return runner

    def test_need_is_idempotent_and_only_one_image_task(self):
        packet = self.packet()
        self.assertEqual("generate-one", packet["route"])
        self.assertEqual(1, packet["max_images"])
        self.assertEqual(packet, self.packet())
        self.assertEqual(["image"], list(Ledger(self.root, packet["run"]).data["tasks"]))
        self.assertEqual(1, len(list((self.root / "production/runs").glob("*"))))

    def test_existing_candidate_is_not_regenerated(self):
        packet = demand.prepare(self.root, "S01-02")
        self.assertEqual("review-existing", packet["route"])
        self.assertEqual(0, packet["max_images"])

    def test_sparse_anchors_preserve_immediate_neighbors(self):
        packet = demand.prepare(self.root, "S01-03")
        self.assertEqual(["S01-02", "S01-04"], [n["id"] for n in packet["neighbors"]])

    def test_changed_source_or_snapshot_blocks_work(self):
        packet = self.packet()
        self.picture(self.anchor, "red")
        with self.assertRaisesRegex(demand.DemandError, "Reference changed"):
            demand.work(self.root, "S01-01", dry_run=True)

    def test_no_duplicate_revision_while_pending_or_paused(self):
        packet = self.packet()
        with self.assertRaisesRegex(demand.DemandError, "Existing demand"):
            self.packet(revision=2, correction="repair hand")
        Ledger(self.root, packet["run"]).pause("interrupted")
        with self.assertRaisesRegex(demand.DemandError, "Existing demand"):
            self.packet(revision=2, correction="repair hand")

    def test_generic_runner_cannot_bypass_demand_contract(self):
        packet = self.packet()
        with self.assertRaisesRegex(RunnerError, "studio demand work"):
            CodexRunner(packet["run"], root=self.root, dry_run=True).loop()

    def test_each_session_attaches_actual_reference_images(self):
        packet = self.packet()
        runner = demand.ImageTurnRunner(packet, root=self.root, dry_run=True)
        _, _, command = runner._codex("inspect references", {}, self.root / "test-output", "worker")
        self.assertEqual(command[-2:], ["--", "inspect references"])
        self.assertEqual(len(packet["references"]), command.count("--image"))
        for r in packet["references"]:
            self.assertIn(str(self.root / r["snapshot"]), command)

    def test_review_collect_idempotence_and_no_auto_author_approval(self):
        packet = self.packet()
        self.execute_fixture(packet)
        result = demand.collect(self.root, packet)
        self.assertEqual("technical-approved", result["asset"]["state"])
        before = (self.root / "production/asset-registry.json").read_bytes()
        demand.collect(self.root, packet)
        self.assertEqual(before, (self.root / "production/asset-registry.json").read_bytes())
        self.assertEqual("approved", Ledger(self.root, packet["run"])._task("image")["state"])
        with self.assertRaisesRegex(demand.DemandError, "canonical"):
            demand.video_handoff(self.root, "S01-01", "video-test")

    def test_mutating_candidate_and_report_after_review_is_detected(self):
        packet = self.packet()
        self.execute_fixture(packet)
        out = self.root / f"production/runs/{packet['run']}/tasks/image"
        self.picture(str((out / "candidate.png").relative_to(self.root)), "red")
        report = json.loads((out / "continuity.json").read_text())
        report["candidate_sha256"] = sha256(out / "candidate.png")
        write_json(out / "continuity.json", report)
        with self.assertRaisesRegex(demand.DemandError, "changed after submission"):
            demand.collect(self.root, packet)

    def test_invalid_continuity_fails_before_submission(self):
        packet = self.packet()
        runner = demand.ImageTurnRunner(packet, root=self.root)
        runner.launch("image")
        final = self.output(packet)
        p = self.root / f"production/runs/{packet['run']}/tasks/image/continuity.json"
        report = json.loads(p.read_text()); del report["continuity"]
        write_json(p, report)
        with self.assertRaisesRegex(ValueError, "continuity"):
            runner.submit("image", "test-creator", final)
        self.assertEqual("running", Ledger(self.root, packet["run"])._task("image")["state"])

    def test_rejection_needs_explicit_revision_and_no_auto_retry(self):
        packet = self.packet()
        self.execute_fixture(packet, "reject")
        ledger = Ledger(self.root, packet["run"])
        self.assertEqual(["image"], list(ledger.data["tasks"]))
        with self.assertRaisesRegex(demand.DemandError, "explicit --correction"):
            self.packet(revision=2)
        revised = self.packet(revision=2, correction="restore rigid paddle geometry")
        self.assertEqual("generate-one", revised["route"])

    def test_author_rejected_candidate_cannot_be_reused(self):
        packet = self.packet()
        self.execute_fixture(packet)
        asset = demand.collect(self.root, packet)["asset"]
        Ledger(self.root, packet["run"]).author_review("image", "luis-m-minier", "reject", "Wrong style")
        self.assertFalse(demand.eligible_image(demand.registry_assets(self.root)[0]))
        with self.assertRaisesRegex(demand.DemandError, "Rejected reference"):
            self.packet(revision=2, candidate=asset["path"])

    def test_interrupted_work_is_paused_without_a_second_session(self):
        self.packet()
        with patch.object(demand.ImageTurnRunner, "_codex", side_effect=RuntimeError("offline")) as call:
            with self.assertRaises(RuntimeError):
                demand.work(self.root, "S01-01")
            with self.assertRaises(RunnerError):
                demand.work(self.root, "S01-01")
            self.assertEqual(1, call.call_count)

    def test_paths_and_coordinator_lock(self):
        with self.assertRaises(demand.DemandError):
            self.packet(refs=["../outside.png"])
        (self.root / "link.png").symlink_to(self.root / self.anchor)
        with self.assertRaises(demand.DemandError):
            self.packet(refs=["link.png"])
        with demand.coordinator(self.root):
            with self.assertRaisesRegex(demand.DemandError, "coordinator is active"):
                with demand.coordinator(self.root):
                    pass

    def approve_fixture(self, asset):
        registry = AssetRegistry(self.root)
        registry.transition(asset["asset_id"], asset["version"], "author-approved", approval={
            "approval_id": "test-author", "type": "author", "asset_id": asset["asset_id"],
            "version": asset["version"], "asset_sha256": asset["sha256"],
            "approver_id": "luis-m-minier", "approver_role": "author",
            "evidence": "Synthetic test approval only", "at": "2026-10-12T00:00:00Z"})
        registry.transition(asset["asset_id"], asset["version"], "canonical")

    def test_canonical_handoff_prepares_hf_and_revocation_blocks_submission(self):
        from studio import video
        packet = self.packet()
        self.execute_fixture(packet)
        asset = demand.collect(self.root, packet)["asset"]
        self.approve_fixture(asset)
        with patch.object(video, "EPISODE", self.root / demand.EPISODE):
            job = demand.video_handoff(self.root, "S01-01", "video-test", frames=72)
            self.assertEqual(72, job["frames"])
            self.assertEqual("prepared", job["state"])
            demand.verify_video_source(self.root, self.root / "video-test")
            AssetRegistry(self.root).transition(asset["asset_id"], asset["version"], "rejected")
            with patch("studio.paths.ROOT", self.root), patch.object(video, "_client") as client:
                with self.assertRaisesRegex(demand.DemandError, "no longer canonical"):
                    video.submit(self.root / "video-test", client_factory=client)
                client.assert_not_called()
            self.assertFalse((self.root / "video-test/submission.lock").exists())

    def test_ensure_canonical_or_collected_does_not_run_a_new_worker(self):
        packet = self.packet()
        self.execute_fixture(packet)
        asset = demand.collect(self.root, packet)["asset"]
        with patch.object(demand.ImageTurnRunner, "_codex") as session:
            self.assertEqual("technical-approved", demand.ensure(self.root, "S01-01")["asset"]["state"])
            session.assert_not_called()
            self.approve_fixture(asset)
            self.assertEqual("reuse-canonical", demand.ensure(self.root, "S01-01")["route"])
            session.assert_not_called()

    def test_changed_unlaunched_packet_can_be_explicitly_superseded(self):
        old = self.packet()
        self.picture(self.anchor, "red")
        new = self.packet(revision=2, correction="Use the updated approved lighting reference")
        self.assertNotEqual(old["run"], new["run"])
        with self.assertRaisesRegex(demand.DemandError, "superseded"):
            demand.work(self.root, "S01-01", dry_run=True)
        self.assertEqual(["image"], demand.work(self.root, "S01-01", revision=2, dry_run=True)["ready"])

    def test_result_file_fallback_gets_same_hash_validation(self):
        packet = self.packet()
        runner = demand.ImageTurnRunner(packet, root=self.root)
        runner.launch("image")
        final = self.output(packet)
        out = self.root / f"production/runs/{packet['run']}/tasks/image"
        write_json(out / "result.json", final)
        self.picture(str((out / "candidate.png").relative_to(self.root)), "red")
        with self.assertRaisesRegex(demand.DemandError, "does not bind"):
            runner.submit("image", "test-creator", None)
        self.output(packet)
        runner.submit("image", "test-creator", None)
        self.assertTrue((self.root / demand.BASE / packet["run"] / "submission.json").exists())

    def test_existing_png_must_be_reused_without_changed_pixels(self):
        packet = demand.prepare(self.root, "S01-02")
        runner = demand.ImageTurnRunner(packet, root=self.root)
        runner.launch("image")
        final = self.output(packet)
        self.picture(f"production/runs/{packet['run']}/tasks/image/candidate.png", "red")
        with self.assertRaisesRegex(demand.DemandError, "byte-for-byte"):
            runner.submit("image", "test-creator", final)


if __name__ == "__main__":
    unittest.main()
