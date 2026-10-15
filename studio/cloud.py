"""ChatGPT-native production handoff for Ilan-Anime.

Produces a source-bound shot packet, accepts actual cloud-created media,
checks its timing, imports it as an exploratory studio layer and refuses to
assemble a scene with missing clips. No Codex, NESSA, provider credentials or
cloud APIs are required to use the handoff. ChatGPT must separately create
real art/video using tools available in the conversation.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from studio.paths import ROOT, load_json, sha256, write_json
from studio.cloud_rig import validate_action

EPISODE = "projects/cemi_episode_01/data/episode.json"
SHOT_INDEX = "production/runs/episode1-anime90s-scenes/shot-index.json"
ART_DIRECTION = "production/art_direction.json"
AUTHOR_DECISIONS = "production/runs/episode1-full-picture/author-decisions.json"
MODES = ("cloud", "local", "hybrid")
SCENE_RE = re.compile(r"S\d{2}(?:-\d{2})?\Z")
SHOT_RE = re.compile(r"S\d{2}-\d{2}\Z")


class CloudError(ValueError):
    pass


def _json(root, relative):
    return load_json(root / relative)


def _hash_sources(root):
    paths = (EPISODE, SHOT_INDEX, ART_DIRECTION, AUTHOR_DECISIONS)
    return {name: sha256(root / name) if (root / name).is_file() else None
            for name in paths}


def _scene_rows(episode, scene):
    if not SCENE_RE.fullmatch(scene):
        raise CloudError("Scene must be S01 or an exact shot such as S01-05")
    rows = [s for s in episode["shots"]
            if (s["id"] == scene if "-" in scene else s["id"].startswith(scene + "-"))]
    if not rows:
        raise CloudError(f"Unknown scene or shot {scene}")
    return rows


def _action(script):
    match = re.search(r"(?m)^- \*\*Action:\*\*\s*(.+)", script)
    return match.group(1).strip() if match else "Read the original script; action not extracted"


def _provenance(root, selected):
    if selected is None:
        return {"state": "missing-reference", "path": None, "sha256": None}
    path = selected.get("path")
    digest = selected.get("sha256")
    available = bool(path and (root / path).is_file())
    actual = sha256(root / path) if available else None
    return {
        "state": "exploratory-reference-not-animation",
        "path": path,
        "sha256": digest,
        "available_in_checkout": available,
        "source_hash_matches": available and actual == digest,
        "dimensions": selected.get("dimensions"),
        "selected_moment": selected.get("selected_moment"),
        "canonical": False,
        "author_approved": False,
    }


def plan(scene, root=ROOT):
    root = Path(root)
    episode = _json(root, EPISODE)
    index = _json(root, SHOT_INDEX)
    selected = {s["shot"]: s for s in index.get("shots", [])}
    rows = _scene_rows(episode, scene)
    contracts = []
    for shot in rows:
        sid = shot["id"]
        constraints = ["Preserve the selected character identities and source/script timing.",
                       "Show real pose changes and separately moving props where action requires them.",
                       "No whole-image warp or still-image pan presented as character acting.",
                       "Do not inherit creative approval from a different revision."]
        if sid == "S01-05":
            constraints += [
                "Rigid pole: preserve length and non-slipping hand positions.",
                "Registered shoulder/elbow/wrist joints: maintain upper/lower arm lengths.",
                "Bell shell and independently moving clapper; rim impact at drawn contact frames.",
                "Do not call 168 frame action complete without inspected full-frame evidence.",
            ]
        contracts.append({
            "shot": sid,
            "start_frame": shot["start_frame"],
            "frames": shot["frames"],
            "end_frame_exclusive": shot["start_frame"] + shot["frames"],
            "fps": episode["fps"],
            "script": shot["script"],
            "required_action": _action(shot["script"]),
            "keyframes": shot.get("keyframes", []),
            "reference": _provenance(root, selected.get(sid)),
            "constraints": constraints,
            "motion_media": "missing-until-ingested",
            "technical_review": "required",
            "author_review": "required",
            "final_eligible": False,
        })
    return {
        "schema": "ilan.chat-cloud.scene.v1",
        "scene": scene,
        "production_mode": "cloud",
        "available_modes": list(MODES),
        "contract": "same episode, selected still index and art-direction files as local/hybrid",
        "fps": episode["fps"],
        "width": episode["width"],
        "height": episode["height"],
        "shot_count": len(rows),
        "frames": sum(s["frames"] for s in rows),
        "seconds": sum(s["frames"] for s in rows) / episode["fps"],
        "source_hashes": _hash_sources(root),
        "shots": contracts,
        "status": "planned-not-rendered",
        "final_eligible": False,
        "note": "An LLM directing images is not a frame renderer. Import real clips and review them before any claim of completion.",
    }


def _folder(root, scene):
    if not SCENE_RE.fullmatch(scene):
        raise CloudError("Invalid scene identifier")
    return Path(root) / "production" / "cloud" / "scenes" / scene


def prepare(scene, root=ROOT, *, refresh=False):
    packet = plan(scene, root)
    folder = _folder(root, scene)
    path = folder / "packet.json"
    if path.exists() and not refresh:
        old = load_json(path)
        if old != packet:
            raise CloudError("Existing packet differs from current source. Inspect changes, then use --refresh.")
        return {"path": str(path), "shots": packet["shot_count"], "unchanged": True}
    folder.mkdir(parents=True, exist_ok=True)
    write_json(path, packet)
    lines = [
        f"# ChatGPT cloud production: {scene}",
        "",
        "Source of truth: packet.json and the exact hashed repository sources.",
        "Create actual action drawings, registered layers and video clips for each shot.",
        "Use the approved character and art contracts, not a generic anime style.",
        "No local Codex agent is needed. The ChatGPT session performs generation and review handoff directly.",
        "A generated still is a reference, never a completed moving shot.",
        "Every deliverable stays exploratory until independent review and author approval.",
        "",
    ]
    for s in packet["shots"]:
        lines += [f"## {s['shot']} — {s['frames']} frames at {s['fps']} fps",
                  s["required_action"], "",
                  f"Selected reference: {s['reference']['path'] or 'missing'}",
                  f"SHA-256: {s['reference']['sha256'] or 'not supplied'}",
                  "Verification: exact frame count, anatomy, contact geometry, prop separation, motion and scene continuity.",
                  ""]
    (folder / "CHATGPT_HANDOFF.md").write_text("\n".join(lines), encoding="utf-8")
    return {"path": str(path), "shots": packet["shot_count"], "frames": packet["frames"],
            "seconds": packet["seconds"], "unchanged": False}


def _packet(root, scene):
    path = _folder(root, scene) / "packet.json"
    if not path.is_file():
        raise CloudError(f"Missing scene packet; run cloud prepare {scene}")
    return load_json(path)


def _media_probe(media):
    if not shutil.which("ffprobe"):
        raise CloudError("ffprobe is required to import actual media")
    cmd = ["ffprobe", "-v", "error", "-count_frames", "-show_streams",
           "-of", "json", str(media)]
    result = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if result.returncode:
        raise CloudError("Cannot decode video: " + result.stderr[-300:])
    streams = json.loads(result.stdout).get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    if not video:
        raise CloudError("Submitted file has no video stream")
    try:
        fps = Fraction(video["avg_frame_rate"])
        frames = int(video["nb_read_frames"])
        size = (int(video["width"]), int(video["height"]))
    except (KeyError, ValueError, ZeroDivisionError) as exc:
        raise CloudError("Cannot establish exact decoded frame count or frame rate") from exc
    return {"fps": str(fps), "frames": frames, "size": list(size),
            "has_audio": any(s.get("codec_type") == "audio" for s in streams)}


def _receipt(root, scene, shot):
    packet = _packet(root, scene)
    if shot not in {s["shot"] for s in packet["shots"]}:
        raise CloudError(f"{shot} does not belong to {scene}")
    path = _folder(root, scene) / "received" / shot / "receipt.json"
    return load_json(path) if path.exists() else None


def ingest(scene, shot, media, root=ROOT, *, evidence=None):
    packet = _packet(root, scene)
    record = next((s for s in packet["shots"] if s["shot"] == shot), None)
    if not record:
        raise CloudError(f"Shot {shot} not in prepared scene {scene}")
    media = Path(media).resolve()
    if not media.is_file() or not media.stat().st_size:
        raise CloudError("Cloud clip does not exist or is empty")
    observed = _media_probe(media)
    if observed["fps"] != str(packet["fps"]) or observed["frames"] != record["frames"] \
            or observed["size"] != [packet["width"], packet["height"]]:
        raise CloudError(f"Frame-exact import failed for {shot}: {observed}, "
                         f"expected {record['frames']}f {packet['fps']}fps "
                         f"{packet['width']}x{packet['height']}")
    folder = _folder(root, scene) / "received" / shot
    digest = sha256(media)
    existing = _receipt(root, scene, shot)
    if existing:
        if existing["sha256"] == digest:
            return existing
        raise CloudError("Shot already has a different submission. Preserve it; start a new revision.")
    if evidence:
        ev = load_json(evidence)
        if ev.get("shot") != shot:
            raise CloudError("Motion evidence shot ID mismatch")
    else:
        ev = {"shot": shot, "drawn_action_review": "unprovided",
              "performance_review": "unprovided"}
    folder.mkdir(parents=True, exist_ok=False)
    copied = folder / "candidate.mp4"
    try:
        with tempfile.NamedTemporaryFile(dir=folder, delete=False, suffix=".part") as tmp:
            temp = Path(tmp.name)
        shutil.copyfile(media, temp)
        if sha256(temp) != digest:
            raise CloudError("Imported file hash mismatch")
        os.replace(temp, copied)
        receipt = {
            "schema": "ilan.chat-cloud.receipt.v1",
            "shot": shot,
            "scene": scene,
            "mode": "cloud",
            "media_path": copied.relative_to(root).as_posix(),
            "sha256": digest,
            "source_hashes": packet["source_hashes"],
            "media": observed,
            "evidence": ev,
            "state": "submitted-for-independent-review",
            "technical_approved": False,
            "author_approved": False,
            "canonical": False,
            "final_eligible": False,
        }
        write_json(folder / "receipt.json", receipt)
        return receipt
    except Exception:
        if "temp" in locals():
            temp.unlink(missing_ok=True)
        if not (folder / "receipt.json").exists():
            copied.unlink(missing_ok=True)
            try:
                folder.rmdir()
            except OSError:
                pass
        raise


def bridge(scene, shot, root=ROOT):
    """Convert an imported video to an ordinary local studio-engine cel sequence."""
    root = Path(root)
    receipt = _receipt(root, scene, shot)
    if not receipt:
        raise CloudError("Submit an actual clip before building a local/hybrid handoff")
    if not shutil.which("ffmpeg"):
        raise CloudError("ffmpeg is required for the hybrid engine handoff")
    video = root / receipt["media_path"]
    if sha256(video) != receipt["sha256"]:
        raise CloudError("Cloud clip hash changed")
    out = _folder(root, scene) / "received" / shot / "hybrid"
    if out.exists():
        raise CloudError("Hybrid import already exists; do not overwrite previous take")
    out.mkdir()
    frames = out / "frames"
    frames.mkdir()
    proc = subprocess.run(["ffmpeg", "-v", "error", "-xerror", "-i", str(video),
                           "-map", "0:v:0", "-fps_mode", "passthrough",
                           str(frames / "%06d.png")], capture_output=True, text=True)
    pngs = sorted(frames.glob("*.png"))
    if proc.returncode or len(pngs) != receipt["media"]["frames"]:
        raise CloudError("Frame extraction failed; inspect partial hybrid directory")
    spec = {
        "id": shot, "size": receipt["media"]["size"], "frames": len(pngs),
        "status": "exploratory", "stage": "cloud-import",
        "layers": [{"name": "cloud-candidate-frames",
                    "sequence": [(p.relative_to(root)).as_posix() for p in pngs], "rate": 1}],
        "camera": [{"frame": 0, "scale": 1}],
        "source_clip_sha256": receipt["sha256"],
        "final_eligible": False,
    }
    write_json(out / "shot.json", spec)
    return {"shot": shot, "spec": str(out / "shot.json"), "frames": len(pngs),
            "status": "exploratory-hybrid-candidate"}


def status(scene, root=ROOT):
    packet = _packet(root, scene)
    rows = []
    for s in packet["shots"]:
        r = _receipt(root, scene, s["shot"])
        rows.append({"shot": s["shot"], "frames": s["frames"],
                     "status": r["state"] if r else "missing-motion",
                     "author_approved": False})
    return {"scene": scene, "mode": "cloud", "shots": rows,
            "received": sum(r["status"] != "missing-motion" for r in rows),
            "total": len(rows), "final_eligible": False}


def assemble_draft(scene, out, root=ROOT):
    """Build ONLY an explicitly labeled silent inspection cut; never final output."""
    root = Path(root)
    packet = _packet(root, scene)
    files = []
    for shot in packet["shots"]:
        receipt = _receipt(root, scene, shot["shot"])
        if not receipt:
            raise CloudError(f"Refusing incomplete scene: {shot['shot']} has no clip")
        path = root / receipt["media_path"]
        if not path.is_file() or sha256(path) != receipt["sha256"]:
            raise CloudError(f"Refusing changed or missing clip: {shot['shot']}")
        if _media_probe(path)["frames"] != shot["frames"]:
            raise CloudError(f"Refusing changed frame count: {shot['shot']}")
        files.append(path)
    if not shutil.which("ffmpeg"):
        raise CloudError("ffmpeg unavailable")
    out = Path(out).resolve()
    if out.exists():
        raise CloudError("Won't overwrite an existing video")
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tempdir:
        lines = ["file '" + str(p).replace("'", "'\\''") + "'" for p in files]
        listfile = Path(tempdir) / "concat.txt"
        listfile.write_text("\n".join(lines) + "\n")
        proc = subprocess.run(["ffmpeg", "-v", "error", "-xerror", "-f", "concat",
                               "-safe", "0", "-i", str(listfile), "-an",
                               "-c:v", "libx264", "-pix_fmt", "yuv420p",
                               "-r", str(packet["fps"]), str(out)],
                              capture_output=True, text=True)
        if proc.returncode:
            out.unlink(missing_ok=True)
            raise CloudError("Scene concat failed: " + proc.stderr[-500:])
    final = _media_probe(out)
    if final["frames"] != packet["frames"]:
        out.unlink(missing_ok=True)
        raise CloudError("Scene frame count mismatch; deleted invalid draft")
    write_json(out.with_suffix(".review.json"), {
        "scene": scene, "frames": final["frames"], "sha256": sha256(out),
        "state": "inspection-only", "author_approved": False,
        "sound": "excluded", "final_eligible": False,
        "note": "Even complete shot coverage is not performance or final approval.",
    })
    return {"draft": str(out), "frames": final["frames"], "status": "inspection-only"}


def set_mode(mode, root=ROOT):
    if mode not in MODES:
        raise CloudError(f"Choose one of: {MODES}")
    path = Path(root) / "production/workflow-mode.json"
    write_json(path, {"schema": "ilan.production-modes.v1", "active": mode,
                      "available": list(MODES),
                      "note": "Mode only selects an interface; existing asset and author gates still apply."})
    return {"active": mode, "path": str(path)}


def main(argv=None):
    p = argparse.ArgumentParser(prog="python -m studio cloud")
    sub = p.add_subparsers(dest="action", required=True)
    a = sub.add_parser("prepare", help="Make source-bound ChatGPT scene packet")
    a.add_argument("scene")
    a.add_argument("--refresh", action="store_true")
    a = sub.add_parser("status")
    a.add_argument("scene")
    a = sub.add_parser("ingest", help="Import an actual cloud-generated MP4")
    a.add_argument("scene")
    a.add_argument("shot")
    a.add_argument("video")
    a.add_argument("--evidence")
    a = sub.add_parser("bridge", help="Convert cloud MP4 to studio-engine frames")
    a.add_argument("scene")
    a.add_argument("shot")
    a = sub.add_parser("assemble-draft", help="Refuse unless all scene clips exist")
    a.add_argument("scene")
    a.add_argument("--out", required=True)
    a = sub.add_parser("validate-action", help="Check bell, grip, joint and clapper geometry")
    a.add_argument("evidence")
    a = sub.add_parser("mode", help="Choose Cloud, Local or Hybrid")
    a.add_argument("selected", choices=MODES)
    args = p.parse_args(argv)
    if args.action == "prepare":
        result = prepare(args.scene, refresh=args.refresh)
    elif args.action == "status":
        result = status(args.scene)
    elif args.action == "ingest":
        result = ingest(args.scene, args.shot, args.video, evidence=args.evidence)
    elif args.action == "bridge":
        result = bridge(args.scene, args.shot)
    elif args.action == "assemble-draft":
        result = assemble_draft(args.scene, args.out)
    elif args.action == "validate-action":
        result = validate_action(load_json(args.evidence))
    else:
        result = set_mode(args.selected)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
