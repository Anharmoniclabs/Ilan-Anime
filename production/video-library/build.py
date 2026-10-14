"""Build a local, hash-checked browser for the episode video files already on disk."""
from __future__ import annotations

import hashlib
import html
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "production/video-library"

# Originals and useful shot renders only. Duplicate imported copies and transcoded
# queue copies are deliberately omitted; their source files remain untouched.
ITEMS = [
    ("S00-01", "Opening sigil", "episode draft", "production/episode-first-pass/opening/S00-01.mp4"),
    ("S00-02", "Opening title card", "episode draft", "production/episode-first-pass/opening/S00-02.mp4"),
    ("S15-09", "Ending loop", "exploratory episode draft", "production/episode-first-pass/ending/S15-09-review.mp4"),
    ("S01-01", "User supplied paddle take", "motion review pending", "projects/cemi_episode_01/renders/minimax/S01-01-user-take-01.mp4"),
    ("S01-01 → S01-02", "Paddle-to-canoe transition", "transition experiment", "projects/cemi_episode_01/renders/minimax/S01-01-to-S01-02-user-transition-take-01.mp4"),
    ("S01-02", "Downloaded canoe motion", "3-second exploratory test; review flagged no character acting", "production/video-jobs/s01-02-test-v1/downloads/c0ea6d285b6fd03edea99f7c7edde0ce323e578d862251fd7a70b519fdfeb921/h3-1791842766679.mp4"),
    ("S01-02", "Canoe test review render", "3-second review copy", "production/video-jobs/s01-02-test-v1/review.mp4"),
    ("S00-01 + S00-02", "Opening two-shot assembly", "9-second draft assembly", "production/episode-first-pass/opening/opening-picture-review.mp4"),
    ("Unassigned", "Bell motion test", "rejected prototype; comparison only", "projects/cemi_episode_01/renders/Bell_motion_test.mp4"),
    ("Unassigned", "Cemí current-turns motion test", "rejected prototype; comparison only", "projects/cemi_episode_01/renders/Cemi_SC0_Current_Turns_motion_test.mp4"),
]


def metadata(path: Path) -> dict:
    info = json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration:stream=codec_name,width,height,r_frame_rate,nb_frames",
        "-of", "json", str(path),
    ], text=True))
    stream = next(s for s in info["streams"] if s.get("codec_name"))
    return {
        "duration_seconds": round(float(info["format"]["duration"]), 3),
        "width": stream.get("width"), "height": stream.get("height"),
        "fps": stream.get("r_frame_rate"), "video_codec": stream.get("codec_name"),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    records = []
    for shot, label, status, rel in ITEMS:
        path = ROOT / rel
        if not path.is_file():
            raise SystemExit(f"Missing video; refusing to build a partial index: {rel}")
        records.append({"shot": shot, "label": label, "status": status,
                        "path": rel, **metadata(path)})

    (OUT / "manifest.json").write_text(json.dumps({
        "version": 1,
        "truth": "Local video inventory. Draft and experiment labels are not approval.",
        "videos": records,
    }, indent=2) + "\n")

    cards = []
    by_shot: dict[str, list[dict]] = {}
    for item in records:
        by_shot.setdefault(item["shot"], []).append(item)
        src = "../" + item["path"]
        desc = (f'{item["duration_seconds"]} s · {item["width"]}×{item["height"]} · '
                f'{item["fps"]} fps · SHA-256 {item["sha256"][:16]}…')
        cards.append(
            f'<article><h2>{html.escape(item["shot"])} · {html.escape(item["label"])}</h2>'
            f'<p class="state">{html.escape(item["status"])}</p>'
            f'<video controls preload="metadata" src="{html.escape(src)}"></video>'
            f'<p>{html.escape(desc)} · <a href="{html.escape(src)}">Open original file</a></p></article>')

    for shot, items in by_shot.items():
        folder = ROOT / "production/scene-folders-v1" / shot.replace(" → ", "-").replace(" + ", "-")
        if folder.is_dir():
            refs = [{k: item[k] for k in ("label", "status", "path", "duration_seconds", "sha256")}
                    for item in items]
            (folder / "video-links.json").write_text(json.dumps({"videos": refs}, indent=2) + "\n")

    # Keep ingest pointers alongside the episode queue without changing its
    # paused/review state. The normal recover-clip command owns that transition.
    queue_links = {shot: [{"label": item["label"], "status": item["status"],
                           "path": item["path"], "duration_seconds": item["duration_seconds"],
                           "sha256": item["sha256"]} for item in items]
                   for shot, items in by_shot.items() if shot in {"S01-01", "S01-02", "S00-01", "S00-02", "S15-09"}}
    queue = ROOT / "production/episode-automation-v1"
    if queue.is_dir():
        (queue / "video-links.json").write_text(json.dumps({
            "truth": "Source pointers only. Import through studio episode recover-clip while the coordinator is free.",
            "shots": queue_links,
        }, indent=2) + "\n")

    page = ("<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width'>"
            "<title>Episode video library</title><style>body{font:16px system-ui;background:#14202b;"
            "color:#eee;max-width:1100px;margin:30px auto;padding:0 20px}a{color:#9fd5ff}"
            "article{border-top:1px solid #526270;padding:18px 0}video{width:min(100%,900px);"
            "background:#080b0f}.state{color:#ffd18a}small{color:#bcc6ce}</style>"
            "<h1>Episode video library</h1><p>Each clip is linked to its shot or labeled as an experiment. "
            "Draft status and review notes travel with the entry. Source files are preserved.</p>"
            + "".join(cards))
    (OUT / "index.html").write_text(page)

    gallery = ROOT / "production/episode-image-pack-v2/index.html"
    if gallery.exists():
        text = gallery.read_text()
        link = '<p><a href="../video-library/index.html">Open linked video clips</a></p>'
        if "video-library/index.html" not in text:
            text = text.replace("<h1>Cemí · Updated draft images</h1>",
                                "<h1>Cemí · Updated draft images</h1>" + link)
            gallery.write_text(text)
    print(f"Indexed {len(records)} clips across {len(by_shot)} shot groups")


if __name__ == "__main__":
    main()
