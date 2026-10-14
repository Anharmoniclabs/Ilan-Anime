"""Full-episode animatic (Leica reel) built from episode.json.

Every one of the 128 shots gets a runnable spec at its exact frame count:

* shots with keyframes hold those paintings (multiple keyframes split the shot
  in order) under the camera move named in the script header or FX tokens;
* shots without art get a slate (shot ID, header, action, sound);
* title/text cards, the sigil, train strobe, speed lines, lane fields, PRESS,
  era grades and vignettes come from the shot's FX tokens.

Tokens that need a time the script doesn't give (flash frames, harmony cuts,
shakes, rings) are listed in ``notes.unplaced_fx`` instead of being guessed.
The animatic is ``exploratory``: it locks timing; it is not animation.
"""
from __future__ import annotations

import re

from studio.paths import EPISODE, PROJECT, load_json, write_json

OVERRIDES = PROJECT / "data" / "animatic_overrides.json"
SHOT_DIR = PROJECT / "data" / "shots"
SIZE = (1280, 720)

SCENE_GRADE = {"S01": "before"}
IMPLEMENTED = {
    "FILM_GRAIN", "GATE_WEAVE", "VIGNETTE", "HALATION", "CHROMA_BLEED", "PRESS", "PERIOD_GRADE",
    "FLASHBACK_GRADE", "WIPE_ERA", "TEXT_SUPER", "SPIRAL_SIGIL", "TRAIN_STROBE", "SPEED_LINES",
    "SPEED_BG", "LANE_FIELD", "PUSH_IN", "PULL_TOWARD", "PAN_STILL", "CRANE_UP", "CAMERA_ROLL",
    "DOLLY_ZOOM", "FADE_OUT", "DISSOLVE", "HOLD_BLACK", "SMASH_CUT_BLACK", "PAINTED_BG",
    "UI_PHONE", "MULTIPLANE", "MULTIPLANE_LATERAL",
}
NEEDS_LAYERS = {"TRANSMITTED_LIGHT", "LIGHT_FIGURE", "AIRBRUSH_RIBBONS", "SOUND_RIBBON", "UI_LAPTOP",
                "MOUTH_FLAP", "CEL_SHADE", "SHADOW_CEL"}
TIMED = {"FLASH_FRAME", "HARMONY_CUT", "CAMERA_SHAKE", "SHOCKWAVE_RING", "DOUBLE_EXPOSURE",
         "IMPACT_FLASH", "FLASH_CUT", "HOLD_FLASH", "HEAT_SHIMMER"}

TOKEN_RE = re.compile(r"([A-Z][A-Z0-9_]*[A-Z0-9↑]?)(\(((?:[^()]|\([^()]*\))*)\))?")


def parse_script(script: str) -> dict:
    lines = script.split("\n")
    header = lines[0]
    fields = {}
    for line in lines[1:]:
        m = re.match(r"- \*\*(\w+):\*\*\s*(.*)", line.strip())
        if m:
            fields[m.group(1).lower()] = m.group(2).strip()
    parts = [p.strip() for p in header.split("·")]
    camera = " · ".join(parts[1:-1]) if len(parts) > 2 else ""
    rate = re.search(r"rate\s*(\d+)s", header)
    fx = []
    m = re.search(r"`([^`]*)`", fields.get("fx", ""))
    if m:
        for token in TOKEN_RE.finditer(m.group(1)):
            fx.append((token.group(1).rstrip("↑"), (token.group(3) or "").strip()))
    return {"header": header.replace("`", ""), "camera": camera, "rate": int(rate.group(1)) if rate else 3,
            "action": fields.get("action", ""), "sound": fields.get("sound", ""), "fx": fx}


def _numbers(text):
    return [float(x) for x in re.findall(r"-?\d+(?:\.\d+)?", text)]


