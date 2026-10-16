from pathlib import Path
import unittest
import subprocess
from unittest.mock import patch

from production import workspace


class WorkspaceSnapshotTests(unittest.TestCase):
    def test_timeout_bytes_are_retained_and_job_is_released(self):
        jobs = {"timeout-test": {"state": "queued"}}
        error = subprocess.TimeoutExpired(["render"], 3600, output=b"frames rendered", stderr=b"\xfferror")
        with patch.object(workspace, "JOBS", jobs), \
             patch.object(workspace, "ACTIVE_JOB", "timeout-test"), \
             patch.object(workspace.subprocess, "run", side_effect=error):
            workspace._job_worker("timeout-test", ["render"])
            self.assertEqual("failed", jobs["timeout-test"]["state"])
            self.assertIn("frames rendered", jobs["timeout-test"]["output"])
            self.assertIn("60-minute", jobs["timeout-test"]["output"])
            self.assertIsNone(workspace.ACTIVE_JOB)

    def test_snapshot_exposes_episode_specs_and_generation_gate(self):
        data = workspace.snapshot()
        self.assertEqual(128, len(data["scene_specs"]))
        self.assertEqual(128, data["episode"]["shot_count"])
        self.assertFalse(data["generation"]["enabled"])
        self.assertEqual(0, data["generation"]["cap_usd"])
        shot = next(item for item in data["scene_specs"] if item["id"] == "S01-02")
        self.assertEqual("assets/keyframes/S01-02.png", shot["preview"])
        self.assertIn("canoes", shot["action"])

    def test_paused_or_unknown_runs_cannot_start(self):
        with self.assertRaisesRegex(ValueError, "paused"):
            workspace.start_job("run", {"run": "episode1-amaia-finish"})
        with self.assertRaisesRegex(ValueError, "existing production run"):
            workspace.start_job("run", {"run": "not-a-run"})

    def test_run_dispatch_is_hard_limited_to_one_task(self):
        with patch.object(workspace, "build_snapshot", return_value={"runs": {"runs": [
                {"id": "test-run", "paused": False}]}}), \
             patch.object(workspace.threading, "Thread") as thread, \
             patch.object(workspace, "ACTIVE_JOB", None):
            job = workspace.start_job("run", {"run": "test-run"})
            command = thread.call_args.kwargs["args"][1]
            self.assertEqual("queued", job["state"])
            self.assertIn("--max-tasks", command)
            self.assertEqual("1", command[command.index("--max-tasks") + 1])

    def test_project_file_reads_real_local_assets_and_rejects_escape(self):
        preview = workspace.project_file("assets/keyframes/S01-02.png")
        self.assertTrue(preview.is_file())
        self.assertTrue(preview.is_relative_to(Path(workspace.PROJECT).resolve()))
        with self.assertRaisesRegex(ValueError, "escapes"):
            workspace.project_file("../../AGENTS.md")
        with self.assertRaisesRegex(ValueError, "Unsupported"):
            workspace.project_file("data/episode.py")


if __name__ == "__main__":
    unittest.main()
