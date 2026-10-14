"""HF Space video candidates -> frame-exact, exploratory studio shot specs.

The only remote backend is the explicitly selected public MiniMax Space.
Anonymous requests deliberately do not attach cached HF credentials: this
adapter cannot draw on the user's prepaid balance. Quota failure stops work.
No automatic retry, provider fallback, model download or production approval.
"""
from __future__ import annotations

import argparse
import importlib.util
import inspect
import json
from pathlib import Path
import shutil
import subprocess

from PIL import Image, ImageOps

from studio.paths import EPISODE, PROJECT, load_json, sha256, write_json

SPACE = "Pepe104/MiniMax-H3-Turbo-Lora-UNCENSORED"
SPACE_URL = "https://pepe104-minimax-h3-turbo-lora-uncensored.hf.space"
CANVAS = "1024x576 · 16:9 fast"
FPS = 24
MAX_FRAMES = 14 * FPS


class VideoError(RuntimeError):
    pass


def positive_int(value, label):
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise VideoError(f"{label} must be a positive integer")
    return value


def episode_plan(episode=None):
    """Inventory all shots; splitting preserves timing, not artistic continuity."""
    episode = episode or load_json(EPISODE)
    shots = []
    for shot in episode["shots"]:
        frames = positive_int(shot["frames"], "shot frames")
        segments = [{"offset": start, "frames": min(MAX_FRAMES, frames - start)}
                    for start in range(0, frames, MAX_FRAMES)]
        shots.append({"shot": shot["id"], "frames": frames,
                      "references": shot.get("keyframes", []), "segments": segments,
                      "needs_image": not bool(shot.get("keyframes")),
                      "status": "needs_reference_and_action_review"})
    return {"fps": FPS, "shots": shots, "total_frames": sum(s["frames"] for s in shots),
            "remote_segments": sum(len(s["segments"]) for s in shots),
            "truth": "Inventory only. Segment boundaries and references require shot-specific review."}


def _shot(shot_id):
    for shot in load_json(EPISODE)["shots"]:
        if shot["id"] == shot_id:
            return shot
    raise VideoError(f"unknown episode shot: {shot_id}")


def prepare(shot_id, first, out, *, prompt_file=None, last=None, frames=None, offset=0, seed=42):
    shot = _shot(shot_id)
    frames = shot["frames"] - offset if frames is None else frames
    positive_int(frames, "frames")
    if offset < 0 or offset + frames > shot["frames"]:
        raise VideoError("segment falls outside the scripted shot")
    if frames > MAX_FRAMES:
        raise VideoError("Space supports at most 14 seconds; prepare separate authored segments")
    # Validate images before creating the job directory. Preserve originals.
    refs = {"first": Path(first).resolve()}
    if last:
        refs["last"] = Path(last).resolve()
    for path in refs.values():
        with Image.open(path) as img:
            img.verify()
    from studio.generate import art_preamble
    action = Path(prompt_file).read_text() if prompt_file else shot["script"]
    prompt = (art_preamble("story_frame") + "\n\n" + action +
              f"\nThis test covers only shot frames {offset}–{offset + frames - 1} "
              f"({frames / FPS:g} seconds) of the {shot['frames'] / FPS:g}-second shot. "
              "Do not compress the entire shot into this segment. "
              "\nAnimate the described action with stable faces, hands, grips and rigid props. "
              "No morphing, pulsing hulls, new characters, captions or generated lettering. "
              "Soundtrack is a temporary guide; exact dialogue and final sound are separate.")
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    references = {}
    for label, source in refs.items():
        target = out / f"{label}.png"
        with Image.open(source) as img:
            image = ImageOps.exif_transpose(img).convert("RGB")
            # Exact 16:9 prevents the Space's automatic cover-crop of the input.
            ImageOps.pad(image, (1024, 576), color="black").save(target)
        references[label] = {"path": target.name, "sha256": sha256(target),
                             "original": str(source), "original_sha256": sha256(source),
                             "transform": "fit inside 1024x576; black padding; original untouched"}
    duration = max(2.0, frames / FPS)
    expected = round(duration * FPS)
    while expected % 17 != 5:
        expected += 1
    manifest = {"version": 1, "provider": SPACE, "shot": shot_id,
                "shot_offset": offset, "frames": frames, "fps": FPS, "state": "prepared",
                "references": references, "request": {"prompt": prompt, "canvas": CANVAS,
                "duration": duration, "steps": 6, "seed": seed, "upsample": False,
                "use_lora": True, "lora": "larry"}, "expected_remote_frames": expected,
                "authentication": "anonymous-only", "paid_requests_allowed": False,
                "truth": "Exploratory reference-conditioned video; neither likeness nor animation quality is guaranteed."}
    write_json(out / "job.json", manifest)
    return manifest


