"""Contract handoff regressions; synthetic artifacts, no agents or media generation."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from production.pipeline import ledger_task
from production.runtime import Ledger, LedgerError
from studio.runner import CodexRunner, RESULT_SCHEMA, result_schema


class RunnerContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "production").mkdir()
        roles = {
            "maker": {"skill": ".agents/skills/anime-maker/SKILL.md", "reviewer": "checker"},
            "checker": {"skill": ".agents/skills/anime-checker/SKILL.md", "reviewer": "maker"},
            "quality-review": {"skill": ".agents/skills/anime-quality-review/SKILL.md", "reviewer": "checker"},
        }
        (self.root / "production/roles.json").write_text(json.dumps(roles))
        self.policy = {"generation": {"enabled": False}, "revisions": {"max_revisions_per_task": 2}}
        self.ledger = Ledger(self.root, "fixture")
        self.task = {
            "id": "keys", "role": "maker", "shots": ["S01-07"], "objective": "Draw the writing action",
            "inputs": [], "depends_on": [], "output_dir": "production/runs/fixture/tasks/keys",
            "full_scene_action": {"character": ["write two lines"], "prop": ["pen contacts page"],
                                  "environment": [], "effects": [], "camera": []},
            "completion_contract": {"required_artifact_kinds": ["registered keys"],
                                    "required_evidence_kinds": ["pen contact review"],
                                    "independent_review_required": True, "technical_gate": False,
                                    "author_gate": None},
        }

    def running(self, task=None):
        task = task or self.task
        self.ledger.add(ledger_task(task))
        prompt = self.ledger.dispatch(task["id"], "creator")
        artifact = self.root / task["output_dir"] / "keys.txt"
        artifact.write_text("synthetic test evidence, not artwork")
        path = artifact.relative_to(self.root).as_posix()
        result = {"task_id": task["id"], "role": task["role"], "status": "submitted", "artifacts": [path],
                  "evidence": ["fixture inspection"], "blockers": [],
                  "completion": {"artifacts": [{"path": path, "kind": "registered keys"}],
                                 "evidence": [{"kind": "pen contact review", "detail": "fixture contact observed"}]}}
        return result, prompt

    def test_contract_survives_planning_dispatch_review_and_dependency(self):
        result, prompt = self.running()
        self.assertIn("write two lines", prompt)
        self.assertIn("required_artifact_kinds", prompt)
        self.assertIn("completion: {artifacts", prompt)
        self.ledger.submit(result)
        next_task = {**self.task, "id": "cleanup", "output_dir": "production/runs/fixture/tasks/cleanup",
                     "depends_on": ["keys"]}
        self.ledger.add(ledger_task(next_task))
        self.assertEqual([], self.ledger.ready())
        self.ledger.review("keys", "checker", "reviewer", "approve", "independent fixture review")
        self.assertEqual(["cleanup"], Ledger(self.root, "fixture").ready())

    def test_missing_kind_evidence_or_unlisted_artifact_cannot_submit(self):
        result, _ = self.running()
        variants = []
        missing = deepcopy(result); missing.pop("completion"); variants.append(missing)
        missing = deepcopy(result); missing["completion"]["artifacts"] = []; variants.append(missing)
        missing = deepcopy(result); missing["completion"]["evidence"] = []; variants.append(missing)
        missing = deepcopy(result); missing["completion"]["evidence"][0]["detail"] = " "; variants.append(missing)
        missing = deepcopy(result); missing["artifacts"] = []; variants.append(missing)
        for bad in variants:
            with self.subTest(bad=bad), self.assertRaises(LedgerError):
                self.ledger.submit(bad)
            self.assertEqual("running", self.ledger._task("keys")["state"])

    def test_artifact_escape_and_missing_file_are_rejected(self):
        result, _ = self.running()
        result["artifacts"] = ["../outside.txt"]
        result["completion"]["artifacts"][0]["path"] = "../outside.txt"
        with self.assertRaisesRegex(LedgerError, "safe repository-relative"):
            self.ledger.submit(result)
        result["artifacts"] = [self.task["output_dir"] + "/missing.txt"]
        result["completion"]["artifacts"][0]["path"] = result["artifacts"][0]
        with self.assertRaisesRegex(LedgerError, "Missing completion artifact"):
            self.ledger.submit(result)

    def test_artifact_removal_between_submit_and_approval_blocks_release(self):
        result, _ = self.running()
        self.ledger.submit(result)
        (self.root / result["artifacts"][0]).unlink()
        with self.assertRaisesRegex(LedgerError, "Missing completion artifact"):
            self.ledger.review("keys", "checker", "reviewer", "approve", "not enough")
        self.assertEqual("submitted", self.ledger._task("keys")["state"])

    def test_legacy_and_blocked_results_remain_compatible(self):
        legacy = deepcopy(self.task); legacy.pop("completion_contract"); legacy.pop("full_scene_action")
        result, _ = self.running(legacy)
        result.pop("completion")
        self.ledger.submit(result)
        self.ledger.review("keys", "checker", "reviewer", "approve", "legacy review")
        blocked_task = {**self.task, "id": "blocked", "output_dir": "production/runs/fixture/tasks/blocked"}
        result, _ = self.running(blocked_task)
        result.update(status="blocked", blockers=["drawing missing"], artifacts=[], completion={"artifacts": [], "evidence": []})
        self.ledger.submit(result)
        self.assertTrue(self.ledger.data["paused"])

    def test_revision_preserves_contract_and_action(self):
        result, _ = self.running()
        self.ledger.submit(result)
        self.ledger.review("keys", "checker", "reviewer", "reject", "repair grip")
        runner = CodexRunner("fixture", root=self.root, policy=self.policy, log=lambda value: None)
        review_dir = runner.run_dir / "reviews/keys"
        review_dir.mkdir(parents=True)
        (review_dir / "review.json").write_text('{"decision":"reject"}')
        new_id = runner.revise("keys", {"repair_notes": ["repair grip"]}, review_dir)
        revised = runner.ledger._task(new_id)
        self.assertEqual(self.task["completion_contract"], revised["completion_contract"])
        self.assertEqual(self.task["full_scene_action"], revised["full_scene_action"])

    def test_live_author_gate_still_blocks_and_no_stale_gate_snapshot_is_kept(self):
        task = {**self.task, "requires_author_approval": True, "author_approver": "luis-m-minier",
                "blocked_by_gates": ["stale-planning-snapshot"]}
        result, _ = self.running(task)
        self.assertNotIn("blocked_by_gates", self.ledger._task("keys"))
        self.ledger.submit(result)
        self.ledger.review("keys", "checker", "reviewer", "approve", "technical review")
        next_task = {**self.task, "id": "cleanup", "output_dir": "production/runs/fixture/tasks/cleanup",
                     "depends_on": ["keys"]}
        self.ledger.add(ledger_task(next_task))
        self.assertEqual([], self.ledger.ready())
        self.ledger.author_review("keys", "luis-m-minier", "approve", "synthetic fixture author decision")
        self.assertEqual(["cleanup"], self.ledger.ready())

    def test_task_schema_includes_contract_and_release_qa_fields(self):
        schema = result_schema(self.task)
        self.assertIn("completion", schema["required"])
        self.assertNotIn("completion", RESULT_SCHEMA["properties"])
        qa = {**self.task, "id": "shot-qa", "role": "quality-review"}
        qa_schema = result_schema(qa)
        for field in ("pipeline_id", "qa_report", "release_asset_sha256s"):
            self.assertIn(field, qa_schema["required"])
            self.assertIn(field, qa_schema["properties"])
        self.ledger.add(ledger_task(self.task))
        runner = CodexRunner("fixture", root=self.root, policy=self.policy, log=lambda value: None)
        job = runner.launch("keys")
        with patch.object(runner, "_codex", return_value=("thread", None, None)) as call:
            runner.execute(job)
        self.assertEqual(schema, call.call_args.args[1])

    def test_malformed_contracts_fail_before_dispatch(self):
        for field, value in (("full_scene_action", {"camera": []}),
                             ("completion_contract", {"required_artifact_kinds": []})):
            task = {**self.task, field: value}
            with self.subTest(field=field), self.assertRaises(LedgerError):
                self.ledger.add(ledger_task(task))
        task = deepcopy(self.task)
        task["completion_contract"]["author_gate"] = "final-author-approval"
        with self.assertRaisesRegex(LedgerError, "requires runtime author approval"):
            self.ledger.add(ledger_task(task))


if __name__ == "__main__":
    unittest.main()
