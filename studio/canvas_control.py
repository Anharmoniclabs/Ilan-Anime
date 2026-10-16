"""Shot-wide 2D canvas editor for the existing Ilan-Anime compositor.

Open a real episode shot, inspect EVERY layer and camera at any frame, key
position/rotation/scale/opacity, reorder layers, inspect screen-space bounds,
audit source coverage, then save a NEW exploratory shot spec. The source shot
and all source art remain untouched. Character transforms are placement only:
changing angle/scale on character art is deliberately blocked.
"""
from __future__ import annotations

import argparse
import copy
import io
import json
import math
import re
import secrets
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from studio.engine.compositor import Compositor, CAMERA_DEFAULTS, LAYER_DEFAULTS, interpolate
from studio.paths import PROJECT, ROOT, load_json, resolve, write_json

SHOT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,55}$")
TRANSFORMS = {"x", "y", "scale", "angle", "opacity"}
LIMITS = {
    "x": (-5000, 5000), "y": (-5000, 5000),
    "scale": (0.1, 5.0), "angle": (-360, 360), "opacity": (0, 1),
}
CAMERA_LIMITS = {**LIMITS, "scale": (0.25, 4.0)}


class CanvasError(ValueError):
    pass


def _number(v, key, camera=False):
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
        raise CanvasError(f"{key} must be finite numeric")
    lo, hi = (CAMERA_LIMITS if camera else LIMITS)[key]
    if not lo <= float(v) <= hi:
        raise CanvasError(f"{key} outside [{lo}, {hi}]")
    return float(v)


def _point(matrix, p):
    a, b, c, d, e, f = matrix
    return [round(a * p[0] + b * p[1] + c, 3), round(d * p[0] + e * p[1] + f, 3)]


def layer_geometry(comp, frame):
    """Source-image bounds projected through parents, camera and parallax."""
    f = comp.post.source_frame(frame)
    press = comp._press(f)
    camera = comp.camera(f)
    result = []
    for layer in comp.layers:
        state = comp.layer_state(layer, f, press)
        if state is None:
            continue
        token, _, params = state
        if token[0] == "gen":
            size = comp.spec_size
        else:
            size = comp._load(token[1], layer["fit"]).size
        matrix = comp._matrix(layer, size, params, camera, press, f)
        # Exact pixel-to-key translation basis including parent chain and camera.
        px = dict(params, x=float(params["x"]) + 1)
        py = dict(params, y=float(params["y"]) + 1)
        mx = comp._matrix(layer, size, px, camera, press, f)
        my = comp._matrix(layer, size, py, camera, press, f)
        basis = [
            [round(mx[2] - matrix[2], 7), round(mx[5] - matrix[5], 7)],
            [round(my[2] - matrix[2], 7), round(my[5] - matrix[5], 7)],
        ]
        w, h = size
        polygon = [_point(matrix, p) for p in ((0, 0), (w, 0), (w, h), (0, h))]
        xs, ys = [p[0] for p in polygon], [p[1] for p in polygon]
        left, top, right, bottom = min(xs), min(ys), max(xs), max(ys)
        cw, ch = comp.size
        visible = max(0.0, min(cw, right) - max(0.0, left)) * max(0.0, min(ch, bottom) - max(0.0, top))
        bounds = {"left": left, "top": top, "right": right, "bottom": bottom}
        result.append({
            "name": layer["name"], "tags": layer["tags"], "polygon": polygon,
            "bounds": bounds,
            "off_canvas": visible == 0,
            "partial": left < 0 or top < 0 or right > cw or bottom > ch,
            "source": token[1] if token[0] == "img" else "[generated]",
            "params": params, "translation_basis": basis, "parallax": layer["parallax"],
        })
    return result


