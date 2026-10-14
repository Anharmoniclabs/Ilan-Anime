"""Complete-shot pipeline contract tests; no rendering or network calls."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from production.pipeline import (
    PipelineError,
    build_pipeline,
    ledger_task,
    load_json,
    validate_author_gate,
    validate_completion,
)
from production.runtime import Ledger
from production.asset_registry import AssetRegistry


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = load_json(ROOT / "production/pipeline_templates/complete_shot.json")
ROLES = load_json(ROOT / "production/roles.json")
EXAMPLE = load_json(ROOT / "production/examples/s01_11_12_pipeline.json")


class PipelineTests(unittest.TestCase):
    def registry_fixture(self, registered_shots=None, link_shots=None):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        repo = Path(temporary.name)
        for relative in EXAMPLE["source_inputs"] + ["production/art_direction.json"]:
            target = repo / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((ROOT / relative).read_bytes())
        for reference in EXAMPLE["comparison_references"]:
            target = repo / reference["path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((ROOT / reference["path"]).read_bytes())
        artifact = repo / "production/runs/final/tasks/s01-11-12-qa/final-review.mp4"
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_bytes(b"synthetic final review media")
        registry = AssetRegistry(repo)
        record = registry.register(
            asset_id="s01-11-12.final-review", path=artifact.relative_to(repo).as_posix(),
            kind="review-render", mode="production",
            shots=registered_shots or ["S01-11", "S01-12"],
            provenance={"origin": "test", "creator": "test", "license": "project-owned",
                        "source_assets": [], "notes": "synthetic fixture"},
            continuity={"character_ids": [], "costume_ids": [], "prop_ids": [],
                        "time": "night", "location": "river"}, initial_state="submitted")
        registry.transition(record["asset_id"], 1, "technical-approved", approval={
            "approval_id": "qa-tech", "type": "technical", "asset_id": record["asset_id"],
            "version": 1, "asset_sha256": record["sha256"], "approver_id": "quality-review",
            "approver_role": "quality-review", "evidence": "fixture technical review",
            "at": "2026-10-12T12:00:00-04:00"})
        registry.transition(record["asset_id"], 1, "author-approved", approval={
            "approval_id": "qa-author", "type": "author", "asset_id": record["asset_id"],
            "version": 1, "asset_sha256": record["sha256"], "approver_id": "luis-m-minier",
            "approver_role": "author", "evidence": "viewed exact fixture",
            "at": "2026-10-12T12:01:00-04:00"})
        registry.transition(record["asset_id"], 1, "canonical")
        registry.link_final("episode-review", record["asset_id"], 1,
                            link_shots or registered_shots or ["S01-11", "S01-12"])
        return repo, artifact, record

    def test_example_is_blocked_at_real_timing_decision(self):
        pipeline = build_pipeline(EXAMPLE, TEMPLATE, ROLES, ROOT)
        self.assertEqual("blocked", pipeline["status"])
        self.assertEqual("unresolved", pipeline["timing_status"])
        self.assertEqual(3, len(pipeline["timing_conflicts"]))
        self.assertEqual(["s01-11-12-script-timing"], pipeline["ready_tasks"])
        board = next(task for task in pipeline["tasks"] if task["id"].endswith("-storyboard"))
        self.assertIn("timing-author-approval", board["blocked_by_gates"])

    def test_full_pipeline_has_bounded_ledger_tasks(self):
        pipeline = build_pipeline(EXAMPLE, TEMPLATE, ROLES, ROOT)
        self.assertEqual(27, len(pipeline["tasks"]))
        for task in pipeline["tasks"]:
            self.assertTrue(task["require_host_bindings"])
            self.assertEqual(0, task["budget"]["max_cost_usd"])
            self.assertTrue(task["acceptance_criteria"])
            self.assertTrue(task["completion_contract"]["required_artifact_kinds"])
            self.assertTrue(task["completion_contract"]["required_evidence_kinds"])
            self.assertEqual(
                f"production/runs/{pipeline['run']}/tasks/{task['id']}", task["output_dir"]
            )
            self.assertNotEqual(task["role"], task["reviewer_role"])
        keys = next(task for task in pipeline["tasks"] if task["id"].endswith("-keys"))
        self.assertTrue(any("camera-only" in item for item in keys["acceptance_criteria"]))

    def test_specialist_roles_and_runtime_fields_are_integrated(self):
        pipeline = build_pipeline(EXAMPLE, TEMPLATE, ROLES, ROOT)
        expected = {
            "script-timing": "script-supervisor",
            "layout": "layout-artist",
            "prop-design": "prop-designer",
            "background-paint": "background-painter",
            "rig-decision": "character-rigger",
            "cleanup": "cleanup-artist",
            "ink-paint": "ink-paint-artist",
            "effects": "effects-animator",
            "pipeline-contract": "pipeline-td",
            "asset-register": "asset-manager",
            "sound-plan": "sound-director",
            "voice": "voice-performer",
            "dialogue-edit": "dialogue-editor",
            "sfx": "sfx-artist",
            "music": "music-composer",
            "mix": "mix-engineer",
        }
        by_stage = {task["id"].removeprefix("s01-11-12-"): task for task in pipeline["tasks"]}
        for stage, role in expected.items():
            self.assertEqual(role, by_stage[stage]["role"])
        self.assertIn("no rig", " ".join(by_stage["rig-decision"]["acceptance_criteria"]).lower())
        self.assertTrue(by_stage["script-timing"]["requires_author_approval"])
        self.assertEqual("luis-m-minier", by_stage["script-timing"]["author_approver"])
        self.assertTrue(by_stage["qa"]["requires_author_approval"])
        self.assertEqual("ENVIRONMENT_PLATE", by_stage["background-paint"]["art_direction_mode"])
        self.assertEqual("STORY_FRAME", ledger_task(by_stage["keys"])["art_direction_mode"])
        self.assertTrue(ledger_task(by_stage["qa"])["requires_author_approval"])
        self.assertTrue(ledger_task(by_stage["qa"])["require_host_bindings"])
        for task in pipeline["tasks"]:
            self.assertNotIn("research/supplied_references/approved_style_reference.png", task["inputs"])
        self.assertEqual("visual-style-comparison-only", pipeline["comparison_references"][0]["purpose"])

    def test_all_tasks_are_accepted_by_existing_ledger(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            (repo / "production").mkdir()
            (repo / "production/roles.json").write_text(json.dumps(ROLES))
            ledger = Ledger(repo, EXAMPLE["run"])
            pipeline = build_pipeline(EXAMPLE, TEMPLATE, ROLES)
            for task in pipeline["tasks"]:
                ledger.add(ledger_task(task))
            self.assertTrue(ledger.validate())
            self.assertEqual(["s01-11-12-script-timing"], ledger.ready())

    def test_camera_only_or_missing_scene_action_is_rejected(self):
        for mutation in ("character", "environment"):
            spec = copy.deepcopy(EXAMPLE)
            spec["full_scene_action"][mutation] = []
            with self.subTest(mutation=mutation), self.assertRaisesRegex(PipelineError, "full_scene_action"):
                build_pipeline(spec, TEMPLATE, ROLES)

    def test_rejected_media_cannot_be_smuggled_as_source_input(self):
        spec = copy.deepcopy(EXAMPLE)
        spec["source_inputs"].append(
            "projects/cemi_episode_01/renders/Cemi_SC0_Current_Turns_motion_test.mp4"
        )
        with self.assertRaisesRegex(PipelineError, "text/data"):
            build_pipeline(spec, TEMPLATE, ROLES)

    def test_caller_status_cannot_relabel_exploratory_cel(self):
        spec = copy.deepcopy(EXAMPLE)
        spec["assets"] = [{
            "path": "projects/cemi_episode_01/assets/replacement_cels/lead_canoe_eight_poses.png",
            "status": "canonical"
        }]
        with self.assertRaisesRegex(PipelineError, "Caller-declared asset status is forbidden"):
            build_pipeline(spec, TEMPLATE, ROLES)

    def test_fake_final_gate_strings_are_rejected(self):
        spec = copy.deepcopy(EXAMPLE)
        spec["gate_decisions"]["final-author-approval"] = {
            "status": "approved", "evidence": ["x", "y", "z"]
        }
        with self.assertRaisesRegex(PipelineError, "Final author approval must contain exactly"):
            build_pipeline(spec, TEMPLATE, ROLES)

    def test_registry_verified_media_and_digest_bound_final_gate(self):
        repo, artifact, record = self.registry_fixture()
        ref = {"asset_id": record["asset_id"], "version": 1, "sha256": record["sha256"],
               "final_use_id": "episode-review"}
        spec = copy.deepcopy(EXAMPLE)
        spec["production_assets"] = [ref]
        spec["gate_decisions"]["final-author-approval"] = {
            "status": "approved", "author_id": "luis-m-minier",
            "qa_task_id": "s01-11-12-qa", "qa_artifact_path": record["path"],
            "qa_artifact_sha256": record["sha256"], "viewed_artifact": record["path"],
            "approval_reference": "recorded-author-review-001",
            "registry_ref": {**ref, "author_approval_id": "qa-author"}
        }
        pipeline = build_pipeline(spec, TEMPLATE, ROLES, repo)
        self.assertEqual(["S01-11", "S01-12"],
                         pipeline["verified_production_assets"][0]["final_use_shots"])
        self.assertTrue(validate_author_gate(pipeline, "final-author-approval", repo))
        self.assertIn(record["path"], pipeline["tasks"][0]["inputs"])
        artifact.write_bytes(b"tampered after approval")
        with self.assertRaisesRegex(PipelineError, "registry verification failed"):
            build_pipeline(spec, TEMPLATE, ROLES, repo)

    def test_pipeline_cannot_bypass_registered_asset_shot_scope(self):
        repo, _, record = self.registry_fixture(registered_shots=["S01-11"])
        spec = copy.deepcopy(EXAMPLE)
        spec["production_assets"] = [{"asset_id": record["asset_id"], "version": 1,
                                      "sha256": record["sha256"],
                                      "final_use_id": "episode-review"}]
        with self.assertRaisesRegex(PipelineError, "registered asset shot scope"):
            build_pipeline(spec, TEMPLATE, ROLES, repo)

    def test_pipeline_cannot_bypass_final_use_link_shot_scope(self):
        repo, _, record = self.registry_fixture(link_shots=["S01-11"])
        spec = copy.deepcopy(EXAMPLE)
        spec["production_assets"] = [{"asset_id": record["asset_id"], "version": 1,
                                      "sha256": record["sha256"],
                                      "final_use_id": "episode-review"}]
        with self.assertRaisesRegex(PipelineError, "final-use link shot scope"):
            build_pipeline(spec, TEMPLATE, ROLES, repo)

    def test_unresolved_timing_cannot_be_empty(self):
        spec = copy.deepcopy(EXAMPLE)
        spec["timing"]["conflicts"] = []
        with self.assertRaisesRegex(PipelineError, "explicit conflicts"):
            build_pipeline(spec, TEMPLATE, ROLES)

    def test_template_cannot_redirect_author_approval(self):
        template = copy.deepcopy(TEMPLATE)
        template["stages"][0]["author_approver"] = "someone-else"
        with self.assertRaisesRegex(PipelineError, "must be luis-m-minier"):
            build_pipeline(EXAMPLE, template, ROLES)

    def test_completion_requires_files_evidence_and_independent_review(self):
        spec = copy.deepcopy(EXAMPLE)
        pipeline = build_pipeline(spec, TEMPLATE, ROLES)
        task = pipeline["tasks"][0]
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            output = repo / task["output_dir"]
            output.mkdir(parents=True)
            artifacts = []
            for index, kind in enumerate(task["completion_contract"]["required_artifact_kinds"]):
                path = output / f"artifact-{index}.txt"
                path.write_text(kind)
                artifacts.append({"path": path.relative_to(repo).as_posix(), "kind": kind})
            evidence = [{"kind": kind, "detail": f"Verified {kind}"}
                        for kind in task["completion_contract"]["required_evidence_kinds"]]
            record = {
                "status": "approved",
                "agent_id": "episode-worker",
                "artifacts": artifacts,
                "evidence": evidence,
                "review": {
                    "role": task["reviewer_role"], "agent_id": "independent-reviewer",
                    "decision": "approve", "evidence": "Compared every deliverable to the sources"
                },
            }
            self.assertTrue(validate_completion(pipeline, task["id"], record, repo))
            self.assertTrue(validate_completion(pipeline, task["id"], record, repo))
            bad = copy.deepcopy(record)
            bad["review"]["agent_id"] = "episode-worker"
            with self.assertRaisesRegex(PipelineError, "Independent"):
                validate_completion(pipeline, task["id"], bad, repo)
            bad = copy.deepcopy(record)
            bad["evidence"] = bad["evidence"][:-1]
            with self.assertRaisesRegex(PipelineError, "Missing evidence"):
                validate_completion(pipeline, task["id"], bad, repo)

    def test_author_gate_is_not_a_technical_review(self):
        pipeline = build_pipeline(EXAMPLE, TEMPLATE, ROLES)
        with self.assertRaisesRegex(PipelineError, "not approved"):
            validate_author_gate(pipeline, "timing-author-approval")
        arbitrary = copy.deepcopy(EXAMPLE)
        arbitrary["gate_decisions"]["timing-author-approval"] = {
            "status": "approved", "evidence": ["x", "y", "z"]
        }
        with self.assertRaisesRegex(PipelineError, "Timing author approval must contain exactly"):
            build_pipeline(arbitrary, TEMPLATE, ROLES)

        repo, _, _ = self.registry_fixture()
        spec = copy.deepcopy(EXAMPLE)
        selections = {item["id"]: item["choices"][0] for item in spec["timing"]["conflicts"]}
        record_path = "production/runs/s01-11-12-production/tasks/s01-11-12-script-timing/author-decision.json"
        record = {
            "pipeline_id": "s01-11-12", "shots": ["S01-11", "S01-12"],
            "author_id": "luis-m-minier", "timing_task_id": "s01-11-12-script-timing",
            "resolved_conflicts": selections, "approval_reference": "timing-approval-001"
        }
        path = repo / record_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(record, sort_keys=True))
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        spec["gate_decisions"]["timing-author-approval"] = {
            "status": "approved", "author_id": "luis-m-minier",
            "timing_task_id": "s01-11-12-script-timing", "decision_record_path": record_path,
            "decision_record_sha256": digest, "viewed_record": record_path,
            "approval_reference": "timing-approval-001", "resolved_conflicts": selections
        }
        with self.assertRaisesRegex(PipelineError, "remains unresolved"):
            build_pipeline(spec, TEMPLATE, ROLES, repo)
        spec["timing"]["status"] = "resolved"
        approved = build_pipeline(spec, TEMPLATE, ROLES, repo)
        self.assertTrue(validate_author_gate(approved, "timing-author-approval", repo))
        board = next(task for task in approved["tasks"] if task["id"].endswith("-storyboard"))
        self.assertNotIn("timing-author-approval", board["blocked_by_gates"])
        self.assertTrue(approved["canonical_delivery_blocked"])


if __name__ == "__main__":
    unittest.main()
