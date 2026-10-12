import json
from pathlib import Path
import tempfile
import unittest

from production.host_handoff import HandoffRegistry
from production.runtime import Ledger, LedgerError


class HandoffTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        (self.repo / "production").mkdir()
        (self.repo / "input.txt").write_text("fixture")
        (self.repo / "production/roles.json").write_text(json.dumps({
            "worker": {"skill": "skills/worker/SKILL.md", "reviewer": "reviewer"},
            "reviewer": {"skill": "skills/reviewer/SKILL.md", "reviewer": "worker"}}))
        ledger = Ledger(self.repo, "run")
        ledger.add({"id": "task", "role": "worker", "shots": ["S01"], "objective": "Test",
                    "inputs": ["input.txt"], "output_dir": "production/runs/run/tasks/task", "depends_on": [],
                    "require_host_bindings": True})
        ledger.dispatch("task", "worker-alias")

    def result(self, **changes):
        result = {"task_id": "task", "role": "worker", "status": "submitted",
                  "artifacts": [], "evidence": ["Inspected fixture"], "blockers": [],
                  "host_agent_id": "/root/creator-real"}
        result.update(changes)
        return result

    def test_bind_persists_real_identity_without_spawning_claim(self):
        registry = HandoffRegistry(self.repo, "run")
        binding = registry.bind_creator("task", "chatgpt-work", "/root/creator-real")
        self.assertEqual("worker-alias", binding["ledger_alias"])
        self.assertEqual("/root/creator-real", HandoffRegistry(self.repo, "run").data["bindings"]["task"]["creator"]["host_agent_id"])
        with self.assertRaises(LedgerError): registry.bind_creator("task", "other", "new")

    def test_submission_requires_matching_creator_binding(self):
        ledger = Ledger(self.repo, "run")
        with self.assertRaisesRegex(LedgerError, "creator host binding"):
            ledger.submit(self.result())
        HandoffRegistry(self.repo, "run").bind_creator("task", "chatgpt-work", "/root/creator-real")
        with self.assertRaisesRegex(LedgerError, "creator host binding"):
            ledger.submit(self.result(host_agent_id="worker-alias"))
        ledger.submit(self.result())
        self.assertEqual("submitted", HandoffRegistry(self.repo, "run").data["bindings"]["task"]["creator"]["state"])

    def test_review_requires_real_distinct_designated_reviewer_binding(self):
        registry = HandoffRegistry(self.repo, "run")
        registry.bind_creator("task", "chatgpt-work", "/root/creator-real")
        Ledger(self.repo, "run").submit(self.result())
        ledger = Ledger(self.repo, "run")
        with self.assertRaisesRegex(LedgerError, "reviewer host binding"):
            ledger.review("task", "reviewer", "reviewer-alias", "approve", "checked")
        registry = HandoffRegistry(self.repo, "run")
        for role, agent in (("worker", "/root/reviewer-real"),
                            ("reviewer", "/root/creator-real"),
                            ("reviewer", "worker-alias")):
            with self.subTest(role=role, agent=agent), self.assertRaises(LedgerError):
                registry.bind_reviewer("task", role, "chatgpt-work", agent)
        registry.bind_reviewer("task", "reviewer", "chatgpt-work", "/root/reviewer-real")
        with self.assertRaisesRegex(LedgerError, "matching separate"):
            ledger.review("task", "reviewer", "fabricated-alias", "approve", "checked")
        ledger.review("task", "reviewer", "/root/reviewer-real", "approve", "Viewed evidence")
        fresh = HandoffRegistry(self.repo, "run")
        self.assertEqual("completed", fresh.data["bindings"]["task"]["creator"]["state"])
        self.assertEqual("completed", fresh.data["bindings"]["task"]["reviewer"]["state"])

    def test_interruption_pauses_ledger_and_terminal_binding_is_immutable(self):
        registry = HandoffRegistry(self.repo, "run")
        registry.bind_creator("task", "chatgpt-work", "/root/creator-real")
        registry.interrupt("task", "creator", "Connection lost")
        self.assertTrue(Ledger(self.repo, "run").data["paused"])
        with self.assertRaises(LedgerError): registry.update("task", "completed", "late")
        ledger = Ledger(self.repo, "run")
        ledger.resume("APPROVE RESUME run")
        with self.assertRaisesRegex(LedgerError, "creator host binding"):
            ledger.submit(self.result())
        ledger.validate()  # Interrupted assignment remains terminal but coherent.

    def test_rejects_inconsistent_completed_binding_on_running_task(self):
        registry = HandoffRegistry(self.repo, "run")
        registry.bind_creator("task", "chatgpt-work", "/root/creator-real")
        path = self.repo / "production/runs/run/handoffs.json"
        data = json.loads(path.read_text())
        data["bindings"]["task"]["creator"]["state"] = "completed"
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(LedgerError, "inconsistent"):
            HandoffRegistry(self.repo, "run")

    def test_simple_tasks_do_not_require_registry(self):
        ledger = Ledger(self.repo, "simple")
        ledger.add({"id": "plain", "role": "worker", "shots": [], "objective": "Simple fixture",
                    "inputs": ["input.txt"], "output_dir": "production/runs/simple/tasks/plain", "depends_on": []})
        ledger.dispatch("plain", "alias")
        ledger.submit({"task_id": "plain", "role": "worker", "status": "submitted",
                       "artifacts": [], "evidence": ["fixture"], "blockers": []})
        ledger.review("plain", "reviewer", "reviewer-alias", "approve", "fixture review")


if __name__ == "__main__": unittest.main()
