"""Opt-in paid generation: drawings (OpenAI Images) and voices (OpenAI TTS).

Consistency is enforced by construction, not by hoping:

* every image request is an *edit* that carries the approved references you
  pass (model sheets, the layout, the previous key), so identity comes from
  your drawings rather than from the prompt;
* the art-direction contract's global rules are prepended to every prompt;
* rigid props are never generated per frame - they are separate fixed layers;
* outputs land in the task's output_dir as ``exploratory`` with a provenance
  sidecar; nothing generated is ever production until reviewed and approved.

Voices use only built-in synthetic voices from ``policy.voice.cast``; no
cloning or imitation of a real person. The disclosure line is mandatory.
"""
from __future__ import annotations

import base64
import hashlib
import json
import mimetypes
import os
from pathlib import Path
import urllib.error
import urllib.request
import uuid

from studio import policy as pol
from studio.paths import ROOT, load_json, rel, sha256, write_json

API = "https://api.openai.com/v1"


class GenerationError(RuntimeError):
    pass


def _task(run, task_id):
    ledger = ROOT / "production" / "runs" / run / "ledger.json"
    if not ledger.exists():
        raise GenerationError(f"no ledger for run {run}")
    task = load_json(ledger)["tasks"].get(task_id)
    if not task:
        raise GenerationError(f"unknown task {task_id} in run {run}")
    return task


def _inside_output(task, out):
    out = Path(out).resolve()
    allowed = (ROOT / task["output_dir"]).resolve()
    try:
        out.relative_to(allowed)
    except ValueError as exc:
        raise GenerationError(f"output must be inside the task output_dir {task['output_dir']}") from exc
    return out


def art_preamble(mode=None):
    contract = load_json(ROOT / "production" / "art_direction.json")
    rules = contract["global_rules"]
    parts = [f"{k.replace('_', ' ').capitalize()}: {rules[k]}" for k in
             ("visual_language", "line", "faces", "color", "text", "geometry", "layers") if k in rules]
    if mode and mode in contract.get("modes", {}):
        parts += [f"Mode {mode}: " + "; ".join(contract["modes"][mode].get("constraints", []))]
    parts.append("Match the attached reference drawings exactly for identity, costume, props and line character.")
    return "\n".join(parts)


def _multipart(fields, files):
    boundary = uuid.uuid4().hex
    body = bytearray()
    for name, value in fields.items():
        body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n{value}\r\n".encode()
    for name, path in files:
        mime = mimetypes.guess_type(str(path))[0] or "image/png"
        body += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"; "
                 f"filename=\"{Path(path).name}\"\r\nContent-Type: {mime}\r\n\r\n").encode()
        body += Path(path).read_bytes() + b"\r\n"
    body += f"--{boundary}--\r\n".encode()
    return bytes(body), f"multipart/form-data; boundary={boundary}"


def _post(url, key, body, content_type, timeout=600):
    request = urllib.request.Request(url, data=body, method="POST",
                                     headers={"Authorization": f"Bearer {key}", "Content-Type": content_type})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read(), dict(response.headers)
    except urllib.error.HTTPError as exc:
        raise GenerationError(f"API {exc.code}: {exc.read()[:500].decode(errors='replace')}") from exc