def _read_job(directory):
    directory = Path(directory).resolve()
    job = load_json(directory / "job.json")
    if job.get("provider") != SPACE or job.get("fps") != FPS:
        raise VideoError("unsupported backend or frame rate")
    frames = positive_int(job.get("frames"), "frames")
    shot = _shot(job["shot"])
    offset = job.get("shot_offset", -1)
    if not isinstance(offset, int) or offset < 0 or offset + frames > shot["frames"]:
        raise VideoError("segment falls outside the scripted shot")
    if frames > MAX_FRAMES:
        raise VideoError("segment exceeds backend limit")
    request = job["request"]
    if (request.get("canvas") != CANVAS or request.get("duration") != max(2.0, frames / FPS)
            or request.get("steps") != 6 or request.get("upsample") is not False
            or request.get("lora") != "larry"):
        raise VideoError("unexpected request settings; prepare a fresh bounded job")
    if not request.get("prompt", "").strip():
        raise VideoError("empty prompt")
    if "first" not in job["references"]:
        raise VideoError("first reference required")
    for item in job["references"].values():
        path = (directory / item["path"]).resolve()
        if not path.is_relative_to(directory) or sha256(path) != item["sha256"]:
            raise VideoError("reference changed or escaped the job directory")
    return directory, job


def _client(directory):
    try:
        from gradio_client import Client, handle_file
    except ImportError as exc:
        raise VideoError("install requirements-video.txt in the studio venv first") from exc
    # Older clients named this hf_token. False explicitly disables cached tokens
    # in huggingface_hub.build_hf_headers; None would silently use the local token.
    key = "token" if "token" in inspect.signature(Client).parameters else "hf_token"
    client = Client(SPACE_URL, **{key: False}, verbose=False,
                    download_files=str(directory / "downloads"))
    if any("authorization" in k.lower() for k in client.headers):
        raise VideoError("refusing authenticated request: anonymous-only budget protection")
    return client, handle_file


def submit(directory, *, client_factory=_client):
    directory, job = _read_job(directory)
    if (directory / "image-source.json").exists():
        from studio.demand import verify_video_source
        from studio.paths import ROOT
        verify_video_source(ROOT, directory)
    if job["state"] != "prepared" or (directory / "submission.lock").exists():
        raise VideoError("job already attempted; inspect its result, never automatically resubmit")
    # Exclusive durable marker also serializes two simultaneous coordinators.
    with (directory / "submission.lock").open("x") as handle:
        handle.write("One remote attempt. Retain this marker even after an error.\n")
    job["state"] = "connecting"
    write_json(directory / "job.json", job)
    try:
        client, handle_file = client_factory(directory)
        api = client.view_api(return_format="dict", print_info=False)
        endpoint = api.get("named_endpoints", {}).get("/generate")
        required = set(job["request"]) | {"image_path", "last_image_path"}
        if not endpoint or not required <= {p.get("parameter_name") for p in endpoint["parameters"]}:
            raise VideoError("live Space API differs from inspected contract; no generation submitted")
        kwargs = dict(job["request"])
        kwargs["image_path"] = handle_file(str(directory / job["references"]["first"]["path"]))
        kwargs["last_image_path"] = (handle_file(str(directory / job["references"]["last"]["path"]))
                                     if "last" in job["references"] else None)
        job["state"] = "submission_intent"
        write_json(directory / "job.json", job)
        result = client.predict(**kwargs, api_name="/generate")
        if not isinstance(result, (list, tuple)) or len(result) != 3:
            raise VideoError("unexpected result; inspect downloads without resubmitting")
        value = result[0]
        path = Path(value["path"] if isinstance(value, dict) else value).resolve()
        if not path.is_relative_to(directory / "downloads") or not path.is_file():
            raise VideoError("client did not download video into the job directory")
        target = directory / "source.mp4"
        if target.exists():
            raise VideoError("refusing to overwrite source.mp4")
        shutil.copyfile(path, target)
        job.update(state="downloaded", source_sha256=sha256(target),
                   provider_report=str(result[1]), refined_prompt=str(result[2]))
        write_json(directory / "job.json", job)
        return job
    except BaseException as exc:
        # Unknown outcome is deliberately sticky, including Ctrl+C and timeout.
        job.update(state="paused", failure_type=type(exc).__name__,
                   recovery="Inspect downloads and Space history. Import an existing result; do not resubmit.")
        write_json(directory / "job.json", job)
        raise


