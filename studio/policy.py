"""Spending policy and the append-only spend log.

Generation is allowed only when production/policy.json enables it, the price
estimates are filled in, the role has the right, the ledger task is running
with a positive ``budget.max_cost_usd``, and every cap still has room. Each
paid call is logged *before* it is sent (status ``sent``) and updated with
the outcome, so an interrupted run can never silently double-spend.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

from studio.paths import POLICY, ROOT, load_json

SPEND_LOG = ROOT / "production" / "spend_log.jsonl"


class PolicyError(RuntimeError):
    pass


def load(path=POLICY):
    return load_json(path) if Path(path).exists() else {"generation": {"enabled": False}}


def spend_entries(path=SPEND_LOG):
    if not Path(path).exists():
        return []
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def spent(task_id=None, path=SPEND_LOG):
    total = 0.0
    for entry in spend_entries(path):
        if entry.get("status") in ("sent", "ok", "failed-after-send") and (task_id is None or entry.get("task_id") == task_id):
            total += float(entry.get("estimated_usd", 0))
    return round(total, 6)


def append(entry, path=SPEND_LOG):
    entry = {"at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), **entry}
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def authorize(kind, estimate, task, role_rights, policy=None, path=SPEND_LOG):
    """Raise PolicyError unless this paid call is allowed; return remaining budgets."""
    policy = policy or load()
    gen = policy.get("generation", {})
    if not gen.get("enabled"):
        raise PolicyError("generation is disabled in production/policy.json")
    if kind not in role_rights:
        raise PolicyError(f"role {task.get('role')} has no {kind} generation right (roles.json)")
    if estimate is None or estimate <= 0:
        raise PolicyError(f"no price estimate for {kind} in production/policy.json; fill it in from the price page")
    if task.get("state") != "running":
        raise PolicyError(f"task {task.get('id')} is not running (state {task.get('state')})")
    task_cap = float((task.get("budget") or {}).get("max_cost_usd", 0))
    per_task = min(task_cap, float(gen.get("max_per_task_usd", 0)))
    total_cap = float(gen.get("max_total_usd", 0))
    used_task, used_total = spent(task["id"], path), spent(None, path)
    if used_task + estimate > per_task + 1e-9:
        raise PolicyError(f"task cap reached: {used_task:.2f} + {estimate:.2f} > {per_task:.2f} USD")
    if used_total + estimate > total_cap + 1e-9:
        raise PolicyError(f"total cap reached: {used_total:.2f} + {estimate:.2f} > {total_cap:.2f} USD")
    return {"task_remaining": round(per_task - used_task - estimate, 4),
            "total_remaining": round(total_cap - used_total - estimate, 4)}