def image(*, run, task_id, prompt_file, refs, out, mode=None, dry_run=False, transport=_post):
    task = _task(run, task_id)
    roles = load_json(ROOT / "production" / "roles.json")
    policy = pol.load()
    cfg = policy.get("generation", {}).get("image", {})
    estimate = cfg.get("estimated_usd_per_image")
    out = _inside_output(task, out)
    refs = [Path(r) for r in refs]
    for ref in refs:
        if not ref.is_file():
            raise GenerationError(f"missing reference {ref}")
    prompt = art_preamble(mode or task.get("art_direction_mode")) + "\n\n" + Path(prompt_file).read_text()
    request = {"model": cfg.get("model"), "size": cfg.get("size", "1536x1024"), "quality": cfg.get("quality", "high"),
               "background": cfg.get("background", "transparent"), "n": 1}
    record = {"kind": "image", "task_id": task_id, "run": run, "model": request["model"],
              "estimated_usd": estimate, "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
              "references": {rel(r): sha256(r) for r in refs}, "output": rel(out)}
    if dry_run:
        return {"dry_run": True, "endpoint": "edits" if refs else "generations", **request, **record,
                "prompt": prompt}
    pol.authorize("image", estimate, task, roles[task["role"]].get("generate", []), policy)
    key = os.environ.get(policy["generation"].get("api_key_env", "OPENAI_API_KEY"))
    if not key:
        raise GenerationError("API key environment variable is not set")
    pol.append({**record, "status": "sent"})
    try:
        if refs:
            body, ctype = _multipart({**request, "prompt": prompt}, [("image[]", r) for r in refs])
            raw, _ = transport(f"{API}/images/edits", key, body, ctype)
        else:
            raw, _ = transport(f"{API}/images/generations", key,
                               json.dumps({**request, "prompt": prompt}).encode(), "application/json")
        data = json.loads(raw)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(base64.b64decode(data["data"][0]["b64_json"]))
    except Exception as exc:
        pol.append({**record, "status": "failed-after-send", "error": str(exc)[:300]})
        raise
    pol.append({**record, "status": "ok", "output_sha256": sha256(out)})
    sidecar = {**record, "state": "exploratory", "output_sha256": sha256(out), "prompt": prompt,
               "truth": "Generated drawing: exploratory until independently reviewed and approved by Luis."}
    write_json(out.with_name(out.name + ".provenance.json"), sidecar)
    return sidecar


def voice(*, run, task_id, line_id, out, dialogue=None, dry_run=False, transport=_post):
    task = _task(run, task_id)
    roles = load_json(ROOT / "production" / "roles.json")
    policy = pol.load()
    cfg = policy.get("generation", {}).get("voice", {})
    dialogue = Path(dialogue or ROOT / "projects/cemi_episode_01/data/dialogue.json")
    lines = {item["id"]: item for item in load_json(dialogue)["lines"]}
    if line_id not in lines:
        raise GenerationError(f"unknown line {line_id} in {rel(dialogue)}")
    line = lines[line_id]
    if line.get("speaker_inferred") or not line.get("speaker"):
        raise GenerationError(f"{line_id}: speaker not confirmed by the script supervisor")
    cast = cfg.get("cast", {})
    if line["speaker"] not in cast:
        raise GenerationError(f"{line['speaker']} has no synthetic voice in policy.generation.voice.cast")
    rate = cfg.get("estimated_usd_per_1k_chars")
    estimate = None if rate is None else round(rate * max(1, len(line["text"])) / 1000, 6)
    out = _inside_output(task, out)
    voice_cfg = cast[line["speaker"]]
    body = {"model": cfg.get("model"), "voice": voice_cfg.get("voice") if isinstance(voice_cfg, dict) else voice_cfg,
            "input": line["text"], "response_format": cfg.get("format", "wav")}
    if isinstance(voice_cfg, dict) and voice_cfg.get("instructions"):
        body["instructions"] = voice_cfg["instructions"]
    if line.get("direction"):
        body["instructions"] = (body.get("instructions", "") + " " + line["direction"]).strip()
    record = {"kind": "voice", "task_id": task_id, "run": run, "model": body["model"], "voice": body["voice"],
              "line_id": line_id, "estimated_usd": estimate, "output": rel(out),
              "disclosure": cfg.get("disclosure")}
    if dry_run:
        return {"dry_run": True, **record, "request": body}
    if not cfg.get("disclosure"):
        raise GenerationError("policy.generation.voice.disclosure is required for AI voices")
    pol.authorize("voice", estimate, task, roles[task["role"]].get("generate", []), policy)
    key = os.environ.get(policy["generation"].get("api_key_env", "OPENAI_API_KEY"))
    if not key:
        raise GenerationError("API key environment variable is not set")
    pol.append({**record, "status": "sent"})
    try:
        raw, _ = transport(f"{API}/audio/speech", key, json.dumps(body).encode(), "application/json")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(raw)
    except Exception as exc:
        pol.append({**record, "status": "failed-after-send", "error": str(exc)[:300]})
        raise
    pol.append({**record, "status": "ok", "output_sha256": sha256(out)})
    sidecar = {**record, "state": "exploratory", "text": line["text"], "output_sha256": sha256(out),
               "truth": "Synthetic voice take: temporary until approved; credit must carry the disclosure."}
    write_json(out.with_name(out.name + ".provenance.json"), sidecar)
    return sidecar