def import_clip(directory, clip=None):
    """Import API or browser result into a separate draft spec; never replace shot canon."""
    directory, job = _read_job(directory)
    source = Path(clip).resolve() if clip else directory / "source.mp4"
    if not source.is_file():
        raise VideoError("missing downloaded clip")
    ffmpeg, ffprobe = shutil.which("ffmpeg"), shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        raise VideoError("FFmpeg and ffprobe required")
    probe = subprocess.run([ffprobe, "-v", "error", "-select_streams", "v:0", "-count_frames",
                            "-show_entries", "stream=nb_read_frames,r_frame_rate,width,height",
                            "-of", "json", str(source)], capture_output=True, text=True, check=True)
    stream = json.loads(probe.stdout)["streams"][0]
    if stream["r_frame_rate"] not in ("24/1", "24"):
        raise VideoError("clip must be 24 fps; do not silently retime action")
    if int(stream["nb_read_frames"]) < job["frames"]:
        raise VideoError("clip is shorter than the requested action; no freeze padding")
    imported = directory / "imported"
    imported.mkdir(exist_ok=False)
    # Own an immutable source copy even when it came from the browser.
    shutil.copyfile(source, imported / "source.mp4")
    frames_dir = imported / "frames"
    frames_dir.mkdir()
    subprocess.run([ffmpeg, "-v", "error", "-nostdin", "-i", str(imported / "source.mp4"),
                    "-an", "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2",
                    "-frames:v", str(job["frames"]), "-threads", "1", "-start_number", "0",
                    str(frames_dir / "%06d.png")], capture_output=True, text=True, check=True)
    files = sorted(frames_dir.glob("*.png"))
    if len(files) != job["frames"]:
        raise VideoError("decoded frame count mismatch")
    from studio.blender import import_sequence
    layer = import_sequence(frames_dir, name="generated_video", rate=1,
                            tags=["generated_video", "exploratory"], screen_space=True)
    layer["provenance"] = {"provider": SPACE, "source_sha256": sha256(imported / "source.mp4"),
                           "job": str(directory / "job.json"), "method": "image_to_video"}
    spec = {"id": job["shot"], "size": [1280, 720], "frames": job["frames"], "fps": FPS,
            "shot_offset": job["shot_offset"], "status": "exploratory", "stage": "video_candidate",
            "animation_status": "needs_review", "layers": [layer], "camera": [], "post": {}, "audio": None,
            "truth": "Generated video candidate. Review motion, anatomy, contacts and references before approval. "
                     "Original generated soundtrack retained only in source.mp4; final audio is separate."}
    write_json(imported / "shot.json", spec)
    job.update(state="imported", imported_spec=str(imported / "shot.json"),
               imported_source_sha256=sha256(imported / "source.mp4"),
               discarded_tail_frames=int(stream["nb_read_frames"]) - job["frames"])
    write_json(directory / "job.json", job)
    return {"spec": str(imported / "shot.json"), "frames": len(files), "status": "exploratory"}


def doctor():
    return {"codex": shutil.which("codex"), "blender": shutil.which("blender"),
            "ffmpeg": shutil.which("ffmpeg"), "ffprobe": shutil.which("ffprobe"),
            "gradio_client": importlib.util.find_spec("gradio_client") is not None,
            "video_space": SPACE, "authentication": "anonymous-only; no cached HF tokens",
            "llm": "existing Codex runner; no HF Inference Providers, Z.ai or GLM",
            "live_generation_verified": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor")
    p = sub.add_parser("plan")
    p.add_argument("--out", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("--shot", required=True)
    p.add_argument("--first", required=True)
    p.add_argument("--last")
    p.add_argument("--prompt-file")
    p.add_argument("--frames", type=int)
    p.add_argument("--offset", type=int, default=0)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--out", required=True)
    for action in ("submit", "import"):
        p = sub.add_parser(action)
        p.add_argument("job")
        if action == "import":
            p.add_argument("--clip", help="existing browser download; no generation request")
    args = parser.parse_args(argv)
    try:
        if args.command == "doctor":
            result = doctor()
        elif args.command == "plan":
            result = episode_plan()
            write_json(args.out, result)
            result = {k: v for k, v in result.items() if k != "shots"} | {"out": args.out}
        elif args.command == "prepare":
            result = prepare(args.shot, args.first, args.out, prompt_file=args.prompt_file,
                             last=args.last, frames=args.frames, offset=args.offset, seed=args.seed)
        elif args.command == "submit":
            result = submit(args.job)
        else:
            result = import_clip(args.job, args.clip)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except (VideoError, OSError, ValueError, subprocess.SubprocessError) as exc:
        raise SystemExit(f"video stopped: {exc}") from exc


if __name__ == "__main__":
    main()
