import http.client
import hashlib
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from production import dashboard
from production.asset_registry import AssetRegistry


class DashboardSnapshotTests(unittest.TestCase):
    def test_snapshot_reports_canonical_episode_without_claiming_animation(self):
        data = dashboard.build_snapshot()
        self.assertEqual(data["mode"], "read-only")
        self.assertEqual(data["episode"]["shot_count"], 128)
        self.assertEqual(data["episode"]["keyframe_covered_shots"], 64)
        self.assertEqual(data["episode"]["missing_keyframe_count"], 64)
        self.assertGreaterEqual(data["episode"]["animation_counts"].get("rejected_motion_test", 0), 1)
        self.assertIn("not finished animation", data["truth_notice"])
        self.assertIn("author", data["author_approval"].lower())

    def test_snapshot_tracks_paused_runs_tasks_assets_and_roles(self):
        data = dashboard.build_snapshot()
        self.assertGreaterEqual(data["runs"]["paused_count"], 1)
        self.assertGreaterEqual(sum(run["task_count"] for run in data["runs"]["runs"]), 1)
        self.assertGreaterEqual(data["assets"]["count"], 1)
        self.assertGreaterEqual(data["roles"]["count"], 17)

    def test_default_event_registry_exposes_version_hash_state_and_final_use(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            art = root / "art" / "pose.png"
            art.parent.mkdir(parents=True)
            art.write_bytes(b"dashboard registry fixture")
            registry = AssetRegistry(root)
            provenance = {"origin": "test", "creator": "test", "license": "project-owned", "source_assets": [], "notes": "Fixture"}
            continuity = {"character_ids": ["beheto"], "costume_ids": ["river-v1"], "prop_ids": ["drum-v1"], "time": "night", "location": "canoe"}
            registry.register(asset_id="s01-11.pose", path="art/pose.png", kind="replacement-cel", mode="work-in-progress", shots=["S01-11"], provenance=provenance, continuity=continuity, at="2026-10-12T16:00:00Z")
            registry.transition("s01-11.pose", 1, "submitted", at="2026-10-12T16:00:00Z")
            digest = hashlib.sha256(art.read_bytes()).hexdigest()
            technical = {"approval_id": "tech-pose-v1", "type": "technical", "asset_id": "s01-11.pose", "version": 1, "asset_sha256": digest, "approver_id": "reviewer", "approver_role": "animation-supervisor", "evidence": "Frame review", "at": "2026-10-12T16:00:00Z"}
            author = {"approval_id": "author-pose-v1", "type": "author", "asset_id": "s01-11.pose", "version": 1, "asset_sha256": digest, "approver_id": "luis-m-minier", "approver_role": "author", "evidence": "Exact digest approved", "at": "2026-10-12T16:00:00Z"}
            registry.transition("s01-11.pose", 1, "technical-approved", technical, "2026-10-12T16:00:00Z")
            registry.transition("s01-11.pose", 1, "author-approved", author, "2026-10-12T16:00:00Z")
            with patch.object(dashboard, "REPO_ROOT", root):
                author_approved = dashboard._load_assets([])
            self.assertEqual("author-approved", author_approved["items"][0]["state"])
            self.assertEqual(1, author_approved["counts"]["author-approved"])
            registry.transition("s01-11.pose", 1, "canonical", at="2026-10-12T16:00:00Z")
            registry.link_final("picture-lock.s01-11", "s01-11.pose", 1, ["S01-11"], "2026-10-12T16:00:00Z")
            with patch.object(dashboard, "REPO_ROOT", root):
                assets = dashboard._load_assets([])
            self.assertEqual("event-registry", assets["source_type"])
            self.assertEqual("production/asset-registry.json", assets["sources"][0])
            self.assertEqual("canonical", assets["items"][0]["state"])
            self.assertEqual(1, assets["items"][0]["version"])
            self.assertEqual(hashlib.sha256(art.read_bytes()).hexdigest(), assets["items"][0]["sha256"])
            self.assertEqual(["picture-lock.s01-11"], assets["items"][0]["final_uses"])

    def test_tampered_registered_file_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            art = root / "art" / "pose.png"
            art.parent.mkdir(parents=True)
            art.write_bytes(b"registered bytes")
            registry = AssetRegistry(root)
            registry.register(
                asset_id="s01-11.pose", path="art/pose.png", kind="replacement-cel",
                mode="work-in-progress", shots=["S01-11"],
                provenance={"origin": "test", "creator": "test", "license": "project-owned", "source_assets": [], "notes": "Fixture"},
                continuity={"character_ids": ["beheto"], "costume_ids": ["river-v1"], "prop_ids": ["drum-v1"], "time": "night", "location": "canoe"},
                at="2026-10-12T16:00:00Z",
            )
            art.write_bytes(b"tampered after registration")
            errors = []
            with patch.object(dashboard, "REPO_ROOT", root):
                assets = dashboard._load_assets(errors)
            self.assertEqual("event-registry-error", assets["source_type"])
            self.assertEqual(0, assets["count"])
            self.assertEqual([], assets["items"])
            self.assertRegex(errors[0], "hash mismatch")


class DashboardServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = dashboard.make_server("127.0.0.1", 0)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def request(self, method, path, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        connection.request(method, path, headers=headers or {})
        response = connection.getresponse()
        payload = response.read()
        headers = dict(response.getheaders())
        connection.close()
        return response.status, headers, payload

    def test_api_returns_safe_json(self):
        status, headers, payload = self.request("GET", "/api/studio")
        self.assertEqual(status, 200)
        self.assertIn("application/json", headers["Content-Type"])
        self.assertEqual(json.loads(payload)["mode"], "read-only")
        self.assertNotIn(str(dashboard.REPO_ROOT).encode(), payload)
        self.assertNotIn(b'"agent_id"', payload)

    def test_static_ui_and_security_headers(self):
        status, headers, payload = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn(b"Production Desk", payload)
        self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
        self.assertIn("default-src 'self'", headers["Content-Security-Policy"])

    def test_traversal_and_mutations_are_denied(self):
        self.assertIn(self.request("GET", "/../AGENTS.md")[0], (400, 404))
        self.assertIn(self.request("GET", "/%2e%2e/AGENTS.md")[0], (400, 404))
        self.assertEqual(self.request("POST", "/api/studio")[0], 405)

    def test_nonloopback_bind_is_refused(self):
        for host in ("0.0.0.0", "192.168.1.10", "example.com"):
            with self.subTest(host=host), self.assertRaisesRegex(ValueError, "loopback"):
                dashboard.make_server(host, 0)

    def test_nonloopback_host_header_is_rejected(self):
        for host in ("evil.example", "192.168.1.10", "0.0.0.0", "localhost.evil.example"):
            with self.subTest(host=host):
                status, _, payload = self.request("GET", "/api/studio", {"Host": host})
                self.assertEqual(421, status)
                self.assertIn(b"loopback", payload)
        for host in ("localhost", f"127.0.0.1:{self.server.server_port}", "[::1]:8765"):
            with self.subTest(host=host):
                self.assertEqual(200, self.request("GET", "/health", {"Host": host})[0])


if __name__ == "__main__":
    unittest.main()
