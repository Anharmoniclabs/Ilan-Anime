"""Local Craft workbench; explicit workflows, durable receipts, no automatic retries."""
from __future__ import annotations

import argparse
from contextlib import ExitStack
import importlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from studio.paths import ROOT, load_json, sha256, write_json

APPS = {
    "photocraft": ("photocraft-cli", "sketches, raster cleanup, paint and transparent cels"),
    "vectorcraft": ("vectorcraft-cli", "vector cleanup, paths, props and titles"),
    "effectcraft": ("effectcraft-cli", "cel exposures, compositing and effects"),
    "filmcraft": ("filmcraft-cli", "shot editing, audio tracks and delivery"),
    "lightcraft": ("lightcraft-cli", "reference development and grading"),
    "designcraft": ("designcraft-cli", "storyboards, model-sheet and production-book layouts"),
    "pdfcraft": ("printcraft-cli", "script and storyboard PDF inspection/export"),
}


def executable(name):
    local = Path.home() / ".local/bin" / name
    return shutil.which(name) or (str(local) if local.is_file() else None)


def backend():
    """Reuse the installed Nessa transport without its agent loop or permission state."""
    path = Path(os.environ.get("ILAN_NESSA_ROOT", ROOT.parent / "NESSA")).resolve()
    if not (path / "agentharness/mcp.py").is_file():
        raise ValueError("Nessa MCP transport missing; set ILAN_NESSA_ROOT to its checkout")
    sys.path.insert(0, str(path))
    return (importlib.import_module("agentharness.mcp").McpConnection,
            importlib.import_module("agentharness.config").McpServer)


def failed(value):
    if isinstance(value, dict):
        if value.get("ok") is False or value.get("success") is False:
            return True
        if value.get("error") or value.get("errors") or value.get("failed"):
            return True
        return any(failed(v) for v in value.values() if isinstance(v, (dict, list)))
    if isinstance(value, list):
        return any(failed(v) for v in value)
    return False


class Session:
    def __init__(self, app, workspace, evidence):
        if app not in APPS:
            raise ValueError(f"unknown Craft engine: {app}")
        binary = executable(APPS[app][0])
        if not binary:
            raise ValueError(f"missing {APPS[app][0]}")
        Connection, Server = backend()
        argv = [binary, "mcp"]
        if app == "vectorcraft":
            argv += ["--headless"]
        elif app == "photocraft":
            argv += ["--automation-read-root", str(workspace), "--automation-write-root", str(workspace)]
        elif app == "pdfcraft":
            argv += ["--root", str(workspace)]
        elif app == "lightcraft":
            argv += ["--compact"]
        self.connection = Connection(Server(app, "stdio", argv=argv, timeout=60), workspace, evidence)
        try:
            self.tools = {t["name"]: t for t in self.connection.list_tools()}
        except BaseException:
            self.connection.close()
            raise
        self.evidence, self.counter = Path(evidence), 0
        self.app, self.workspace = app, Path(workspace).resolve()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.connection.close()

    def call(self, tool, arguments):
        if tool not in self.tools:
            raise ValueError(f"unknown tool {tool}; discover with studio craft tools")
        # PhotoCraft's automation root accepts only relative file paths.
        if self.app == "photocraft":
            arguments = dict(arguments)
            for key in ("path", "paths"):
                if key not in arguments:
                    continue
                values = arguments[key] if isinstance(arguments[key], list) else [arguments[key]]
                normalized = []
                for value in values:
                    path = Path(value)
                    if path.is_absolute():
                        path = path.resolve().relative_to(self.workspace)
                    normalized.append(str(path))
                arguments[key] = normalized if isinstance(arguments[key], list) else normalized[0]
        self.counter += 1
        receipt = self.evidence / f"call-{self.counter:05d}.json"
        record = {"tool": tool, "arguments": arguments, "status": "started"}
        write_json(receipt, record)
        try:
            raw = self.connection.call(tool, arguments)
            try:
                result = json.loads(raw)
            except ValueError:
                result = raw
            record["result"] = result
            if raw.startswith("ERROR:") or failed(result):
                record["status"] = "failed"
                raise ValueError(f"{tool}: {raw[:1200]}")
            record["status"] = "succeeded"
            return result
        except BaseException as exc:
            if record["status"] == "started":
                record["status"] = "unknown"
            record["exception"] = str(exc)
            raise
        finally:
            write_json(receipt, record)


def new_output(path):
    path = Path(path).resolve()
    if path.exists():
        raise ValueError(f"output already exists: {path}; inspect it and choose a new take")
    path.mkdir(parents=True)
    return path


def doctor(out):
    out = new_output(out)
    report = {}
    for app, (binary, purpose) in APPS.items():
        row = report[app] = {"executable": executable(binary), "purpose": purpose}
        try:
            with Session(app, ROOT, out / app) as session:
                write_json(out / app / "tools.json", list(session.tools.values()))
                row.update(status="connected", tools=len(session.tools))
        except Exception as exc:
            row.update(status="unavailable", error=str(exc))
    write_json(out / "report.json", report)
    return report


