"""Local project-data and bounded job helpers for the AnimeStudio desktop UI."""
from __future__ import annotations

import secrets
import subprocess
import sys
import threading
import time
from pathlib import Path

from production.dashboard import REPO_ROOT, build_snapshot, _safe_host_header
from studio.paths import PROJECT, load_json
from studio import policy

JOBS: dict[str, dict] = {}
LOCK = threading.RLock()
ACTIVE_JOB: str | None = None


def _read_specs() -> list[dict]:
    output = []
    episode_rows = {s["id"]: s for s in load_json(PROJECT / "data" / "episode.json")["shots"]}
    for path in sorted((PROJECT / "data" / "shots").glob("*.json")):
        try:
            spec = load_json(path)
        except (OSError, ValueError):
            continue
        shot_id = str(spec.get("id", path.stem))
        episode_row = episode_rows.get(shot_id, {})
        keyframes = [str(k) for k in episode_row.get("keyframes", [])]
        preview = next((k for k in keyframes if (PROJECT / k).is_file()), None)
        output.append({
            "id": shot_id,
            "frames": int(spec.get("frames", episode_row.get("frames", 0)) or 0),
            "fps": int(spec.get("fps", 24) or 24),
            "stage": str(spec.get("stage", "template")),
            "status": str(spec.get("status", episode_row.get("status", "unknown"))),
            "animation_status": str(spec.get("animation_status", episode_row.get("animation_status", "unknown"))),
            "action": str(spec.get("action", "")),
            "camera": str(spec.get("camera_note", "")),
            "truth": str(spec.get("truth", "")),
            "keyframes": keyframes,
            "preview": preview,
            "spec": path.relative_to(REPO_ROOT).as_posix(),
            "render": _latest_render(shot_id),
        })
    return output


def _latest_render(shot_id: str) -> str | None:
    directory = PROJECT / "renders" / "workspace"
    candidates = sorted(directory.glob(f"{shot_id}-*.mp4"), key=lambda path: path.stat().st_mtime, reverse=True) if directory.is_dir() else []
    return candidates[0].relative_to(PROJECT).as_posix() if candidates else None


def snapshot() -> dict:
    data = build_snapshot()
    data["scene_specs"] = _read_specs()
    generation = policy.load().get("generation", {})
    data["generation"] = {
        "enabled": bool(generation.get("enabled", False)),
        "spent_usd": policy.spent(),
        "cap_usd": float(generation.get("max_total_usd", 0) or 0),
    }
    with LOCK:
        data["jobs"] = [dict(job) for job in JOBS.values()]
    return data


def project_file(relative: str) -> Path:
    candidate = (PROJECT / relative).resolve()
    if not candidate.is_relative_to(PROJECT.resolve()):
        raise ValueError("Project path escapes the episode workspace.")
    if candidate.suffix.lower() not in {".json", ".png", ".jpg", ".jpeg", ".webp", ".mp4", ".mkv"}:
        raise ValueError("Unsupported project file type.")
    if not candidate.is_file():
        raise ValueError("Project file was not found.")
    return candidate


def _job_worker(job_id: str, command: list[str]) -> None:
    global ACTIVE_JOB
    with LOCK:
        JOBS[job_id]["state"] = "running"
        JOBS[job_id]["started_at"] = time.time()
    try:
        result = subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True,
                                timeout=60 * 60, check=False)
        with LOCK:
            JOBS[job_id].update(state="succeeded" if result.returncode == 0 else "failed",
                                returncode=result.returncode,
                                output=(result.stdout + result.stderr)[-16000:])
    except subprocess.TimeoutExpired as exc:
        # TimeoutExpired may contain bytes even when run(text=True) was used.
        output = "".join(part.decode("utf-8", errors="replace") if isinstance(part, bytes)
                         else part or "" for part in (exc.stdout, exc.stderr))
        with LOCK:
            JOBS[job_id].update(state="failed", returncode=None, output=str(output)[-16000:] + "\nJob exceeded the 60-minute limit.")
    except OSError as exc:
        with LOCK:
            JOBS[job_id].update(state="failed", returncode=None, output=str(exc))
    finally:
        with LOCK:
            JOBS[job_id]["finished_at"] = time.time()
            ACTIVE_JOB = None


def start_job(kind: str, payload: dict) -> dict:
    global ACTIVE_JOB
    data = build_snapshot()
    if kind == "run":
        run_id = str(payload.get("run", ""))
        run = next((item for item in data["runs"]["runs"] if item["id"] == run_id), None)
        if run is None:
            raise ValueError("Select an existing production run.")
        if run["paused"]:
            raise ValueError("This run is paused. Resolve its recorded blockers and resume it explicitly in the CLI.")
        command = [sys.executable, "-m", "studio", "run", "--run", run_id, "--max-tasks", "1"]
        if payload.get("dry_run") is True:
            command.append("--dry-run")
        label = f"{'Dry run' if payload.get('dry_run') is True else 'Run one task'} · {run_id}"
    elif kind == "render":
        shot_id = str(payload.get("shot", ""))
        if not shot_id.isascii() or not shot_id.replace("-", "").isalnum():
            raise ValueError("Invalid shot ID.")
        spec = PROJECT / "data" / "shots" / f"{shot_id}.json"
        if not spec.is_file():
            raise ValueError("Shot spec was not found.")
        out_dir = PROJECT / "renders" / "workspace"
        out_dir.mkdir(parents=True, exist_ok=True)
        output = out_dir / f"{shot_id}-{time.strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(3)}.mp4"
        command = [sys.executable, "-m", "studio", "render", str(spec.relative_to(REPO_ROOT)),
                   "--out", str(output.relative_to(REPO_ROOT)), "--draft", "--quality", "draft", "--burn"]
        label = f"Draft render · {shot_id}"
    else:
        raise ValueError("Unknown workspace action.")

    with LOCK:
        if ACTIVE_JOB is not None:
            raise ValueError("A workspace job is already running. Wait for it to finish before starting another.")
        job_id = secrets.token_hex(8)
        JOBS[job_id] = {"id": job_id, "kind": kind, "label": label, "state": "queued",
                        "created_at": time.time(), "output": ""}
        ACTIVE_JOB = job_id
    threading.Thread(target=_job_worker, args=(job_id, command), daemon=True).start()
    return dict(JOBS[job_id])


def main(argv: list[str] | None = None) -> None:
    from production.desktop_workspace import main as desktop_main
    desktop_main(argv)
