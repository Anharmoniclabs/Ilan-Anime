"""Render queue, checkpoints and episode assembly.

* ``export_shot``: one spec -> one file, with a manifest that hashes the spec,
  every source image and the output, plus a decoded frame-count check.
* ``RenderQueue``: renders many shots, skipping any whose manifest still
  matches (resume after interruption without redoing work), and records
  failures instead of retrying them.
* ``assemble``: concatenates shot masters in canonical episode order, checks
  the total frame count, and writes the episode master + a review copy.
"""
from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor, as_completed
import json
from pathlib import Path
import subprocess
import time

from studio import __version__
from studio.engine import READY_STATUSES, Compositor, Writer, burn_in
from studio.engine.io import ExportError, ffmpeg_bin, probe_frames
from studio.paths import PROJECT, ROOT, load_json, rel, resolve, sha256, write_json

EXT = {"master": ".mkv", "review": ".mp4", "frames": ""}


def _sources(spec, base):
    """Every file a spec reads (for checkpoint hashing)."""
    found = set()
    for layer in spec.get("layers", []):
        for key in ("source",):
            if layer.get(key):
                found.add(layer[key])
        found.update(layer.get("sequence", []))
        found.update(e["source"] for e in layer.get("exposures", []))
    for item in spec.get("post", {}).get("double_exposure", []):
        found.add(item["source"])
    if spec.get("audio"):
        found.add(spec["audio"])
    return sorted(found)


def spec_fingerprint(spec, base=PROJECT, quality="final", mode="review", burn=False):
    files = {path: sha256(resolve(path, base)) for path in _sources(spec, base)}
    blob = json.dumps({"spec": spec, "files": files, "engine": __version__,
                       "quality": quality, "mode": mode, "burn": burn}, sort_keys=True)
    import hashlib
    return hashlib.sha256(blob.encode()).hexdigest(), files


def export_shot(spec, out, *, draft=False, base=PROJECT, mode=None, quality="final",
                burn=False, start_frame=None, label=None):
    """Render one shot. Unready specs need ``draft=True`` (never a final)."""
    out = Path(out)
    if spec.get("status") not in READY_STATUSES and not draft:
        raise ExportError(f"{spec.get('id')}: status {spec.get('status')!r} is not animation-ready; "
                          "pass --draft for a preview. A draft is never a final.")
    mode = mode or ("frames" if out.suffix == "" else ("master" if out.suffix == ".mkv" else "review"))
    compositor = Compositor(spec, base=base, quality=quality, scale=float(spec.get("render_scale", 1.0)))
    audio = resolve(spec["audio"], base) if spec.get("audio") else None
    started = time.time()
    with Writer(out, compositor.size, mode=mode, audio=audio,
                duration=compositor.frames / 24 if audio else None) as writer:
        for frame in range(compositor.frames):
            image = compositor.draw(frame)
            if burn:
                absolute = None if start_frame is None else start_frame + frame
                image = burn_in(image, spec.get("id", "shot"), frame, absolute, label)
            writer.write(image)
    if mode != "frames":
        decoded = probe_frames(out)
        if decoded != compositor.frames:
            raise ExportError(f"{spec.get('id')}: wrote {decoded} frames, expected {compositor.frames}")
    fingerprint, files = spec_fingerprint(spec, base, quality, mode, burn)
    manifest = {
        "shot": spec.get("id"), "output": rel(out), "mode": mode, "quality": quality,
        "frames": compositor.frames, "size": list(compositor.size), "draft": bool(draft),
        "status": spec.get("status"), "engine": __version__, "fingerprint": fingerprint,
        "inputs": files, "output_sha256": sha256(out) if mode != "frames" else None,
        "seconds": round(time.time() - started, 2),
        "truth": "A successful render proves the spec executes, not that the animation is good.",
    }
    write_json(_manifest_path(out), manifest)
    return manifest


def _manifest_path(out: Path) -> Path:
    return out.with_name(out.name + ".manifest.json") if out.suffix else out / "manifest.json"


def is_current(spec, out, base=PROJECT, quality="final", mode="review", burn=False):
    path = _manifest_path(Path(out))
    if not path.exists() or not Path(out).exists():
        return False
    manifest = load_json(path)
    fingerprint, _ = spec_fingerprint(spec, base, quality, mode, burn)
    if manifest.get("fingerprint") != fingerprint:
        return False
    return manifest.get("output_sha256") in (None, sha256(out))


def _job(args):
    spec, out, draft, quality, burn, start, label = args
    return export_shot(spec, out, draft=draft, quality=quality, burn=burn, start_frame=start, label=label)