def camera_keys(camera: str, fx, frames: int, size=SIZE):
    """Map script camera notation + camera FX to keys on a held plate."""
    w, h = size
    last = frames - 1
    cam = camera.upper()
    fxd = dict(fx)
    if "ROLL" in cam or "CAMERA_ROLL" in fxd:
        nums = _numbers(fxd.get("CAMERA_ROLL", "") or cam)
        angle = nums[-1] if nums else 12
        return [{"frame": 0, "scale": 1.18, "angle": 0, "ease": "smooth"},
                {"frame": last, "scale": 1.18, "angle": angle}]
    if "DOLLY" in cam or "DOLLY_ZOOM" in fxd:
        return [{"frame": 0, "scale": 1.0, "ease": "smooth"}, {"frame": last, "scale": 1.22}]
    if "WHIP" in cam:
        hold = max(0, last - 6)
        return [{"frame": 0, "x": 0, "scale": 1.12, "ease": "hold"}, {"frame": hold, "x": 0, "scale": 1.12, "ease": "ease_in"},
                {"frame": last, "x": -w * 0.5, "scale": 1.12}]
    if "CRANE UP" in cam or "CRANE_UP" in fxd:
        d = h * 0.06
        return [{"frame": 0, "y": -d, "scale": 1.14, "ease": "smooth"}, {"frame": last, "y": d, "scale": 1.14}]
    if "CRANE DOWN" in cam or "FALLING" in cam:
        d = h * 0.06
        return [{"frame": 0, "y": d, "scale": 1.14, "ease": "smooth"}, {"frame": last, "y": -d, "scale": 1.14}]
    if "PAN" in cam or "TRACK" in cam or "PAN_STILL" in fxd or "MULTIPLANE_LATERAL" in fxd:
        d = w * 0.05
        sign = -1 if "R→L" in cam or "R->L" in cam else 1
        return [{"frame": 0, "x": sign * d, "scale": 1.12, "ease": "smooth"},
                {"frame": last, "x": -sign * d, "scale": 1.12}]
    if "PUSH_IN" in fxd or "PULL_TOWARD" in fxd or "PUSH" in cam or "→" in cam or "RACK" in cam:
        nums = [n for n in _numbers(fxd.get("PUSH_IN", "")) if n < 50]
        amount = nums[0] / 100 if nums else 0.08
        return [{"frame": 0, "scale": 1.0, "ease": "smooth"}, {"frame": last, "scale": 1.0 + amount}]
    return []


def _caps_phrases(text):
    return [m.strip(" .") + ("." if m.strip().endswith(".") else "")
            for m in re.findall(r"((?:[A-ZÁÉÍÓÚÑ0-9:·.'’]{2,}\s*)+)", text) if len(m.strip(" .")) > 2]


