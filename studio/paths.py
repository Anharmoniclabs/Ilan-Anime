"""Repository locations and small shared helpers."""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "projects" / "cemi_episode_01"
EPISODE = PROJECT / "data" / "episode.json"
POLICY = ROOT / "production" / "policy.json"
FPS = 24


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, data):
    """Atomic JSON write (temp file + rename)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".tmp-", suffix=".json", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)
    return path


def sha256(path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def rel(path) -> str:
    """Repository-relative POSIX path (absolute input allowed)."""
    path = Path(path).resolve()
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def resolve(path, base: Path | None = None) -> Path:
    """Resolve a spec path: absolute, else relative to ``base``, else to the repo."""
    path = Path(path)
    if path.is_absolute():
        return path
    if base is not None and (base / path).exists():
        return base / path
    if (PROJECT / path).exists():
        return PROJECT / path
    return ROOT / path


def timecode(frame: int, fps: int = FPS) -> str:
    seconds, frames = divmod(int(frame), fps)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}:{frames:02d}"


def episode():
    return load_json(EPISODE)
