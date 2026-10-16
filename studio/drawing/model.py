"""Bounded local-model planning for the drawing engine (Ollama, one model at a time).

Qwen never emits geometry here. It reads one script/action line and chooses
from an enumerated menu (expression name + intensity + gaze). The answer is
schema-validated; a bad answer is retried a bounded number of times and then
fails loudly. Nothing is invented to repair it. Every call writes a receipt
(prompt, raw reply, latency, outcome).
"""
from __future__ import annotations

import json
import time
import urllib.request
from pathlib import Path

from studio.drawing.face import EXPRESSIONS, PARAMS, expression
from studio.drawing.schema import DrawingError
from studio.paths import write_json

OLLAMA = "http://127.0.0.1:11434/api/chat"
MODEL = "qwen2.5-coder:1.5b"
GAZE = {"center": (0.0, 0.0), "left": (-1.0, 0.0), "right": (1.0, 0.0), "down": (0.0, 0.8), "up": (0.0, -0.8)}

PROMPT = """You direct facial acting for an anime character.
Action line: "{line}"
Choose the facial expression for this moment.
expression: one of {names}
intensity: number from 0.0 to 1.0
gaze: one of {gazes}
Reply with only JSON, for example: {{"expression": "fear", "intensity": 0.8, "gaze": "left"}}"""


def _chat(prompt, *, model, timeout, num_predict):
    payload = {"model": model, "stream": False, "format": "json", "keep_alive": "2m",
               "options": {"temperature": 0, "num_ctx": 1024, "num_predict": num_predict},
               "messages": [{"role": "user", "content": prompt}]}
    req = urllib.request.Request(OLLAMA, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp)


def validate_plan(raw):
    """Parse and strictly validate a model reply -> plan dict. Raises DrawingError."""
    try:
        plan = json.loads(raw)
    except (TypeError, json.JSONDecodeError) as exc:
        raise DrawingError(f"reply is not JSON: {exc}") from None
    if not isinstance(plan, dict) or set(plan) != {"expression", "intensity", "gaze"}:
        raise DrawingError(f"reply must have exactly expression, intensity, gaze: {plan!r}")
    if plan["expression"] not in EXPRESSIONS:
        raise DrawingError(f"expression {plan['expression']!r} not in menu")
    i = plan["intensity"]
    if isinstance(i, bool) or not isinstance(i, (int, float)) or not 0 <= i <= 1:
        raise DrawingError(f"intensity {i!r} outside 0..1")
    if plan["gaze"] not in GAZE:
        raise DrawingError(f"gaze {plan['gaze']!r} not in menu")
    return {"expression": plan["expression"], "intensity": float(i), "gaze": plan["gaze"]}


def plan_to_expression(plan):
    """Scale the named expression's offsets from neutral by intensity; add gaze."""
    base, target = expression(), expression(plan["expression"])
    values = {k: base[k] + (target[k] - base[k]) * plan["intensity"] for k in base}
    values["gaze_x"], values["gaze_y"] = GAZE[plan["gaze"]]
    return expression(**{k: max(PARAMS[k][0], min(PARAMS[k][1], v)) for k, v in values.items()})


def plan_expression(line, receipt_dir, *, model=MODEL, retries=2, timeout=180, chat=None):
    """Ask the model for a plan; return (plan, receipt). Raises DrawingError after bounded retries."""
    chat = chat or _chat
    prompt = PROMPT.format(line=line.replace('"', "'")[:300], names=sorted(EXPRESSIONS), gazes=sorted(GAZE))
    attempts = []
    for attempt in range(retries + 1):
        started = time.perf_counter()
        reply, raw = None, ""
        try:
            reply = chat(prompt, model=model, timeout=timeout, num_predict=60)
            raw = reply.get("message", {}).get("content", "")
            plan = validate_plan(raw)
            error = None
        except DrawingError as exc:
            plan, error = None, str(exc)
        except OSError as exc:  # connection refused/timeout: side-effect free, but report it
            plan, error, raw = None, f"ollama unavailable: {exc}", ""
        attempts.append({"attempt": attempt + 1, "raw": raw, "error": error,
                         "seconds": round(time.perf_counter() - started, 2),
                         "eval_count": (reply or {}).get("eval_count") if error is None else None})
        if plan:
            break
    receipt = {"model": model, "line": line, "prompt": prompt, "attempts": attempts, "plan": plan,
               "authorship": "model-chosen menu values; geometry is procedural"}
    Path(receipt_dir).mkdir(parents=True, exist_ok=True)
    write_json(Path(receipt_dir) / "plan-receipt.json", receipt)
    if plan is None:
        raise DrawingError(f"model gave no valid plan after {len(attempts)} attempts; see receipt")
    return plan, receipt
