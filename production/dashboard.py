#!/usr/bin/env python3
"""Read-only local production dashboard for AnimeStudio.

The server deliberately exposes a small, normalized summary instead of raw
repository files. It never writes production state and binds to loopback by
default.
"""

from __future__ import annotations

import argparse
import ipaddress
import json
import mimetypes
import socket
from collections import Counter
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

try:
    from production.asset_registry import AssetRegistry, AssetRegistryError
except ModuleNotFoundError:  # Direct execution from the production directory.
    from asset_registry import AssetRegistry, AssetRegistryError


REPO_ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = Path(__file__).resolve().parent / "dashboard_assets"
STATIC_FILES = {"/": "index.html", "/index.html": "index.html", "/app.js": "app.js", "/style.css": "style.css"}
FINAL_STATES = {"approved", "rejected", "author-approved", "author-rejected", "blocked", "cancelled"}


def _read_json(path: Path, errors: list[str]) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"Could not read {path.relative_to(REPO_ROOT)}: {exc}")
        return None


def _rel(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()


def _classification(asset: dict[str, Any]) -> str:
    text = " ".join(str(asset.get(key, "")) for key in ("status", "review", "path", "approval_status")).lower()
    if "reject" in text:
        return "rejected"
    if any(word in text for word in ("unapproved", "exploratory", "needs review", "not approved")):
        return "unapproved"
    if "approved" in text and "not approved" not in text and "unapproved" not in text:
        return "approved"
    if any(word in text for word in ("keyframe only", "partial", "incomplete", "not complete")):
        return "partial"
    return "unreviewed"


def _legacy_assets(errors: list[str]) -> dict[str, Any]:
    """Load the old inventory without inferring a production approval."""
    path = REPO_ROOT / "projects" / "cemi_episode_01" / "data" / "art_inventory.json"
    records: list[dict[str, Any]] = []
    raw = _read_json(path, errors)
    items = raw if isinstance(raw, list) else raw.get("assets", raw.get("items", [])) if isinstance(raw, dict) else []
    for item in items:
        if not isinstance(item, dict):
            continue
        state = _classification(item)
        records.append({
            "id": str(item.get("id") or item.get("name") or item.get("path") or "unnamed"),
            "version": None, "sha256": None, "path": str(item.get("path", "")),
            "review": str(item.get("review") or item.get("notes") or item.get("status") or "No review recorded"),
            "classification": state, "state": state, "kind": "legacy-inventory",
            "mode": "unknown", "shots": [str(item["id"])] if item.get("id") else [], "final_uses": [],
        })
    counts = Counter(record["state"] for record in records)
    return {"source_type": "legacy-inventory", "sources": [_rel(path)] if path.is_file() else [],
            "event_count": 0, "count": len(records), "counts": dict(sorted(counts.items())),
            "final_uses": [], "items": records}


def _load_assets(errors: list[str]) -> dict[str, Any]:
    """Replay the canonical event registry, falling back to the legacy inventory."""
    registry_path = REPO_ROOT / "production" / "asset-registry.json"
    if not registry_path.is_file():
        return _legacy_assets(errors)
    try:
        registry = AssetRegistry(REPO_ROOT)
        registry.verify(check_files=True)
        summary = registry.summary()
    except (AssetRegistryError, OSError, json.JSONDecodeError) as exc:
        errors.append(f"Could not verify production/asset-registry.json: {exc}")
        return {"source_type": "event-registry-error", "sources": [_rel(registry_path)],
                "event_count": 0, "count": 0, "counts": {}, "final_uses": [], "items": []}

    uses_by_ref: dict[tuple[str, int], list[str]] = {}
    safe_uses = []
    for use in summary.get("final_uses", []):
        if not isinstance(use, dict):
            continue
        asset_id, version = str(use.get("asset_id", "")), int(use.get("version", 0) or 0)
        use_id = str(use.get("use_id", ""))
        uses_by_ref.setdefault((asset_id, version), []).append(use_id)
        safe_uses.append({"use_id": use_id, "asset_id": asset_id, "version": version})

    records = []
    for item in summary.get("assets", []):
        if not isinstance(item, dict):
            continue
        asset_id, version = str(item.get("asset_id", "unnamed")), int(item.get("version", 0) or 0)
        state = str(item.get("state", "unknown"))
        records.append({
            "id": asset_id, "version": version, "sha256": str(item.get("sha256", "")),
            "path": str(item.get("path", "")), "review": f"Registry state: {state}",
            "classification": state, "state": state, "kind": str(item.get("kind", "unknown")),
            "mode": str(item.get("mode", "unknown")),
            "shots": [str(shot) for shot in item.get("shots", [])],
            "final_uses": uses_by_ref.get((asset_id, version), []),
        })
    counts = Counter(record["state"] for record in records)
    return {"source_type": "event-registry", "sources": [_rel(registry_path)],
            "event_count": int(summary.get("event_count", 0) or 0), "count": len(records),
            "counts": dict(sorted(counts.items())), "final_uses": safe_uses, "items": records}


def _safe_host_header(value: str | None) -> bool:
    """Accept only explicit localhost or literal loopback Host authorities."""
    if not value or any(character.isspace() for character in value) or "," in value or "@" in value:
        return False
    try:
        authority = urlsplit(f"//{value}")
        hostname = authority.hostname
        _ = authority.port  # Force malformed ports to raise.
    except ValueError:
        return False
    if (not hostname or authority.username is not None or authority.password is not None
            or authority.path or authority.query or authority.fragment):
        return False
    if hostname.lower() == "localhost":
        return True
    try:
        return ipaddress.ip_address(hostname).is_loopback
    except ValueError:
        return False


def _load_episode(errors: list[str]) -> dict[str, Any]:
    path = REPO_ROOT / "projects" / "cemi_episode_01" / "data" / "episode.json"
    raw = _read_json(path, errors) or {}
    shots = raw.get("shots", []) if isinstance(raw, dict) else []
    normalized = []
    status_counts: Counter[str] = Counter()
    animation_counts: Counter[str] = Counter()
    voice_counts: Counter[str] = Counter()
    for shot in shots:
        if not isinstance(shot, dict):
            continue
        keyframes = shot.get("keyframes") if isinstance(shot.get("keyframes"), list) else []
        status = str(shot.get("status", "unknown"))
        animation = str(shot.get("animation_status", "unknown"))
        voice = str(shot.get("voice_status", "unknown"))
        status_counts[status] += 1
        animation_counts[animation] += 1
        voice_counts[voice] += 1
        normalized.append(
            {
                "id": str(shot.get("id", "unknown")),
                "frames": int(shot.get("frames", 0) or 0),
                "status": status,
                "animation_status": animation,
                "voice_status": voice,
                "keyframes": len(keyframes),
            }
        )
    covered = sum(1 for shot in normalized if shot["keyframes"] > 0)
    missing = [shot["id"] for shot in normalized if shot["keyframes"] == 0]
    return {
        "source": _rel(path),
        "fps": raw.get("fps", 0),
        "width": raw.get("width", 0),
        "height": raw.get("height", 0),
        "body_frames": raw.get("body_frames", 0),
        "shot_count": len(normalized),
        "keyframe_covered_shots": covered,
        "missing_keyframe_count": len(missing),
        "missing_keyframe_shots": missing,
        "status_counts": dict(sorted(status_counts.items())),
        "animation_counts": dict(sorted(animation_counts.items())),
        "voice_counts": dict(sorted(voice_counts.items())),
        "shots": normalized,
    }


def _load_roles(errors: list[str]) -> dict[str, Any]:
    path = REPO_ROOT / "production" / "roles.json"
    raw = _read_json(path, errors) or {}
    roles = []
    if isinstance(raw, dict):
        for role_id, role in raw.items():
            if not isinstance(role, dict):
                continue
            roles.append(
                {
                    "id": role_id,
                    "name": role_id.replace("-", " ").title(),
                    "duties": str(role.get("duties", "")),
                    "reviewer": str(role.get("reviewer", "Unassigned")),
                    "skill": str(role.get("skill", "")),
                }
            )
    return {"source": _rel(path), "count": len(roles), "roles": roles}


def _load_runs(errors: list[str]) -> dict[str, Any]:
    runs = []
    state_counts: Counter[str] = Counter()
    approvals = []
    root = REPO_ROOT / "production" / "runs"
    for path in sorted(root.glob("*/ledger.json")) if root.is_dir() else []:
        raw = _read_json(path, errors)
        if not isinstance(raw, dict):
            continue
        tasks = []
        raw_tasks = raw.get("tasks", {})
        iterable = raw_tasks.items() if isinstance(raw_tasks, dict) else []
        for task_id, task in iterable:
            if not isinstance(task, dict):
                continue
            state = str(task.get("state", "unknown"))
            state_counts[state] += 1
            task_view = {
                "id": str(task_id),
                "role": str(task.get("role", "unassigned")),
                "state": state,
                "shots": task.get("shots", []),
                "depends_on": task.get("depends_on", []),
                "objective": str(task.get("objective", "")),
            }
            tasks.append(task_view)
            if state in {"approved", "rejected", "author-approved", "author-rejected"}:
                approvals.append({"run": str(raw.get("run", path.parent.name)), "task": str(task_id), "decision": state})
        for event in raw.get("events", []):
            if isinstance(event, dict) and event.get("action") in {"review", "author-review", "approve", "reject"}:
                approvals.append(
                    {
                        "run": str(raw.get("run", path.parent.name)),
                        "task": str(event.get("task_id", "unknown")),
                        "decision": str(event.get("decision", event.get("action"))),
                        "reviewer": str(event.get("reviewer_role", "")),
                    }
                )
        runs.append(
            {
                "id": str(raw.get("run", path.parent.name)),
                "source": _rel(path),
                "paused": bool(raw.get("paused", False)),
                "pause_reason": str(raw.get("pause_reason", "")),
                "task_count": len(tasks),
                "open_task_count": sum(1 for task in tasks if task["state"] not in FINAL_STATES),
                "tasks": tasks,
            }
        )
    return {
        "count": len(runs),
        "paused_count": sum(1 for run in runs if run["paused"]),
        "task_state_counts": dict(sorted(state_counts.items())),
        "approvals": approvals,
        "runs": runs,
    }


def _load_plans(errors: list[str]) -> list[dict[str, str]]:
    candidates = [
        REPO_ROOT / "production" / "pipeline_plan.json",
        REPO_ROOT / "production" / "pipeline.json",
        REPO_ROOT / "projects" / "cemi_episode_01" / "data" / "pipeline_plan.json",
    ]
    plans = []
    for path in candidates:
        if not path.is_file():
            continue
        raw = _read_json(path, errors)
        plans.append({"source": _rel(path), "status": str(raw.get("status", "present")) if isinstance(raw, dict) else "present"})
    return plans


def build_snapshot() -> dict[str, Any]:
    """Return the complete dashboard payload without mutating the repository."""
    errors: list[str] = []
    episode = _load_episode(errors)
    assets = _load_assets(errors)
    roles = _load_roles(errors)
    runs = _load_runs(errors)
    return {
        "project": "Heralds of the Cemí — Episode 1",
        "mode": "read-only",
        "truth_notice": "Plans, tests, atlases, keyframes and successful exports are not finished animation. Technical review and author creative approval are separate gates.",
        "author_approval": "No asset or shot is author-approved unless that decision is explicitly recorded. Absence of rejection is not approval.",
        "episode": episode,
        "assets": assets,
        "roles": roles,
        "runs": runs,
        "plans": _load_plans(errors),
        "errors": errors,
    }


class DashboardHandler(BaseHTTPRequestHandler):
    server_version = "AnimeStudioDashboard/1.0"

    def _send(self, payload: bytes, content_type: str, status: HTTPStatus = HTTPStatus.OK) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(payload)

    def _allow_request_host(self) -> bool:
        if _safe_host_header(self.headers.get("Host")):
            return True
        self._send(b'{"error":"Host header must name localhost or a loopback IP address"}',
                   "application/json; charset=utf-8", HTTPStatus.MISDIRECTED_REQUEST)
        return False

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        if not self._allow_request_host():
            return
        raw_path = unquote(urlsplit(self.path).path)
        if ".." in Path(raw_path).parts or "\\" in raw_path or "\x00" in raw_path:
            self._send(b'{"error":"invalid path"}', "application/json; charset=utf-8", HTTPStatus.BAD_REQUEST)
            return
        if raw_path == "/api/studio":
            payload = json.dumps(build_snapshot(), ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            self._send(payload, "application/json; charset=utf-8")
            return
        if raw_path == "/health":
            self._send(b'{"status":"ok","mode":"read-only"}', "application/json; charset=utf-8")
            return
        filename = STATIC_FILES.get(raw_path)
        if filename is None:
            self._send(b"Not found", "text/plain; charset=utf-8", HTTPStatus.NOT_FOUND)
            return
        candidate = (ASSET_ROOT / filename).resolve()
        try:
            candidate.relative_to(ASSET_ROOT.resolve())
        except ValueError:
            self._send(b"Not found", "text/plain; charset=utf-8", HTTPStatus.NOT_FOUND)
            return
        try:
            payload = candidate.read_bytes()
        except OSError:
            self._send(b"Not found", "text/plain; charset=utf-8", HTTPStatus.NOT_FOUND)
            return
        mime = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
        self._send(payload, f"{mime}; charset=utf-8" if mime.startswith(("text/", "application/javascript")) else mime)

    def do_POST(self) -> None:  # noqa: N802 - explicit read-only denial
        if not self._allow_request_host():
            return
        self._send(b'{"error":"dashboard is read-only"}', "application/json; charset=utf-8", HTTPStatus.METHOD_NOT_ALLOWED)

    do_PUT = do_POST
    do_PATCH = do_POST
    do_DELETE = do_POST

    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"dashboard: {self.address_string()} - {fmt % args}")


def _loopback_host(host: str) -> tuple[str, bool]:
    """Validate a literal loopback address without relying on DNS."""
    if host.lower() == "localhost":
        return "127.0.0.1", False
    try:
        address = ipaddress.ip_address(host)
    except ValueError as exc:
        raise ValueError("Dashboard host must be localhost or a loopback IP address") from exc
    if not address.is_loopback:
        raise ValueError("Dashboard refuses non-loopback bind addresses")
    return str(address), address.version == 6


def make_server(host: str = "127.0.0.1", port: int = 8765) -> ThreadingHTTPServer:
    host, ipv6 = _loopback_host(host)
    if ipv6:
        class LoopbackIPv6Server(ThreadingHTTPServer):
            address_family = socket.AF_INET6

        return LoopbackIPv6Server((host, port), DashboardHandler)
    return ThreadingHTTPServer((host, port), DashboardHandler)


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve the read-only AnimeStudio production dashboard.")
    parser.add_argument("--host", default="127.0.0.1", help="Loopback bind host only (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8765, help="Bind port (default: 8765)")
    parser.add_argument("--json", action="store_true", help="Print the normalized snapshot and exit")
    args = parser.parse_args()
    if args.json:
        print(json.dumps(build_snapshot(), ensure_ascii=False, indent=2))
        return
    try:
        server = make_server(args.host, args.port)
    except ValueError as exc:
        parser.error(str(exc))
    display_host = f"[{server.server_address[0]}]" if ":" in server.server_address[0] else server.server_address[0]
    print(f"AnimeStudio dashboard: http://{display_host}:{server.server_port} (read-only)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