class RenderQueue:
    """Checkpointed batch renderer. State lives in ``<out_dir>/queue.json``."""

    def __init__(self, out_dir, *, mode="master", quality="final", draft=False, burn=False,
                 label=None, workers=1):
        self.out_dir = Path(out_dir)
        self.mode, self.quality, self.draft = mode, quality, draft
        self.burn, self.label, self.workers = burn, label, max(1, int(workers))
        self.state_path = self.out_dir / "queue.json"
        self.state = load_json(self.state_path) if self.state_path.exists() else {"shots": {}}

    def output_for(self, shot_id):
        return self.out_dir / f"{shot_id}{EXT[self.mode]}"

    def run(self, jobs, progress=print):
        """jobs: list of (shot_id, spec, start_frame). Returns summary dict."""
        todo, skipped = [], []
        for shot_id, spec, start in jobs:
            out = self.output_for(shot_id)
            if is_current(spec, out, PROJECT, self.quality, self.mode, self.burn):
                skipped.append(shot_id)
                self.state["shots"][shot_id] = {"status": "rendered", "output": rel(out)}
                continue
            todo.append((shot_id, (spec, out, self.draft, self.quality, self.burn, start, self.label)))
        failures = {}
        self.out_dir.mkdir(parents=True, exist_ok=True)
        if self.workers == 1:
            for shot_id, args in todo:
                self._record(shot_id, args, failures, progress)
        else:
            with ProcessPoolExecutor(self.workers) as pool:
                futures = {pool.submit(_job, args): (shot_id, args) for shot_id, args in todo}
                for future in as_completed(futures):
                    shot_id, args = futures[future]
                    try:
                        manifest = future.result()
                        self.state["shots"][shot_id] = {"status": "rendered", "output": manifest["output"]}
                        progress(f"rendered {shot_id} ({manifest['seconds']}s)")
                    except Exception as exc:  # recorded, never retried automatically
                        failures[shot_id] = str(exc)
                        self.state["shots"][shot_id] = {"status": "failed", "error": str(exc)}
                        progress(f"FAILED {shot_id}: {exc}")
                    write_json(self.state_path, self.state)
        write_json(self.state_path, self.state)
        return {"rendered": len(todo) - len(failures), "skipped_current": len(skipped),
                "failed": failures, "queue": rel(self.state_path)}

    def _record(self, shot_id, args, failures, progress):
        try:
            manifest = _job(args)
            self.state["shots"][shot_id] = {"status": "rendered", "output": manifest["output"]}
            progress(f"rendered {shot_id} ({manifest['seconds']}s)")
        except Exception as exc:
            failures[shot_id] = str(exc)
            self.state["shots"][shot_id] = {"status": "failed", "error": str(exc)}
            progress(f"FAILED {shot_id}: {exc}")
        write_json(self.state_path, self.state)


def assemble(shot_files, out, *, expected_frames=None, audio=None, review_copy=True):
    """Concatenate shot files (same size/rate/codec) in order; verify frame total.

    FFV1 ``.mkv`` masters -> episode master ``.mkv`` (+ a tagged review ``.mp4``).
    H.264 ``.mp4`` review files (e.g. the animatic) -> one ``.mp4`` by stream copy.
    """
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    listing = out.with_suffix(".concat.txt")
    listing.write_text("".join(f"file '{Path(f).resolve()}'\n" for f in shot_files))
    review_inputs = all(str(f).endswith(".mp4") for f in shot_files)
    target = out.with_suffix(".mp4" if review_inputs else ".mkv")
    cmd = [ffmpeg_bin(), "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0",
           "-i", str(listing)]
    if audio:
        cmd += ["-i", str(audio), "-map", "0:v", "-map", "1:a", "-shortest",
                "-c:a", "aac" if review_inputs else "pcm_s24le"]
    cmd += ["-c:v", "copy"] + (["-movflags", "+faststart"] if review_inputs else []) + [str(target)]
    subprocess.run(cmd, check=True)
    total = probe_frames(target)
    if expected_frames is not None and total != expected_frames:
        raise ExportError(f"assembled {total} frames, expected {expected_frames}")
    result = {"output": rel(target), "frames": total, "sha256": sha256(target)}
    if review_copy and not review_inputs:
        review = out.with_suffix(".mp4")
        cmd = [ffmpeg_bin(), "-hide_banner", "-loglevel", "error", "-y", "-i", str(target),
               "-vf", "scale=out_color_matrix=bt709:out_range=tv", "-c:v", "libx264", "-crf", "20",
               "-preset", "medium", "-pix_fmt", "yuv420p", "-colorspace", "bt709",
               "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv",
               "-movflags", "+faststart"]
        cmd += ["-c:a", "aac", "-b:a", "192k"] if audio else []
        cmd.append(str(review))
        subprocess.run(cmd, check=True)
        result["review"] = rel(review)
    write_json(out.with_suffix(".assembly.json"), result)
    return result