class CanvasSession:
    def __init__(self, project=PROJECT, repo=ROOT):
        self.project = Path(project).resolve()
        self.repo = Path(repo).resolve()
        self.spec_root = self.project / "data" / "shots"
        self.shot = None
        self.original = None
        self.spec = None
        self.edits = []
        self.revision = 0
        self._lock = threading.RLock()

    def shots(self):
        return [p.stem for p in sorted(self.spec_root.glob("*.json")) if SHOT_RE.fullmatch(p.stem)]

    def select(self, shot):
        if not isinstance(shot, str) or not SHOT_RE.fullmatch(shot):
            raise CanvasError("invalid shot name")
        path = self.spec_root / f"{shot}.json"
        if not path.is_file():
            raise CanvasError("unknown shot")
        spec = load_json(path)
        if not isinstance(spec.get("layers"), list) or not spec.get("frames"):
            raise CanvasError("shot does not have a renderable spec")
        if spec.get("id", shot) != shot:
            raise CanvasError("shot ID does not match its file")
        with self._lock:
            self.shot, self.original, self.spec = shot, copy.deepcopy(spec), spec
            self.edits, self.revision = [], self.revision + 1
            return self.state()

    def state(self):
        if self.spec is None:
            raise CanvasError("select a shot first")
        return {
            "shot": self.shot, "size": self.spec.get("size", [1280, 720]),
            "fps": int(self.spec.get("fps", 24)), "frames": int(self.spec["frames"]),
            "stage": self.original.get("stage", "unknown"),
            "status": "exploratory-preview", "source_status": self.original.get("status", "unknown"),
            "camera": self.spec.get("camera", []),
            "layers": [{"name": x["name"], "tags": x.get("tags", []),
                        "rate": x.get("rate", 3), "parallax": x.get("parallax", 1),
                        "source_type": "sequence" if x.get("sequence") else (
                            "exposures" if x.get("exposures") else (
                                "generator" if x.get("generator") else "source")),
                        "drawings": len(x.get("sequence", [])) or len(x.get("exposures", [])) or (1 if x.get("source") else 0),
                        "keys": x.get("keys", []), "opacity": x.get("opacity", 1),
                        "parent": x.get("parent")} for x in self.spec["layers"]],
            "edited": len(self.edits), "revision": self.revision,
            "approval": "not granted", "truth": "Scene-wide transform preview is not new character acting.",
        }

    def _layer(self, name):
        return next((l for l in self.spec["layers"] if l["name"] == name), None)

    def edit(self, patch):
        """Explicit single-frame key or whole-layer property; no raster mutation."""
        if not isinstance(patch, dict):
            raise CanvasError("edit payload must be an object")
        with self._lock:
            if self.spec is None:
                raise CanvasError("select a shot first")
            target = patch.get("target")
            if target not in ("camera", "layer"):
                raise CanvasError("target must be camera or layer")
            prop = patch.get("property")
            frame = patch.get("frame")
            if type(frame) is not int or not 0 <= frame < int(self.spec["frames"]):
                raise CanvasError("frame outside shot")
            if target == "camera":
                if prop not in {"x", "y", "scale", "angle"}:
                    raise CanvasError("invalid camera property")
                layer = None
                keys = self.spec.setdefault("camera", [])
                defaults = CAMERA_DEFAULTS
            else:
                layer = self._layer(patch.get("layer"))
                if layer is None:
                    raise CanvasError("unknown layer")
                if prop not in TRANSFORMS and prop not in {"parallax", "base_opacity"}:
                    raise CanvasError("invalid layer property")
                if "character" in layer.get("tags", []) and prop in ("scale", "angle"):
                    raise CanvasError("character scaling/rotation is not acting: provide redrawn cel exposures")
                if prop == "parallax":
                    value = patch.get("value")
                    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 3:
                        raise CanvasError("parallax must be between 0 and 3")
                    layer["parallax"] = float(value)
                    self.edits.append({"layer": layer["name"], "property": prop, "value": value})
                    self.revision += 1
                    return self.state()
                if prop == "base_opacity":
                    value = _number(patch.get("value"), "opacity")
                    layer["opacity"] = value
                    self.edits.append({"layer": layer["name"], "property": prop, "value": value})
                    self.revision += 1
                    return self.state()
                # Held cels do not read keys off their exposure clock.
                # Snap edits to the active layer's frame grid; camera is 1s.
                start = int(layer.get("in", 0))
                end = int(layer.get("out", self.spec["frames"]))
                if not start <= frame < end:
                    raise CanvasError("cannot key an inactive layer at this frame")
                rate = int(layer.get("rate", 3))
                if rate < 1:
                    raise CanvasError("invalid drawing exposure rate")
                if not layer.get("smooth"):
                    frame = start + ((frame - start) // rate) * rate
                keys = layer.setdefault("keys", [])
                defaults = LAYER_DEFAULTS
            value = _number(patch.get("value"), prop, target == "camera")
            # Insert a COMPLETE interpolated pose so unrelated fields do not jump.
            current = interpolate(keys, frame, defaults)
            current[prop] = value
            existing = next((k for k in keys if k["frame"] == frame), None)
            if existing is not None:
                current["ease"] = existing.get("ease", "smooth")
                keys.remove(existing)
            else:
                current["ease"] = "smooth"
            keys.append(dict(current, frame=frame))
            keys.sort(key=lambda k: k["frame"])
            self.edits.append({"target": target, "layer": layer["name"] if layer else None,
                               "frame": frame, "property": prop, "value": value})
            self.revision += 1
            return self.state()

    def reorder(self, name, direction):
        with self._lock:
            idx = next((i for i, l in enumerate(self.spec["layers"]) if l["name"] == name), None)
            if idx is None or direction not in (-1, 1):
                raise CanvasError("invalid layer/reorder direction")
            neighbor = idx + direction
            if not 0 <= neighbor < len(self.spec["layers"]):
                raise CanvasError("layer already at stack boundary")
            self.spec["layers"][idx], self.spec["layers"][neighbor] = (
                self.spec["layers"][neighbor], self.spec["layers"][idx])
            self.edits.append({"target": "stack", "layer": name, "direction": direction})
            self.revision += 1
            return self.state()

    def inventory(self):
        """Fast structural preflight of EVERY episode shot. No rendered-acting claims."""
        rows = []
        for shot in self.shots():
            try:
                spec = load_json(self.spec_root / f"{shot}.json")
                layers = spec.get("layers", [])
                missing = []
                drawing_counts = {}
                for layer in layers:
                    paths = ([layer["source"]] if layer.get("source") else []) + (
                        list(layer.get("sequence") or [])) + [
                        e["source"] for e in layer.get("exposures", [])
                    ]
                    distinct = len(set(paths))
                    drawing_counts[layer.get("name", "?")] = distinct
                    for name in set(paths):
                        if not resolve(name, self.project).is_file():
                            missing.append(name)
                characters = [l for l in layers if "character" in l.get("tags", [])]
                acting = sum(drawing_counts.get(l.get("name"), 0) >= 2 for l in characters)
                rows.append({"shot": shot, "frames": spec.get("frames"),
                             "stage": spec.get("stage", "unknown"),
                             "layers": len(layers), "characters": len(characters),
                             "characters_with_multiple_drawings": acting,
                             "missing_sources": sorted(set(missing)),
                             "motion_evidence": "multi-drawing present" if acting else "not demonstrated"})
            except (OSError, ValueError, KeyError, TypeError) as exc:
                rows.append({"shot": shot, "error": str(exc),
                             "missing_sources": [], "motion_evidence": "invalid spec"})
        return {
            "shot_count": len(rows), "shots": rows,
            "invalid_specs": sum(bool(x.get("error")) for x in rows),
            "shots_with_missing_files": sum(bool(x["missing_sources"]) for x in rows),
            "shots_without_character_action_evidence":
                sum(x["motion_evidence"] != "multi-drawing present" for x in rows),
            "scope": "structural source/drawing inventory only; not per-shot artwork certification",
            "author_approved": False,
        }

    def _comp(self):
        return Compositor(copy.deepcopy(self.spec), base=self.project, quality="draft", scale=0.5)

    def preview(self, frame):
        with self._lock:
            if type(frame) is not int or not 0 <= frame < int(self.spec["frames"]):
                raise CanvasError("frame outside shot")
            comp = self._comp()
            img = comp.draw(frame)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            bounds = layer_geometry(comp, frame)
            return buf.getvalue(), bounds

    def bounds(self, frame):
        with self._lock:
            if type(frame) is not int or not 0 <= frame < int(self.spec["frames"]):
                raise CanvasError("frame outside shot")
            return layer_geometry(self._comp(), frame)

    def audit(self, sample=24):
        """Whole-shot sampled screen-space geometry + established acting test.

        A bounding box is not pixel-accurate alpha coverage. This is a
        diagnostic, not independent final animation/identity approval.
        """
        if type(sample) is not int or not 1 <= sample <= 120:
            raise CanvasError("sample must be 1..120")
        with self._lock:
            comp = self._comp()
            frames = int(self.spec["frames"])
            choices = sorted(set([0, frames - 1] + list(range(0, frames, sample))))
            if len(choices) > 1200:
                raise CanvasError("too many audit frames")
            samples, errors = [], []
            for frame in choices:
                try:
                    boxes = layer_geometry(comp, frame)
                    samples.append({"frame": frame, "off_canvas": [b["name"] for b in boxes if b["off_canvas"]],
                                    "partial": [b["name"] for b in boxes if b["partial"]],
                                    "active_layers": len(boxes)})
                except (OSError, ValueError) as exc:
                    errors.append({"frame": frame, "error": str(exc)})
            try:
                from studio.qa import acting_flags
                acting = acting_flags(self.spec)
            except (ImportError, KeyError) as exc:
                acting = [{"type": "unknown", "detail": str(exc)}]
            return {
                "shot": self.shot, "samples": samples, "errors": errors,
                "no_acting": acting, "edits": len(self.edits),
                "source_files_untouched": True,
                "coverage": "geometric bounds only, not opaque pixel coverage",
                "visual_quality": "not_assessed", "character_identity": "not_assessed",
                "status": "technical_preflight_only", "author_approved": False,
            }

    def save(self):
        """Save an explicit NEW exploratory take; never rewrite shot inputs."""
        with self._lock:
            if self.spec is None or not self.edits:
                raise CanvasError("nothing to save; change camera or layer first")
            name = f"{self.shot}-canvas-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}-{secrets.token_hex(3)}"
            dest = self.repo / "production" / "engineering" / "canvas-takes" / name
            dest.mkdir(parents=True, exist_ok=False)
            draft = copy.deepcopy(self.spec)
            draft["status"], draft["author_approved"] = "exploratory", False
            draft["truth"] = "Edited shot layout/camera/layer transforms; no new acting drawings generated or approved."
            write_json(dest / "shot.draft.json", draft)
            write_json(dest / "edits.json", {"source": str(self.spec_root / f"{self.shot}.json"),
                                             "edits": copy.deepcopy(self.edits),
                                             "source_unchanged": True, "approval": False})
            write_json(dest / "canvas-audit.json", self.audit())
            return {"take": str(dest), "spec": str(dest / "shot.draft.json"),
                    "audit": str(dest / "canvas-audit.json"), "approved": False}


class CanvasHandler(BaseHTTPRequestHandler):
    session: CanvasSession = None  # assigned by serve()

    def _send(self, code, data, mime="application/json"):
        payload = json.dumps(data, ensure_ascii=False).encode() if mime == "application/json" else data
        self.send_response(code)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'")
        self.end_headers()
        self.wfile.write(payload)

    def _query(self):
        return urlparse(self.path), parse_qs(urlparse(self.path).query)

    def do_GET(self):
        try:
            url, query = self._query()
            if url.path == "/":
                html = (ROOT / "production" / "canvas_control.html").read_bytes()
                return self._send(200, html, "text/html; charset=utf-8")
            if url.path == "/api/shots":
                return self._send(200, {"shots": self.session.shots()})
            if url.path == "/api/select":
                return self._send(200, self.session.select(query.get("shot", [""])[0]))
            if url.path == "/api/state":
                return self._send(200, self.session.state())
            if url.path == "/api/inventory":
                return self._send(200, self.session.inventory())
            if url.path in ("/api/frame", "/api/bounds"):
                frame = int(query.get("frame", ["0"])[0])
                if url.path == "/api/bounds":
                    return self._send(200, {"bounds": self.session.bounds(frame)})
                frame_bytes, _ = self.session.preview(frame)
                return self._send(200, frame_bytes, "image/png")
            if url.path == "/api/audit":
                return self._send(200, self.session.audit(sample=int(query.get("step", ["24"])[0])))
            return self._send(404, {"error": "not found"})
        except (CanvasError, ValueError, OSError, KeyError, TypeError) as exc:
            return self._send(400, {"error": str(exc)})

    def do_POST(self):
        try:
            host = self.headers.get("Host", "")
            origin = self.headers.get("Origin")
            if origin and urlparse(origin).netloc != host:
                return self._send(403, {"error": "cross-origin writes blocked"})
            count = int(self.headers.get("Content-Length", "0"))
            if not 0 < count <= 8192:
                return self._send(413, {"error": "invalid request size"})
            if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                return self._send(415, {"error": "JSON required"})
            data = json.loads(self.rfile.read(count))
            path = urlparse(self.path).path
            if path == "/api/edit":
                return self._send(200, self.session.edit(data))
            if path == "/api/reorder":
                return self._send(200, self.session.reorder(data.get("layer"), data.get("direction")))
            if path == "/api/save":
                return self._send(200, self.session.save())
            return self._send(404, {"error": "not found"})
        except (CanvasError, ValueError, OSError, KeyError, TypeError) as exc:
            return self._send(400, {"error": str(exc)})

    def log_message(self, fmt, *args):
        if not self.path.startswith("/api/frame"):
            super().log_message(fmt, *args)


def serve(host="127.0.0.1", port=8766):
    CanvasHandler.session = CanvasSession()
    address = (host, port)
    with ThreadingHTTPServer(address, CanvasHandler) as server:
        print(f"Full-canvas shot editor listening on http://{host}:{port}")
        print("Keep any forwarded Codespaces port PRIVATE. Saves are new exploratory takes.")
        server.serve_forever()


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("serve", nargs="?", default="serve")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8766)
    a = p.parse_args(argv)
    if not 1024 <= a.port <= 65535:
        p.error("port must be between 1024 and 65535")
    serve(a.host, a.port)


if __name__ == "__main__":
    main()
