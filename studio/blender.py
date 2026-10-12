"""Blender bridge: render element layers headless, check stepping, import as exposures.

* ``render``  runs ``blender -b scene.blend --python studio/blender_npr_setup.py``
              (the NPR contract from the blender-npr-3d-anime skill) and returns
              its report. Blender is found via ``BLENDER_BIN``, PATH, or the
              usual install locations.
* ``check``   reads a rendered PNG sequence and reports every frame where the
              picture changes off the step grid - the classic 3D-look failure
              of a character moving on 1s.
* ``import_sequence`` turns a PNG sequence into an engine layer: identical
              consecutive frames collapse into one exposure (a hold).
"""
from __future__ import annotations

import glob
import hashlib
import os
from pathlib import Path
import shutil
import subprocess

from studio.paths import PROJECT, load_json, rel, write_json

SETUP_SCRIPT = Path(__file__).with_name("blender_npr_setup.py")
COMMON = ["/Applications/Blender.app/Contents/MacOS/Blender",
          "C:/Program Files/Blender Foundation/Blender*/blender.exe",
          "/snap/bin/blender", "/usr/bin/blender", "/usr/local/bin/blender"]


class BlenderError(RuntimeError):
    pass


def find_blender():
    env = os.environ.get("BLENDER_BIN")
    if env and Path(env).exists():
        return env
    found = shutil.which("blender")
    if found:
        return found
    for pattern in COMMON:
        matches = sorted(glob.glob(pattern))
        if matches:
            return matches[-1]
    raise BlenderError("Blender not found. Install Blender 4.2+ and put it on PATH or set BLENDER_BIN.")


def render(scene, out, *, frames, step=2, layers=(), width=1280, height=720, camera="blender",
           no_render=False, blender=None, timeout=None):
    """Render element layers through the NPR setup script; returns its report."""
    scene, out = Path(scene), Path(out)
    if not scene.is_file():
        raise BlenderError(f"missing .blend file: {scene}")
    if int(step) < 1:
        raise BlenderError("step must be >= 1")
    cmd = [blender or find_blender(), "-b", str(scene), "--python", str(SETUP_SCRIPT), "--",
           "--out", str(out), "--frames", str(frames), "--step", str(int(step)),
           "--layers", ",".join(layers), "--width", str(int(width)), "--height", str(int(height)),
           "--camera", camera]
    if no_render:
        cmd.append("--no-render")
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    report_path = out / "blender_render.json"
    if proc.returncode != 0 or not report_path.exists():
        raise BlenderError(f"Blender failed ({proc.returncode}): {(proc.stderr or proc.stdout)[-1200:]}")
    return load_json(report_path)


def _frames(directory):
    files = sorted(Path(directory).glob("*.png"), key=lambda p: (len(p.stem), p.stem))
    if not files:
        raise BlenderError(f"no PNG frames in {directory}")
    return files


def _pixel_digest(path):
    """Hash decoded pixels so identical images with different PNG metadata still match."""
    from PIL import Image
    with Image.open(path) as image:
        return hashlib.sha256(image.convert("RGBA").tobytes()).hexdigest()


def check(directory, step, start=0):
    """Report picture changes that land off the ``step`` grid."""
    files = _frames(directory)
    digests = [_pixel_digest(f) for f in files]
    changes = [i for i in range(1, len(digests)) if digests[i] != digests[i - 1]]
    off_grid = [i + start for i in changes if (i % int(step)) != 0]
    report = {"directory": rel(directory), "frames": len(files), "step": int(step), "changes": len(changes),
              "off_grid_changes": off_grid[:50], "off_grid_count": len(off_grid),
              "ok": not off_grid,
              "verdict": "stepped" if not off_grid else
                         f"{len(off_grid)} changes off the {step}s grid: reads as 3D (moving on 1s)"}
    return report


def import_sequence(directory, *, name, rate=2, tags=(), start=0, screen_space=True, out=None):
    """PNG sequence -> engine layer with exposures; holds collapse into one drawing."""
    files = _frames(directory)
    digests = [_pixel_digest(f) for f in files]
    base = PROJECT
    exposures = []
    for i, (path, digest) in enumerate(zip(files, digests)):
        if exposures and exposures[-1]["_digest"] == digest:
            exposures[-1]["end"] = i + 1
            continue
        try:
            source = Path(path).resolve().relative_to(base).as_posix()
        except ValueError:
            source = str(Path(path).resolve())
        exposures.append({"start": i, "end": i + 1, "source": source, "_digest": digest})
    for item in exposures:
        item.pop("_digest")
    # rate 1: play exactly what Blender rendered (already stepped and checked); keep the
    # intended drawing rate for reviewers and QA.
    layer = {"name": name, "rate": 1, "drawing_rate": int(rate), "tags": list(tags), "in": int(start),
             "out": int(start) + len(files), "source": exposures[0]["source"], "exposures": exposures,
             "provenance": {"renderer": "blender", "frames_dir": rel(directory),
                            "report": rel(Path(directory).parent / "blender_render.json")}}
    if screen_space:
        layer["screen_space"] = True  # Blender owned the camera; the engine must not move it again
    if out:
        write_json(out, layer)
    return layer
