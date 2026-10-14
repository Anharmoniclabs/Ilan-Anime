"""Codex agent runner: ready ledger tasks -> real Codex workers -> separate
Codex reviewers -> ledger decisions -> revisions or the author gate.

One process is the sole ledger writer. Each worker and reviewer is a separate
``codex exec`` session (its ``thread_id`` is the real host agent id). Before
every launch the runner writes a checkpoint; if a run is found mid-flight on
startup it pauses the ledger instead of relaunching, because the first launch
may already have done (and paid for) work. Nothing is retried automatically.

    python -m studio run --run s01-11-12 [--max-tasks 5] [--parallel 2] [--dry-run]
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from studio import policy as pol
from studio.paths import ROOT, load_json, write_json

sys.path.insert(0, str(ROOT))
from production.host_handoff import HandoffRegistry  # noqa: E402
from production.runtime import Ledger, LedgerError  # noqa: E402

RESULT_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["task_id", "role", "status", "artifacts", "evidence", "blockers"],
    "properties": {
        "task_id": {"type": "string"}, "role": {"type": "string"},
        "status": {"type": "string", "enum": ["submitted", "blocked"]},
        "artifacts": {"type": "array", "items": {"type": "string"}},
        "evidence": {"type": "array", "items": {"type": "string"}},
        "blockers": {"type": "array", "items": {"type": "string"}},
    },
}
REVIEW_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["decision", "evidence", "repair_notes"],
    "properties": {
        "decision": {"type": "string", "enum": ["approve", "reject"]},
        "evidence": {"type": "string"},
        "repair_notes": {"type": "array", "items": {"type": "string"}},
    },
}


def result_schema(task):
    """The worker schema must permit the fields its ledger contract requires."""
    schema = deepcopy(RESULT_SCHEMA)
    if task.get("completion_contract"):
        schema["required"].append("completion")
        schema["properties"]["completion"] = {
            "type": "object", "additionalProperties": False,
            "required": ["artifacts", "evidence"],
            "properties": {
                "artifacts": {"type": "array", "items": {
                    "type": "object", "additionalProperties": False,
                    "required": ["path", "kind"],
                    "properties": {"path": {"type": "string"}, "kind": {"type": "string"}}}},
                "evidence": {"type": "array", "items": {
                    "type": "object", "additionalProperties": False,
                    "required": ["kind", "detail"],
                    "properties": {"kind": {"type": "string"}, "detail": {"type": "string"}}}},
            },
        }
    if task["role"] == "quality-review" and task["id"].endswith("-qa"):
        schema["required"] += ["pipeline_id", "qa_report", "release_asset_sha256s"]
        schema["properties"].update({
            "pipeline_id": {"type": ["string", "null"]},
            "qa_report": {"anyOf": [
                {"type": "null"},
                {"type": "object", "additionalProperties": False,
                 "required": ["path", "sha256"],
                 "properties": {"path": {"type": "string"}, "sha256": {"type": "string"}}},
            ]},
            "release_asset_sha256s": {"type": "array", "items": {"type": "string"}},
        })
    return schema


class RunnerError(RuntimeError):
    pass


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class CodexRunner:
    def __init__(self, run, *, dry_run=False, parallel=1, log=print, codex=None, policy=None, root=ROOT):
        self.root = Path(root)
        self.run = run
        self.ledger = Ledger(self.root, run)
        self.policy = policy or pol.load(self.root / "production" / "policy.json")
        self.cfg = self.policy.get("codex", {})
        self.codex = codex or self.cfg.get("binary", "codex")
        self.dry_run = dry_run
        self.parallel = max(1, min(int(parallel), 6))
        self.log = log
        self.run_dir = self.ledger.run_dir
        self.state_path = self.run_dir / "runner_state.json"
        self.state = load_json(self.state_path) if self.state_path.exists() else {"inflight": {}, "history": []}
        self.roles = self.ledger.roles

    # ------------------------------------------------------------ plumbing
    def _save(self):
        write_json(self.state_path, self.state)

    def _event(self, **event):
        event = {"at": _now(), **event}
        self.state["history"].append(event)
        self._save()
        self.log(json.dumps(event))

    def preflight(self):
        self._verify_picture_packet()
        if ((self.root / "production/image-demand" / self.run / "packet.json").exists()
                and not getattr(self, "image_demand_runner", False)):
            raise RunnerError("Image demand runs require `studio demand work SHOT`; "
                              "the generic runner cannot validate their reference packets.")
        if not self.dry_run and not shutil.which(self.codex):
            raise RunnerError(f"`{self.codex}` not found. Install the Codex CLI and sign in, "
                              "or set policy.codex.binary.")
        if self.ledger.data.get("paused"):
            raise RunnerError(f"run {self.run} is paused: {self.ledger.data.get('pause_reason')}. "
                              f"Inspect outputs, then: python production/runtime.py --run {self.run} "
                              f"resume --approval 'APPROVE RESUME {self.run}' (user decision only)")
        if self.state["inflight"]:
            reason = ("runner found in-flight work from an interrupted session: "
                      + ", ".join(f"{k} ({v['phase']})" for k, v in self.state["inflight"].items())
                      + ". It may have produced files or spent money; inspect before resuming.")
            self.ledger.pause(reason)
            raise RunnerError(reason)

    def _codex(self, prompt, schema, out_dir, label, network=False, images=()):
        """Run one codex exec session; return (thread_id, final_json, events_path)."""
        out_dir.mkdir(parents=True, exist_ok=True)
        schema_path = out_dir / f"{label}.schema.json"
        last_path = out_dir / f"{label}.last_message.json"
        events_path = out_dir / f"{label}.events.jsonl"
        schema_path.write_text(json.dumps(schema))
        cmd = [self.codex, "exec", "--json", "--sandbox", self.cfg.get("sandbox", "workspace-write"),
               "--output-schema", str(schema_path), "-o", str(last_path)]
        if network:
            cmd += ["-c", "sandbox_workspace_write.network_access=true"]
        cmd += list(self.cfg.get("extra_args", []))
        for image in images:
            cmd += ["--image", str(image)]
        # --image accepts multiple paths; terminate option parsing so it cannot
        # swallow the prompt as another filename.
        cmd.extend(["--", prompt])
        if self.dry_run:
            return f"dry-run-{label}", None, cmd
        env = os.environ.copy()
        venv_bin = self.root / ".venv" / "bin"
        if (venv_bin / "python").exists():
            env["PATH"] = str(venv_bin) + os.pathsep + env.get("PATH", "")
        with open(events_path, "w", encoding="utf-8") as events:
            proc = subprocess.run(cmd, cwd=self.root, stdout=events, stderr=subprocess.PIPE, text=True,
                                  timeout=int(self.cfg.get("timeout_seconds", 3600)), env=env)
        thread_id = None
        for line in events_path.read_text().splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event.get("type") == "thread.started":
                thread_id = event.get("thread_id")
                break
        if proc.returncode != 0:
            raise RunnerError(f"codex exec failed ({proc.returncode}) for {label}: {proc.stderr[-800:]}")
        final = None
        if last_path.exists():
            try:
                final = json.loads(last_path.read_text())
            except json.JSONDecodeError:
                final = None
        return thread_id, final, events_path

    # --------------------------------------------------------------- prompts
    def _skill_name(self, role):
        return Path(self.roles[role]["skill"]).parent.name

    def worker_prompt(self, task, dispatch_text):
        out = task["output_dir"]
        return (f"${self._skill_name(task['role'])}\n\n"
                f"You are the `{task['role']}` worker for ledger run `{self.run}`, task `{task['id']}`.\n\n"
                f"{dispatch_text}\n\n"
                f"When done, write the result object to `{out}/result.json` and return exactly that JSON "
                "as your final message. Artifacts must be real files inside output_dir.")

    def reviewer_prompt(self, task, reviewer_role, result, review_dir):
        task = dict(task)
        task['inputs'] = [self.ledger._current_input(p) for p in task['inputs']]
        return (f"${self._skill_name(reviewer_role)}\n\n"
                f"You are the independent `{reviewer_role}` reviewer for task `{task['id']}` "
                f"(made by `{task['role']}`) in run `{self.run}`. You did not make this work and must not edit it.\n\n"
                f"Task envelope:\n{json.dumps(task, indent=2)}\n\nWorker result:\n{json.dumps(result, indent=2)}\n\n"
                "Open and inspect the actual artifacts (view images; for renders run "
                "`python -m studio qa <shot.json> --out <dir>` and look at the flagged frames). Check every "
                "acceptance criterion and, for visual work, the task's art_direction_mode in "
                "production/art_direction.json. Write notes only inside "
                f"`{review_dir}`. Approve only what meets the criteria; a technical pass is never Luis's "
                "creative approval.\n\nReturn JSON {decision: approve|reject, evidence: specific observations "
                "with paths/frames, repair_notes: [targeted fixes]}.")

    # ------------------------------------------------------------- one task
    def _network_for(self, task):
        rights = self.roles[task["role"]].get("generate", [])
        budget = float((task.get("budget") or {}).get("max_cost_usd", 0))
        return bool(rights and budget > 0 and self.policy.get("generation", {}).get("enabled")
                    and self.cfg.get("network_for_generation_tasks", True))

    def launch(self, task_id):
        """Dispatch in the ledger (sole writer) and checkpoint before any session starts."""
        self._verify_picture_packet()
        alias = f"codex-{task_id}"[:80]
        dispatch_text = self.ledger.dispatch(task_id, alias)
        task = self.ledger._task(task_id)
        self.state["inflight"][task_id] = {"phase": "worker", "alias": alias, "started": _now()}
        self._save()
        return {"task_id": task_id, "prompt": self.worker_prompt(task, dispatch_text),
                "dir": self.root / task["output_dir"] / ".codex", "network": self._network_for(task),
                "schema": result_schema(task),
                "images": [self.root / self.ledger._current_input(p) for p in task['inputs']
                           if Path(p).suffix.lower() in {'.png', '.jpg', '.jpeg', '.webp'}]}

    def _verify_picture_packet(self):
        packet = self.run_dir / 'picture-packet.json'
        if packet.exists():
            from studio.picture import verify_packet, PictureError
            try:
                verify_packet(self.root, load_json(packet))
            except (PictureError, OSError, KeyError) as exc:
                raise RunnerError(f'Picture source verification failed: {exc}') from exc

    def execute(self, job):
        """Run the worker session (no ledger writes here; safe in a thread)."""
        thread, final, _ = self._codex(job["prompt"], job["schema"], job["dir"], "worker", network=job["network"], images=job.get('images', ()))
        return job["task_id"], thread, final

    def work(self, task_id):
        return self.execute(self.launch(task_id))

    def submit(self, task_id, thread, final):
        task = self.ledger._task(task_id)
        result = final
        result_path = self.root / task["output_dir"] / "result.json"
        if result is None and result_path.exists():
            result = json.loads(result_path.read_text())
        if self.dry_run:
            self._event(action="dry-run-worker", task=task_id)
            return None
        if not isinstance(result, dict):
            raise RunnerError(f"{task_id}: worker returned no result JSON")
        if task.get("require_host_bindings"):
            if not thread:
                raise RunnerError(f"{task_id}: no Codex thread id to bind")
            HandoffRegistry(self.root, self.run).bind_creator(task_id, "codex", thread)
            self.ledger = Ledger(self.root, self.run)
            result["host_agent_id"] = thread
        self.ledger.submit(result)
        self.state["inflight"][task_id]["phase"] = "submitted"
        self._save()
        self._event(action="submitted", task=task_id, status=result["status"], host_agent_id=thread)
        return result

    def review(self, task_id, result):
        task = self.ledger._task(task_id)
        reviewer_role = self.roles[task["role"]]["reviewer"]
        review_dir = self.run_dir / "reviews" / task_id
        self.state["inflight"][task_id]["phase"] = "review"
        self._save()
        prompt = self.reviewer_prompt(task, reviewer_role, result, review_dir.relative_to(self.root))
        thread, final, _ = self._codex(prompt, REVIEW_SCHEMA, review_dir, "reviewer")
        if self.dry_run:
            return None
        if not isinstance(final, dict) or final.get("decision") not in ("approve", "reject"):
            raise RunnerError(f"{task_id}: reviewer returned no decision")
        if not thread:
            raise RunnerError(f"{task_id}: reviewer has no Codex thread id")
        write_json(review_dir / "review.json", {**final, "reviewer_role": reviewer_role, "host_agent_id": thread})
        if task.get("require_host_bindings"):
            HandoffRegistry(self.root, self.run).bind_reviewer(task_id, reviewer_role, "codex", thread)
            self.ledger = Ledger(self.root, self.run)
        evidence = final["evidence"] + ("" if not final["repair_notes"] else
                                        " | repair: " + "; ".join(final["repair_notes"]))
        self.ledger.review(task_id, reviewer_role, thread, final["decision"], evidence)
        self._event(action="reviewed", task=task_id, decision=final["decision"], reviewer=thread)
        if final["decision"] == "reject":
            self.revise(task_id, final, review_dir)
        elif task.get("requires_author_approval"):
            self._event(action="awaiting-author", task=task_id,
                        note=f"Luis: python -m studio approve --run {self.run} {task_id} --decision approve|reject "
                             "--evidence 'what you watched and why'")
        return final

    def revise(self, task_id, review, review_dir):
        cfg = self.policy.get("revisions", {})
        if not cfg.get("auto_create_on_reject", True):
            return None
        head, _, tail = task_id.rpartition("-r")
        base = head if head and tail.isdigit() else task_id
        n = 1 + sum(1 for t in self.ledger.data["tasks"]
                    if t.startswith(base + "-r") and t[len(base) + 2:].isdigit())
        if n > int(cfg.get("max_revisions_per_task", 2)):
            self.ledger.pause(f"{base}: rejected {n} times; needs a user decision")
            self._event(action="paused", task=task_id, reason="revision limit")
            return None
        old = self.ledger._task(task_id)
        new_id = f"{base}-r{n}"
        fields = {k: old[k] for k in ("role", "shots", "inputs", "depends_on", "acceptance_criteria", "budget",
                                      "requires_author_approval", "author_approver", "art_direction_mode",
                                      "require_host_bindings", "full_scene_action", "completion_contract") if k in old}
        review_rel = str((review_dir / "review.json").relative_to(self.root))
        prior = [p for p in [old["output_dir"]] if (self.root / p).exists()]
        task = {**fields, "id": new_id, "supersedes": task_id,
                "inputs": list(dict.fromkeys(old["inputs"] + prior + [review_rel])),
                "output_dir": f"production/runs/{self.run}/tasks/{new_id}",
                "objective": (old["objective"].split("\nRevision")[0] + f"\nRevision {n}: fix only what the "
                              f"reviewer found ({review_rel}): " + "; ".join(review.get("repair_notes", [])))}
        self.ledger.add(task)
        self._event(action="revision-created", task=new_id, supersedes=task_id)
        return new_id

    # ---------------------------------------------------------------- loop
    def step(self):
        ready = self.ledger.ready()
        if not ready:
            return []
        jobs = [self.launch(task_id) for task_id in ready[:self.parallel]]  # sequential ledger writes
        results = []
        with ThreadPoolExecutor(len(jobs)) as pool:
            futures = [pool.submit(self.execute, job) for job in jobs]
            for job, future in zip(jobs, futures):
                try:
                    results.append(future.result())
                except Exception as exc:  # a failed session pauses the run; never relaunched
                    self.ledger = Ledger(self.root, self.run)
                    if not self.ledger.data.get("paused"):
                        self.ledger.pause(f"{job['task_id']}: {exc}")
                    self._event(action="paused", task=job["task_id"], reason=str(exc))
                    raise
        done = []
        for task_id, thread, final in results:
            try:
                result = self.submit(task_id, thread, final)
                if result is not None and result["status"] == "submitted":
                    self.review(task_id, result)
                elif result is not None:
                    self._event(action="blocked", task=task_id, blockers=result["blockers"])
            except (RunnerError, LedgerError, subprocess.TimeoutExpired) as exc:
                self.ledger = Ledger(self.root, self.run)
                if not self.ledger.data.get("paused"):
                    self.ledger.pause(f"{task_id}: {exc}")
                self._event(action="paused", task=task_id, reason=str(exc))
                raise
            finally:
                self.state["inflight"].pop(task_id, None)
                self._save()
            done.append(task_id)
        return done

    def loop(self, max_tasks=None):
        self.preflight()
        completed = 0
        while max_tasks is None or completed < max_tasks:
            if self.dry_run:
                ready = self.ledger.ready()
                for task_id in ready[: (max_tasks or len(ready))]:
                    task = self.ledger._task(task_id)
                    self.log(json.dumps({"would_run": task_id, "role": task["role"],
                                         "reviewer": self.roles[task["role"]]["reviewer"],
                                         "network": self._network_for(task)}))
                return {"dry_run": True, "ready": ready}
            done = self.step()
            if not done:
                break
            completed += len(done)
        status = {t["id"]: t["state"] for t in self.ledger.data["tasks"].values()}
        waiting = [t for t, s in status.items() if s == "approved"
                   and self.ledger._task(t).get("requires_author_approval")]
        return {"run": self.run, "completed_this_session": completed, "states": status,
                "awaiting_luis": waiting, "paused": self.ledger.data.get("paused")}
