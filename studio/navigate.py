"""Rebuild a local episode navigator from source records and actual file bytes.

This is an inventory, never an approval or replacement for motion review.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from html import escape
import json
import os
from pathlib import Path
import subprocess
from urllib.parse import quote

from studio.paths import ROOT, load_json, sha256, write_json

TIMELINE = "production/runs/episode1-full-picture/tasks/episode-wiring/timeline.json"
EPISODE = "projects/cemi_episode_01/data/episode.json"


def inspect_file(root, name, expected=None):
    if not name:
        return {"path": None, "state": "unassigned"}
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()):
        return {"path": str(name), "state": "outside_repository"}
    result = {"path": path.relative_to(root).as_posix()}
    if not path.is_file():
        return dict(result, state="missing")
    with path.open("rb") as handle:
        if handle.read(100).startswith(b"version https://git-lfs.github.com/spec/v1"):
            return dict(result, state="lfs_pointer")
    digest = sha256(path)
    return dict(result, state="hash_mismatch" if expected and expected != digest else "present",
                sha256=digest, bytes=path.stat().st_size, expected_sha256=expected)


def audit(root=ROOT, probe=False):
    root = Path(root).resolve()
    episode = load_json(root / EPISODE)
    timeline = load_json(root / TIMELINE)
    saved = {row["shot"]: row for row in timeline["shots"]}
    rows = []
    cursor = 0
    timing_errors = []
    for shot in episode["shots"]:
        row = saved.get(shot["id"], {})
        if shot["start_frame"] != cursor:
            timing_errors.append(shot["id"])
        cursor = shot["start_frame"] + shot["frames"]
        draft = row.get("draft") or {}
        art = row.get("artwork") or {}
        motion = inspect_file(root, draft.get("path"), draft.get("sha256"))
        if probe and motion["state"] in {"present", "hash_mismatch"}:
            try:
                completed = subprocess.run([
                    "ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
                    "-show_entries", "stream=width,height,r_frame_rate,nb_read_frames",
                    "-of", "json", str(root / motion["path"])],
                    capture_output=True, text=True, timeout=120, check=True)
                stream = json.loads(completed.stdout)["streams"][0]
                motion["probe"] = stream
                motion["timing_matches"] = (int(stream["nb_read_frames"]) == shot["frames"]
                                              and stream["r_frame_rate"] == f'{episode["fps"]}/1')
            except (OSError, ValueError, KeyError, IndexError, subprocess.SubprocessError) as exc:
                motion["probe_error"] = str(exc)
        rows.append({"shot": shot["id"], "start_frame": shot["start_frame"],
                     "frames": shot["frames"], "script": shot["script"],
                     "recorded_status": row.get("status", "not_indexed"),
                     "artwork": inspect_file(root, art.get("path"), art.get("sha256")),
                     "motion": motion, "native": inspect_file(root, draft.get("native")),
                     "review": inspect_file(root, draft.get("review")),
                     "spec": f'projects/cemi_episode_01/data/shots/{shot["id"]}.json',
                     "remaining_actions": row.get("missing_or_unvalidated_actions", []),
                     "missing_drawings": row.get("missing_drawings", []),
                     "voice_status": shot.get("voice_status", "unknown")})
    queue_path = root / "production/episode-automation-v1/episode.json"
    queue = load_json(queue_path) if queue_path.exists() else {}
    recovered = []
    for directory in ("production/restored-motion-20261014", "episode-01/build/take-03-restored"):
        for path in sorted((root / directory).glob("*.mp4")):
            item = inspect_file(root, path.relative_to(root))
            item["review_status"] = "reconstructed candidate; original approvals do not transfer"
            if probe and item["state"] == "present":
                try:
                    result = subprocess.run(["ffprobe", "-v", "error", "-count_frames",
                        "-select_streams", "v:0", "-show_entries",
                        "stream=width,height,r_frame_rate,nb_read_frames", "-of", "json", str(path)],
                        capture_output=True, text=True, check=True, timeout=120)
                    item["probe"] = json.loads(result.stdout)["streams"][0]
                except (OSError, ValueError, KeyError, IndexError, subprocess.SubprocessError) as exc:
                    item["probe_error"] = str(exc)
            recovered.append(item)
    return {"generated_at": datetime.now(timezone.utc).isoformat(),
            "truth": "Inventory only. Saved reviews apply to their exact hashes. No final approval is inferred.",
            "sources": {EPISODE: sha256(root / EPISODE), TIMELINE: sha256(root / TIMELINE)},
            "format": {key: episode[key] for key in ("fps", "width", "height")},
            "shot_count": len(rows), "frames": sum(r["frames"] for r in rows),
            "timing_errors": timing_errors,
            "artwork_counts": dict(Counter(r["artwork"]["state"] for r in rows)),
            "motion_counts": dict(Counter(r["motion"]["state"] for r in rows)),
            "recorded_status_counts": dict(Counter(r["recorded_status"] for r in rows)),
            "automation": {key: queue.get(key) for key in ("state", "blocked_shot", "reason")},
            "recovered_candidates": recovered, "shots": rows}


def render_html(report, root, output):
    def link(name, label):
        if not name or not (root / name).exists():
            return escape(label) + " (unavailable)"
        href = quote(os.path.relpath(root / name, output), safe="/")
        return f'<a href="{href}">{escape(label)}</a>'

    cards = []
    for row in report["shots"]:
        links = [link(row["spec"], "Shot spec")]
        for key in ("artwork", "motion", "native", "review"):
            item = row[key]
            links.append(link(item["path"], key.title()) + " — " + escape(item["state"]))
        remaining = "\n".join(str(item) for item in row["remaining_actions"] + row["missing_drawings"])
        cards.append(f'<article id="{row["shot"]}"><h2>{row["shot"]}</h2>'
                     f'<p>{row["frames"]} frames · starts at {row["start_frame"]} · '
                     f'Saved status: {escape(row["recorded_status"])}</p>'
                     f'<p>{"<br>".join(links)}</p><details><summary>Script and remaining work</summary>'
                     f'<pre>{escape(row["script"])}</pre><h3>Recorded unvalidated action / drawings</h3>'
                     f'<pre>{escape(remaining or "See the exact-file review; no final approval inferred.")}</pre>'
                     f'<p>Voice: {escape(row["voice_status"])}</p></details></article>')
    navigation = " · ".join(link(path, label) for path, label in (
        ("START_HERE.md", "Start here"), ("docs/REPOSITORY_MAP.md", "Folder map"),
        ("docs/WORKSPACE.md", "Desktop app"), ("episode-01/WORKFLOW.md", "Approved workflow"),
        ("production/runs", "Production runs")))
    summary = {key: report[key] for key in ("shot_count", "frames", "format", "motion_counts", "artwork_counts", "automation")}
    recovery_links = '<h2>Recovered motion — requires fresh review</h2><ul>' + ''.join(
        '<li>' + link(item["path"], item["path"]) + ' — ' + escape(item["state"]) + '</li>'
        for item in report.get("recovered_candidates", [])) + '</ul>'
    return ('<!doctype html><html lang="en"><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            '<title>Episode 1 navigator</title><style>'
            'body{font:17px system-ui;max-width:1000px;margin:2rem auto;padding:0 1rem;background:#14202b;color:#eee}'
            'a{color:#f0ce83}article{border:1px solid #697880;padding:1rem;margin:1rem 0;border-radius:8px}'
            'pre{white-space:pre-wrap;overflow-wrap:anywhere}input{font:inherit;padding:.7rem;width:90%}'
            '</style><h1>Episode 1 — production navigator</h1><p>' + navigation + '</p>'
            '<p>Work in progress. This page inventories actual local files; it is not a finished episode.</p>'
            '<p>Hash mismatches mean a saved review cannot verify the current video. Restored renders need fresh review.</p>'
            '<pre>' + escape(json.dumps(summary, indent=2)) + '</pre>' + recovery_links +
            '<label for="search">Find a shot, character, action or file status</label><p>'
            '<input id="search" type="search" placeholder="S01-03, Amaia, hash_mismatch…"></p>'
            + ''.join(cards) + '<script>document.querySelector("#search").addEventListener("input",e=>{'
            'const q=e.target.value.toLowerCase();document.querySelectorAll("article").forEach(a=>'
            'a.hidden=!a.textContent.toLowerCase().includes(q));});</script></html>')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="production/navigation")
    parser.add_argument("--probe", action="store_true", help="decode/count linked video frames with ffprobe")
    args = parser.parse_args(argv)
    output = Path(args.out).resolve()
    report = audit(probe=args.probe)
    output.mkdir(parents=True, exist_ok=True)
    write_json(output / "inventory.json", report)
    (output / "index.html").write_text(render_html(report, ROOT, output), encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "shots"}, indent=2))
    print(f'Navigator: {output / "index.html"}')