def run_recipe(recipe_path, out):
    recipe = load_json(recipe_path)
    steps = recipe.get("steps")
    if not isinstance(steps, list) or not steps:
        raise ValueError("recipe requires a nonempty steps list")
    for step in steps:
        if step.get("app") not in APPS or not isinstance(step.get("tool"), str):
            raise ValueError("each step requires an installed app name and tool")
        if not isinstance(step.get("arguments", {}), dict):
            raise ValueError("step arguments must be an object")
    out = new_output(out)
    write_json(out / "recipe.json", recipe)
    status = {"status": "running", "completed_steps": 0, "creative_status": "exploratory"}
    write_json(out / "status.json", status)

    def expand(value):
        if isinstance(value, str):
            return value.replace("${OUT}", str(out)).replace("${ROOT}", str(ROOT))
        if isinstance(value, list):
            return [expand(v) for v in value]
        if isinstance(value, dict):
            return {k: expand(v) for k, v in value.items()}
        return value

    try:
        with ExitStack() as stack:
            sessions = {}
            for step in steps:
                app = step["app"]
                if app not in sessions:
                    sessions[app] = stack.enter_context(Session(app, ROOT, out / "evidence" / app))
                sessions[app].call(step["tool"], expand(step.get("arguments", {})))
                status["completed_steps"] += 1
                write_json(out / "status.json", status)
        for name in recipe.get("outputs", []):
            path = (out / name).resolve()
            if not path.is_relative_to(out) or not path.is_file() or path.stat().st_size == 0:
                raise ValueError(f"missing/nonlocal declared output: {name}")
        status["status"] = "succeeded"
    except BaseException as exc:
        status.update(status="stopped", error=str(exc), recovery="Inspect receipts and saved files; no automatic retry.")
        raise
    finally:
        write_json(out / "status.json", status)
    return {**status, "output": str(out)}


def validate_cels(path):
    from PIL import Image
    path = Path(path).resolve()
    spec = load_json(path)
    w, h = spec.get("width"), spec.get("height")
    if type(w) is not int or type(h) is not int or not (16 <= w <= 7680 and 9 <= h <= 4320):
        raise ValueError("width/height must be positive canvas integers within 7680x4320")
    if w * 9 != h * 16 or w % 2 or h % 2 or spec.get("fps") != 24:
        raise ValueError("Ilan-Anime requires an even 16:9 canvas and 24 fps")
    exposures = spec.get("exposures")
    if not isinstance(exposures, list) or not exposures:
        raise ValueError("exposures must contain {path, frames} drawings")
    paths = []
    for entry in exposures:
        if type(entry.get("frames")) is not int or entry["frames"] <= 0:
            raise ValueError("each drawing needs a positive integer frame exposure")
        paths.append(entry["path"])
    if sum(e["frames"] for e in exposures) > 14400:
        raise ValueError("render one shot at a time (maximum 10 minutes)")
    if spec.get("background"):
        paths.append(spec["background"])
    resolved = {}
    for name in paths:
        source = (path.parent / name).resolve()
        with Image.open(source) as im:
            if im.format != "PNG" or im.size != (w, h):
                raise ValueError(f"{source}: expected full-canvas {w}x{h} PNG; register cels first")
        resolved[name] = source
    return spec, resolved