def build_spec(shot: dict, overrides: dict, size=SIZE) -> dict:
    parsed = parse_script(shot["script"])
    frames = int(shot["frames"])
    fx = parsed["fx"]
    fxd = dict(fx)
    scene = shot["id"].split("-")[0]
    override = overrides.get(shot["id"], {})
    layers, post = [], {}
    notes = {"unplaced_fx": [], "needs_separated_layers_fx": [], "asset_slot_fx": [], "assumptions": []}
    keyframes = shot.get("keyframes", [])
    is_card = any(k in parsed["camera"].lower() for k in ("text card", "title card", "black"))

    if keyframes:
        n = len(keyframes)
        for i, path in enumerate(keyframes):
            start, end = frames * i // n, frames * (i + 1) // n
            layers.append({"name": f"plate_{i}", "source": path, "fit": "cover", "rate": 1, "smooth": True,
                           "in": start, "out": end, "tags": ["bg"], "parallax": 1.0})
        if n > 1:
            notes["assumptions"].append(f"{n} keyframes split the shot evenly; real cut points are unset")
    elif "SPIRAL_SIGIL" in fxd or is_card or override.get("text"):
        layers.append({"name": "field", "generator": {"type": "solid", "color": override.get("field", "#14202B")},
                       "rate": 3, "screen_space": True})
    else:
        layers.append({"name": "slate", "screen_space": True, "rate": 3, "generator": {
            "type": "slate", "shot": shot["id"], "header": parsed["header"],
            "action": parsed["action"] + ("\nSOUND: " + parsed["sound"] if parsed["sound"] else "")}})

    if "SPIRAL_SIGIL" in fxd and not keyframes:
        nums = _numbers(fxd["SPIRAL_SIGIL"])
        draw = int(nums[0] * 24) if nums else 72
        layers.append({"name": "sigil", "rate": 1, "screen_space": True,
                       "generator": {"type": "sigil", "draw_frames": draw,
                                     "center": override.get("sigil_center", [size[0] / 2, size[1] * 0.42])}})
    if keyframes and ("SPIRAL_SIGIL" in fxd):
        notes["assumptions"].append("keyframe assumed to already show the sigil/title; no procedural overlay")
    for i, card in enumerate(override.get("text", [])):
        layers.append({"name": f"text_{i}", "rate": 3, "screen_space": True, "generator": {"type": "text", **card}})
    if "TEXT_SUPER" in fxd and not override.get("text"):
        arg = fxd["TEXT_SUPER"]
        sup = re.search(r"Super:\s*(.+?)(?:\.\s|$)", parsed["action"])
        text = arg if arg and arg.upper() == arg else (sup.group(1) if sup else "")
        if text:
            layers.append({"name": "super", "rate": 3, "screen_space": True, "generator": {
                "type": "text", "text": [text], "font": "serif", "size": 26, "tracking": 0.3,
                "align": "left", "position": [size[0] * 0.06, size[1] * 0.88]}})
        else:
            notes["unplaced_fx"].append("TEXT_SUPER (text not stated)")
    if "TRAIN_STROBE" in fxd:
        layers.append({"name": "train_strobe", "rate": 1, "screen_space": True, "blend": "screen",
                       "generator": {"type": "train_strobe"}})
    for token in ("SPEED_LINES", "SPEED_BG"):
        if token in fxd:
            direction = "horizontal" if "horizontal" in fxd[token] else "radial"
            layers.append({"name": token.lower(), "rate": 2, "screen_space": True,
                           "generator": {"type": "speed_lines", "direction": direction, "seed": shot["id"]}})
    if "LANE_FIELD" in fxd:
        nums = _numbers(fxd["LANE_FIELD"])
        layers.append({"name": "lanes", "rate": 2, "screen_space": True, "blend": "screen",
                       "generator": {"type": "lanes", "lanes": int(nums[0]) if nums else 6}})

    # ---- post
    post["grade"] = SCENE_GRADE.get(scene)
    if "PERIOD_GRADE" in fxd or "WIPE_ERA" in fxd:
        year = re.search(r"19\d\d", fxd.get("PERIOD_GRADE", "") + " " + parsed["action"])
        if year and year.group(0) in ("1934", "1957", "1973"):
            if "WIPE_ERA" in fxd:
                present_first = "reverse" not in fxd["WIPE_ERA"]
                a, b = ("present", year.group(0)) if present_first else (year.group(0), "present")
                mid = frames // 2
                post["grade"] = [{"frame": 0, "grade": a}, {"frame": mid, "grade": b, "blend": 24}]
                notes["assumptions"].append("WIPE_ERA placed at mid-shot over 24f")
            else:
                post["grade"] = year.group(0)
    if "FLASHBACK_GRADE" in fxd:
        post["grade"] = "flashback"
    if post.get("grade") is None:
        post.pop("grade")
    if "VIGNETTE" in fxd:
        nums = _numbers(fxd["VIGNETTE"])
        post["vignette"] = nums[0] if nums else 0.3
    if "HALATION" in fxd:
        post["halation"] = 0.5
    if "PRESS" in fxd:
        arg = fxd["PRESS"]
        nums = [n for n in _numbers(arg) if 0 <= n <= 1]
        if "audio only" in arg:
            notes["unplaced_fx"].append("PRESS (audio only; see sound mix)")
        elif len(nums) >= 2:
            post["press"] = [{"frame": 0, "value": nums[0]}, {"frame": frames - 1, "value": nums[1]}]
        elif nums:
            post["press"] = nums[0]
        if "UI only" in arg:
            notes["assumptions"].append("PRESS limited to UI in script; applied globally in animatic")
    if "FADE_OUT" in fxd:
        nums = _numbers(fxd["FADE_OUT"])
        length = int(nums[0]) if nums else 24
        post.setdefault("fade", []).append({"start": max(0, frames - length), "end": frames, "to": "black"})
    if "DISSOLVE" in fxd and is_card:
        nums = _numbers(fxd["DISSOLVE"])
        length = int(nums[0]) if nums else 24
        post.setdefault("fade", []).append({"start": 0, "end": min(frames, length), "to": "black", "dir": "in"})
    if "HOLD_BLACK" in fxd or "SMASH_CUT_BLACK" in fxd:
        notes["unplaced_fx"].append("HOLD_BLACK/SMASH_CUT_BLACK (cut point not stated)")
    if "UI_PHONE" in fxd and not keyframes:
        notes["unplaced_fx"].append("UI_PHONE (message text/timing belong in a UI spec)")

    for name, _arg in fx:
        if name in TIMED:
            notes["unplaced_fx"].append(name)
        elif name in NEEDS_LAYERS:
            notes["needs_separated_layers_fx"].append(name)
        elif name not in IMPLEMENTED:
            notes["asset_slot_fx"].append(name)
    notes = {k: sorted(set(v)) for k, v in notes.items() if v}
    return {
        "id": shot["id"], "size": list(size), "frames": frames, "fps": 24,
        "status": shot.get("status", "missing_art"), "stage": "animatic",
        "animation_status": shot.get("animation_status", "not_rigged"),
        "action": parsed["action"], "camera_note": parsed["camera"], "drawing_rate": parsed["rate"],
        "layers": layers, "camera": camera_keys(parsed["camera"], fx, frames, size),
        "post": post, "audio": None, "notes": notes,
        "truth": "Animatic spec: held keyframes, slates and procedural FX. Not production animation.",
    }


def build_all(write=True, shots=None):
    episode = load_json(EPISODE)
    overrides = load_json(OVERRIDES) if OVERRIDES.exists() else {}
    specs, start = [], 0
    for shot in episode["shots"]:
        frames = int(shot["frames"])
        if shots is None or shot["id"] in shots:
            spec = build_spec(shot, overrides, (episode.get("width", 1280), episode.get("height", 720)))
            if write:
                path = SHOT_DIR / f"{shot['id']}.json"
                existing = load_json(path) if path.exists() else {}
                for keep in ("required_layers", "motion_review"):
                    if keep in existing:
                        spec[keep] = existing[keep]
                write_json(path, spec)
            specs.append((shot["id"], spec, start))
        start += frames
    return specs
