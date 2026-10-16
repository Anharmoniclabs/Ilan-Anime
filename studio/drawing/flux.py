"""Optional learned-art backend: FLUX.2 Klein 4B via a local stable-diffusion.cpp binary.

Used only for drawings the procedural engine cannot construct (new head/body
angles, novel poses). It is reference-conditioned (``-r``) on approved art and
returns ONE flat raster per call. That raster is ``model-generated``: it is not
editable layers until it goes through ``reference.extract``, and it is never
canon until the author approves its exact digest.

Install (outside the repo; weights are never committed):

    ~/ai-models/flux2-klein/bin/sd-cli                       stable-diffusion.cpp CPU build
    ~/ai-models/flux2-klein/models/flux-2-klein-4b-Q4_0.gguf  diffusion model (2.46 GB)
    ~/ai-models/flux2-klein/models/Qwen3-4B-Q4_K_M.gguf       text encoder (2.50 GB)
    ~/ai-models/flux2-klein/models/flux2-vae.safetensors      VAE (0.34 GB)

Override the root with ``ILAN_FLUX_ROOT``. Measured on the i3-1115G4 / 12 GB
laptop (2026-10-16): ~1356 s per 512x768 image at 4 steps, 4.5 GB peak RSS.

Safety: one run at a time (lock file), hard timeout, no automatic retry. A
timed-out or interrupted run is recorded as ``unknown`` and must be inspected.
"""
from __future__ import annotations

import json
import os
import resource
import subprocess
import time
from pathlib import Path

from studio.paths import rel, sha256, write_json

ROOT = Path(os.environ.get("ILAN_FLUX_ROOT", Path.home() / "ai-models" / "flux2-klein"))
FILES = {"binary": "bin/sd-cli", "diffusion": "models/flux-2-klein-4b-Q4_0.gguf",
         "llm": "models/Qwen3-4B-Q4_K_M.gguf", "vae": "models/flux2-vae.safetensors"}
MAX_PIXELS = 1024 * 1024


class FluxError(RuntimeError):
    pass


def paths(root=ROOT):
    return {k: Path(root) / v for k, v in FILES.items()}


def doctor(root=ROOT):
    """Report which backend files exist. Never downloads anything."""
    found = {k: p.is_file() for k, p in paths(root).items()}
    return {"root": str(root), "files": found, "ready": all(found.values())}


def command(reference, prompt, output, *, width=512, height=768, steps=4, seed=42, threads=4, root=ROOT):
    """Build the sd-cli argument list (pure; testable without the binary)."""
    if width % 16 or height % 16 or width * height > MAX_PIXELS:
        raise FluxError(f"size {width}x{height} must be multiples of 16 and <= {MAX_PIXELS} pixels")
    if not 1 <= steps <= 8:
        raise FluxError("steps must be 1..8 (Klein is a 4-step distilled model)")
    if not prompt or len(prompt) > 1200:
        raise FluxError("prompt must be 1..1200 characters")
    p = paths(root)
    return [str(p["binary"]), "--diffusion-model", str(p["diffusion"]), "--llm", str(p["llm"]),
            "--vae", str(p["vae"]), "-r", str(reference), "-p", prompt, "--cfg-scale", "1.0",
            "--sampling-method", "euler", "--steps", str(steps), "-W", str(width), "-H", str(height),
            "--seed", str(seed), "--mmap", "-t", str(threads), "-o", str(output), "-v"]


def generate(reference, prompt, out_dir, *, timeout=3600, root=ROOT, **options):
    """Run one reference-conditioned generation into a new ``out_dir``. Returns the receipt."""
    out_dir = Path(out_dir)
    if out_dir.exists() and any(out_dir.iterdir()):
        raise FluxError(f"{out_dir} is not empty; every run needs a new take directory")
    status = doctor(root)
    if not status["ready"]:
        raise FluxError(f"backend files missing: {status['files']}")
    out_dir.mkdir(parents=True, exist_ok=True)
    lock = Path(root) / ".run.lock"
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        raise FluxError(f"another FLUX run holds {lock}; inspect it before removing") from None
    output = out_dir / "generated.png"
    cmd = command(reference, prompt, output, root=root, **options)
    receipt = {"backend": "flux2-klein-4b-q4 via stable-diffusion.cpp", "reference": rel(reference),
               "reference_sha256": sha256(reference), "prompt": prompt, "options": options,
               "argv": cmd, "kind": "model-generated", "editable": False, "approved": False}
    write_json(out_dir / "receipt.json", {**receipt, "state": "running"})
    started = time.perf_counter()
    try:
        os.write(fd, str(os.getpid()).encode())
        with open(out_dir / "sd-cli.log", "w") as log:
            proc = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, timeout=timeout)
        state = "succeeded" if proc.returncode == 0 and output.is_file() else "failed"
        receipt["exit"] = proc.returncode
    except subprocess.TimeoutExpired:
        state = "unknown"  # the process was killed; do not assume anything about partial output
    finally:
        os.close(fd)
        lock.unlink(missing_ok=True)
    receipt.update({"state": state, "seconds": round(time.perf_counter() - started, 1),
                    "peak_rss_mb": resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss // 1024})
    if state == "succeeded":
        receipt["output"], receipt["output_sha256"] = rel(output), sha256(output)
    write_json(out_dir / "receipt.json", receipt)
    if state != "succeeded":
        raise FluxError(f"FLUX run {state}; see {out_dir / 'sd-cli.log'}")
    return receipt


if __name__ == "__main__":  # pragma: no cover
    print(json.dumps(doctor(), indent=2))