def render_cels(manifest, out):
    spec, sources = validate_cels(manifest)
    ffmpeg, ffprobe = executable("ffmpeg"), executable("ffprobe")
    if not ffmpeg or not ffprobe:
        raise ValueError("FFmpeg and ffprobe are required")
    out = new_output(out)
    write_json(out / "source-manifest.json", spec)
    state = {"status": "running", "creative_status": "exploratory", "frames": 0}
    write_json(out / "status.json", state)
    try:
        inputs, provenance = {}, []
        (out / "inputs").mkdir()
        (out / "frames").mkdir()
        for i, (name, source) in enumerate(sources.items()):
            # Numbered siblings are auto-imported as an image sequence by EffectCraft.
            # Non-numeric basenames keep every exposure a distinct still drawing.
            target = out / "inputs" / f"drawing_{sha256(source)}_still.png"
            shutil.copy2(source, target)
            inputs[name] = str(target)
            provenance.append({"source": str(source), "copy": str(target), "sha256": sha256(target)})
        write_json(out / "inputs.json", provenance)
        frames = sum(e["frames"] for e in spec["exposures"])
        cursor, exposures = 0, []
        for entry in spec["exposures"]:
            exposures.append({"start": cursor, "end": cursor + entry["frames"], "source": inputs[entry["path"]]})
            cursor += entry["frames"]
        layers = []
        if spec.get("background"):
            layers.append({"name": "background", "source": inputs[spec["background"]], "rate": 1})
        layers.append({"name": "cels", "exposures": exposures, "rate": 1})
        write_json(out / "studio-shot.json", {"id": spec.get("shot", "craft-draft"),
                   "size": [spec["width"], spec["height"]], "fps": 24, "frames": frames,
                   "status": "exploratory", "stage": "draft", "layers": layers})
        with Session("effectcraft", ROOT, out / "evidence/effectcraft") as ec:
            ec.call("open_project", {"new": True})
            ec.call("execute_command", {"command": "comp.new", "params": {
                "name": spec.get("shot", "Cel draft"), "width": spec["width"], "height": spec["height"],
                "frameRate": 24, "duration": frames / 24}})
            ec.call("execute_command", {"command": "file.import", "params": {"paths": list(dict.fromkeys(inputs.values()))}})
            project = ec.call("get_project", {})
            if any(item["type"] == "Image Sequence" for item in project["items"]):
                raise ValueError("engine interpreted a cel as an image sequence; explicit stills required")
            items = {item["name"]: item["id"] for item in project["items"] if item["type"] != "Composition"}

            def add(name, start, duration):
                return ec.call("execute_command", {"command": "layer.addItem", "params": {
                    "item": items[Path(inputs[name]).name], "time": start / 24, "duration": duration / 24}})

            if spec.get("background"):
                add(spec["background"], 0, frames)
            cursor = 0
            for entry in spec["exposures"]:
                add(entry["path"], cursor, entry["frames"])
                cursor += entry["frames"]
            ec.call("save_project", {"path": str(out / "shot.ecproj")})
            for frame in range(frames):
                ec.call("render_frame", {"time": frame / 24, "path": str(out / "frames" / f"{frame:06d}.png"),
                                          "max_side": 0, "inline": False})
                state["frames"] = frame + 1
                write_json(out / "status.json", state)
        subprocess.run([ffmpeg, "-v", "error", "-n", "-framerate", "24", "-start_number", "0",
                        "-i", str(out / "frames/%06d.png"), "-frames:v", str(frames), "-c:v", "libx264",
                        "-pix_fmt", "yuv420p", "-crf", "18", str(out / "preview.mp4")], check=True, timeout=600)
        probe = json.loads(subprocess.check_output([ffprobe, "-v", "error", "-count_frames",
                "-select_streams", "v:0", "-show_streams", "-of", "json", str(out / "preview.mp4")], timeout=60))
        stream = probe["streams"][0]
        if (int(stream["nb_read_frames"]) != frames or stream["r_frame_rate"] != "24/1"
                or (stream["width"], stream["height"]) != (spec["width"], spec["height"])):
            raise ValueError("encoded preview does not match exposure manifest")
        write_json(out / "probe.json", probe)
        with Session("filmcraft", ROOT, out / "evidence/filmcraft") as fc:
            imported = fc.call("media_import", {"text": str(out / "preview.mp4")})
            fc.call("command_run", {"id": "file.newSequence", "params": {
                "name": spec.get("shot", "Cel draft"), "width": spec["width"], "height": spec["height"],
                "fps": 24, "fromItem": imported["items"][0]}})
            fc.call("command_run", {"id": "file.saveAs", "params": {"path": str(out / "edit.filmcraft")}})
            timeline = fc.call("sequence_inspect", {})
            write_json(out / "timeline.json", timeline)
            settings = timeline["settings"]
            if (timeline["durationFrames"] != frames or settings["frame_rate"] != {"num": 24, "den": 1}
                    or (settings["width"], settings["height"]) != (spec["width"], spec["height"])):
                raise ValueError("FilmCraft sequence does not match the exposure manifest")
        for name in ("shot.ecproj", "edit.filmcraft", "preview.mp4"):
            if not (out / name).is_file() or (out / name).stat().st_size == 0:
                raise ValueError(f"missing saved artifact: {name}")
        state.update(status="succeeded", output=str(out), review="Inspect motion and contacts; no creative approval recorded.")
    except BaseException as exc:
        state.update(status="stopped", error=str(exc), recovery="Inspect saved project and receipts; use a new take for revisions.")
        raise
    finally:
        write_json(out / "status.json", state)
    return state


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python -m studio craft", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("doctor", help="initialize all seven engines and save live tool schemas")
    p.add_argument("--out", required=True)
    p = sub.add_parser("tools", help="discover live schemas for one engine")
    p.add_argument("app", choices=APPS)
    p.add_argument("--query", default="")
    p.add_argument("--out", required=True)
    p = sub.add_parser("run", help="execute a JSON recipe; state persists across its steps")
    p.add_argument("recipe")
    p.add_argument("--out", required=True)
    p = sub.add_parser("cels", help="PNG exposures → EffectCraft → frames/MP4 → FilmCraft")
    p.add_argument("manifest")
    p.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "doctor":
            result = doctor(args.out)
            print(json.dumps(result, indent=2))
            if any(r["status"] != "connected" for r in result.values()):
                raise SystemExit(1)
            return
        if args.command == "tools":
            out = new_output(args.out)
            with Session(args.app, ROOT, out) as session:
                result = [v for v in session.tools.values() if args.query.lower() in
                          (v["name"] + " " + v.get("description", "")).lower()]
                write_json(out / "tools.json", result)
        elif args.command == "run":
            result = run_recipe(args.recipe, args.out)
        else:
            result = render_cels(args.manifest, args.out)
        print(json.dumps(result, indent=2))
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        raise SystemExit(f"craft: {exc}") from exc
