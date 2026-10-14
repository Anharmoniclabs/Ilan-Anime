"""Isolated ledger tests; no rendering, networking, or paid tools."""
import json
from pathlib import Path
import tempfile
import unittest

from production.runtime import Ledger, LedgerError


class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name).resolve()
        (self.repo / "approved.png").write_text("synthetic fixture, not artwork")
        (self.repo / "production").mkdir()
        (self.repo / "production/roles.json").write_text(json.dumps({"roles": {
            "animator": {"skill": "skills/animator/SKILL.md", "reviewer": "supervisor"},
            "supervisor": {"skill": "skills/supervisor/SKILL.md", "reviewer": "director"},
            "director": {"skill": "skills/director/SKILL.md", "reviewer": "supervisor"}}}))
        self.ledger = Ledger(self.repo, "pilot")

    def task(self, name="draw", deps=None):
        return {"id": name, "role": "animator", "shots": ["S01-11"],
                "objective": "Draw contact pose", "inputs": ["approved.png"],
                "output_dir": f"production/runs/pilot/tasks/{name}", "depends_on": deps or []}

    def result(self, name="draw", **changes):
        result = {"task_id": name, "role": "animator", "status": "submitted",
                  "artifacts": [], "evidence": ["Compared pose to approved reference"], "blockers": []}
        result.update(changes)
        return result

    def running(self, name="draw"):
        self.ledger.add(self.task(name))
        return self.ledger.dispatch(name, f"worker-{name}")

    def test_dependency_approval_and_persistence(self):
        prompt = self.running()
        self.assertIn("skills/animator/SKILL.md", prompt)
        self.assertIn("not an OS/tool sandbox", prompt)
        self.ledger.add(self.task("between", ["draw"]))
        self.assertEqual([], self.ledger.ready())
        self.ledger.submit(self.result())
        self.assertEqual([], self.ledger.ready())
        self.ledger.review("draw", "supervisor", "reviewer", "approve", "Checked contact pose")
        self.assertEqual(["between"], Ledger(self.repo, "pilot").ready())

    def test_unknown_role_and_missing_dependency(self):
        bad = self.task()
        bad["role"] = "unknown"
        with self.assertRaises(LedgerError):
            self.ledger.add(bad)
        with self.assertRaisesRegex(LedgerError, "Missing dependency"):
            self.ledger.add(self.task(deps=["missing"]))
        self.assertEqual({}, self.ledger.data["tasks"])

    def test_cycle(self):
        self.ledger.add(self.task("first"))
        self.ledger.add(self.task("second", ["first"]))
        self.ledger.data["tasks"]["first"]["depends_on"] = ["second"]
        with self.assertRaisesRegex(LedgerError, "cycle"):
            self.ledger.validate()

    def test_output_paths_and_ids(self):
        for name in ("../escape", "/absolute", "bad/name", ""):
            with self.assertRaises(LedgerError):
                self.ledger.add(self.task(name))
        bad = self.task()
        bad["output_dir"] = "production/runs/another/tasks/draw"
        with self.assertRaises(LedgerError):
            self.ledger.add(bad)

    def test_output_symlink(self):
        root = self.repo / "production/runs/pilot/tasks"
        root.mkdir(parents=True)
        (root / "draw").symlink_to(self.repo, target_is_directory=True)
        with self.assertRaisesRegex(LedgerError, "symlinks"):
            self.ledger.add(self.task())

    def test_result_identity_evidence_and_paths(self):
        self.running()
        for change in ({"role": "supervisor"}, {"evidence": []}, {"artifacts": ["../bad"]},
                       {"artifacts": ["production/runs/pilot/tasks/draw/missing.txt"]},
                       {"artifacts": [str(self.repo / "outside.txt")]},
                       {"blockers": ["Unresolved"]}):
            with self.assertRaises(LedgerError):
                self.ledger.submit(self.result(**change))
        outside = self.repo / "outside.txt"
        outside.write_text("not assigned")
        linked = self.repo / "production/runs/pilot/tasks/draw/link.txt"
        linked.symlink_to(outside)
        with self.assertRaises(LedgerError):
            self.ledger.submit(self.result(artifacts=[str(linked.relative_to(self.repo))]))
        good = linked.parent / "pose.txt"
        good.write_text("drawing evidence")
        self.ledger.submit(self.result(artifacts=[str(good.relative_to(self.repo))]))

    def test_independent_review(self):
        self.running()
        self.ledger.submit(self.result())
        for role, agent in (("animator", "reviewer"), ("director", "reviewer"),
                            ("supervisor", "worker-draw")):
            with self.assertRaises(LedgerError):
                self.ledger.review("draw", role, agent, "approve", "checked")
        self.ledger.review("draw", "supervisor", "reviewer", "reject", "Needs revision")
        self.assertEqual("rejected", self.ledger.data["tasks"]["draw"]["state"])
        with self.assertRaises(LedgerError):
            self.ledger.dispatch("draw", "another-worker")

    def test_concurrency(self):
        for index in range(6):
            self.running(f"task{index}")
        self.ledger.add(self.task("overflow"))
        with self.assertRaisesRegex(LedgerError, "Six-worker"):
            self.ledger.dispatch("overflow", "worker-overflow")

    def test_pause_approval_does_not_retry(self):
        self.running()
        self.ledger.submit(self.result(status="blocked", evidence=[], blockers=["Connection interrupted"]))
        self.assertTrue(Ledger(self.repo, "pilot").data["paused"])
        self.assertEqual([], self.ledger.ready())
        with self.assertRaises(LedgerError):
            self.ledger.add(self.task("new"))
        with self.assertRaises(LedgerError):
            self.ledger.resume("yes")
        self.ledger.resume("APPROVE RESUME pilot")
        self.assertEqual("blocked", self.ledger.data["tasks"]["draw"]["state"])
        self.assertEqual([], self.ledger.ready())

    def test_pause_running_preserves_assignment(self):
        self.running()
        self.ledger.pause("Host connection lost")
        with self.assertRaises(LedgerError):
            self.ledger.submit(self.result())
        self.ledger.resume("APPROVE RESUME pilot")
        self.assertEqual("running", self.ledger.data["tasks"]["draw"]["state"])

    def test_optional_contract_survives_add_and_dispatch(self):
        task = self.task()
        task.update(acceptance_criteria=["Contact point stays fixed"],
                    budget={"max_tool_calls": 8, "max_seconds": 120, "max_cost_usd": 0})
        self.ledger.add(task)
        fresh = Ledger(self.repo, "pilot")
        self.assertEqual(task["acceptance_criteria"], fresh.data["tasks"]["draw"]["acceptance_criteria"])
        prompt = fresh.dispatch("draw", "worker")
        self.assertIn("Contact point stays fixed", prompt)
        self.assertIn('"max_tool_calls": 8', prompt)

    def test_optional_contract_validation(self):
        for field, value in (("acceptance_criteria", []), ("acceptance_criteria", [""]),
                             ("acceptance_criteria", "check"), ("budget", {}),
                             ("budget", {"max_tool_calls": -1}), ("budget", {"max_seconds": True}),
                             ("budget", {"max_cost_usd": 1}), ("budget", {"unknown": 1})):
            task = self.task()
            task[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(LedgerError):
                self.ledger.add(task)
        for field, value in (("requires_author_approval", "yes"),
                             ("require_host_bindings", "yes"),
                             ("art_direction_mode", "generic-anime")):
            task = self.task(); task[field] = value
            with self.subTest(field=field), self.assertRaises(LedgerError):
                self.ledger.add(task)

        task = self.task()
        task.update(requires_author_approval=True, author_approver="someone-else")
        with self.assertRaisesRegex(LedgerError, "luis-m-minier"):
            self.ledger.add(task)

    def test_missing_unsafe_inputs_do_not_dispatch(self):
        external = tempfile.TemporaryDirectory()
        self.addCleanup(external.cleanup)
        (self.repo / "outside-link").symlink_to(external.name, target_is_directory=True)
        for index, source in enumerate(("missing.png", "../escape", str(self.repo / "approved.png"), "outside-link")):
            task = self.task(f"input{index}")
            task["inputs"] = [source]
            self.ledger.add(task)
            with self.subTest(source=source), self.assertRaises(LedgerError):
                self.ledger.dispatch(task["id"], "worker")
            self.assertEqual("pending", self.ledger.data["tasks"][task["id"]]["state"])
            self.assertFalse((self.repo / task["output_dir"]).exists())

    def test_persisted_state_requires_result_and_review(self):
        self.ledger.add(self.task())
        task = self.ledger.data["tasks"]["draw"]
        for state in ("made-up", "approved", "rejected", "submitted"):
            task["state"] = state
            with self.subTest(state=state), self.assertRaises(LedgerError):
                self.ledger.validate()
        task.update(state="approved", result=self.result())
        with self.assertRaisesRegex(LedgerError, "review"):
            self.ledger.validate()

    def test_author_gate_blocks_dependents_until_explicit_human_review(self):
        task = self.task()
        task.update(requires_author_approval=True, author_approver="luis-m-minier", art_direction_mode="STORY_FRAME")
        self.ledger.add(task)
        prompt = self.ledger.dispatch("draw", "worker")
        self.assertIn("production/art_direction.json", prompt)
        self.ledger.submit(self.result())
        self.ledger.review("draw", "supervisor", "reviewer", "approve", "Technical checks pass")
        self.ledger.add(self.task("composite", ["draw"]))
        self.assertEqual([], self.ledger.ready())
        with self.assertRaises(LedgerError):
            self.ledger.author_review("draw", "someone-else", "approve", "Looks correct")
        self.ledger.author_review("draw", "luis-m-minier", "approve", "Approved this exact story frame")
        self.assertEqual(["composite"], self.ledger.ready())

    def test_author_rejection_never_unlocks_dependency(self):
        task = self.task()
        task.update(requires_author_approval=True, author_approver="luis-m-minier")
        self.ledger.add(task)
        self.ledger.dispatch("draw", "worker")
        self.ledger.submit(self.result())
        self.ledger.review("draw", "supervisor", "reviewer", "approve", "Technically valid")
        self.ledger.author_review("draw", "luis-m-minier", "reject", "Face does not match")
        self.ledger.add(self.task("paint", ["draw"]))
        self.assertEqual([], self.ledger.ready())

    def test_persisted_author_identity_must_equal_designated_approver(self):
        task = self.task()
        task.update(requires_author_approval=True, author_approver="luis-m-minier")
        self.ledger.add(task)
        self.ledger.dispatch("draw", "worker")
        self.ledger.submit(self.result())
        self.ledger.review("draw", "supervisor", "reviewer", "approve", "Technical pass")
        self.ledger.author_review("draw", "luis-m-minier", "approve", "Approved exact asset")
        path = self.repo / "production/runs/pilot/ledger.json"
        data = json.loads(path.read_text())
        data["tasks"]["draw"]["author_review"]["author"] = "fabricated-author"
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(LedgerError, "author review"):
            Ledger(self.repo, "pilot").validate()


if __name__ == "__main__":
    unittest.main()
