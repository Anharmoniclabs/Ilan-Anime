"""Host-neutral production task ledger; Python standard library only.

Run ``python production/runtime.py --help``. One coordinator must be the sole
writer for each run (including review and dispatch); workers return result JSON.
Writes are atomic, but concurrent coordinators are not supported. This program
does NOT spawn agents, restrict their tools, or provide an OS sandbox. The host
must spawn separate workers and enforce permissions, budgets and paid-tool gates.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import tempfile


class LedgerError(ValueError):
    """Invalid task, handoff, or approval."""


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", value):
        raise LedgerError("Identifiers require 1–80 letters, digits, underscores or hyphens")
    return value


class Ledger:
    """Single-writer, recoverable run state rooted in an existing repository."""

    def __init__(self, repo, run, roles_path="production/roles.json"):
        self.repo = Path(repo).resolve()
        self.run = identifier(run)
        self.run_dir = self.repo / "production" / "runs" / self.run
        self.path = self.run_dir / "ledger.json"
        self._contained(self.path, self.repo)
        raw = json.loads((self.repo / roles_path).read_text())
        roles = raw.get("roles", raw)
        self.roles = {r["id"]: r for r in roles} if isinstance(roles, list) else roles
        if not isinstance(self.roles, dict):
            raise LedgerError("roles.json must contain a roles mapping or list")
        self.data = json.loads(self.path.read_text()) if self.path.exists() else {
            "version": 1, "run": self.run, "paused": False, "pause_reason": None,
            "tasks": {}, "events": []}
        if self.data.get("run") != self.run:
            raise LedgerError("Ledger run identity mismatch")

    @staticmethod
    def _contained(path, root):
        try:
            Path(path).resolve().relative_to(Path(root).resolve())
        except ValueError as exc:
            raise LedgerError("Path escapes its assigned directory") from exc

    def _save(self):
        self._contained(self.path, self.repo)
        self.run_dir.mkdir(parents=True, exist_ok=True)
        fd, name = tempfile.mkstemp(prefix=".ledger-", suffix=".tmp", dir=self.run_dir)
        try:
            with os.fdopen(fd, "w") as handle:
                json.dump(self.data, handle, indent=2)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(name, self.path)
        finally:
            if os.path.exists(name):
                os.unlink(name)

    def _event(self, action, **details):
        self.data["events"].append({"action": action, **details})
        self._save()

    def initialize(self):
        if not self.path.exists():
            self._event("initialize")
        return self.data

    def _active(self):
        if self.data["paused"]:
            raise LedgerError("Run paused; explicit user approval is required to resume")

    def _task(self, task_id):
        try:
            return self.data["tasks"][task_id]
        except KeyError as exc:
            raise LedgerError(f"Unknown task: {task_id}") from exc

    def _output(self, task):
        expected = f"production/runs/{self.run}/tasks/{identifier(task['id'])}"
        if task["output_dir"].rstrip("/") != expected:
            raise LedgerError(f"output_dir must be exactly {expected}")
        path = self.repo / expected
        # Forbid a directory symlink from silently redirecting an assignment.
        if path.resolve() != path:
            raise LedgerError("Task output directory must not contain symlinks")
        return path

    @staticmethod
    def _optional_contract(task):
        """Validate prompt budgets; the host, not this ledger, meters tool use."""
        if "acceptance_criteria" in task:
            criteria = task["acceptance_criteria"]
            if (not isinstance(criteria, list) or not criteria
                    or any(not isinstance(x, str) or not x.strip() for x in criteria)):
                raise LedgerError("acceptance_criteria must be a nonempty list of nonempty strings")
        if "budget" in task:
            budget = task["budget"]
            allowed = {"max_tool_calls", "max_seconds", "max_output_tokens", "max_cost_usd"}
            if not isinstance(budget, dict) or not budget or not budget.keys() <= allowed:
                raise LedgerError("Invalid budget keys; use max_tool_calls, max_seconds, max_output_tokens, max_cost_usd")
            for key, value in budget.items():
                if key == "max_cost_usd":
                    if isinstance(value, bool) or not isinstance(value, (int, float)) or value != 0:
                        raise LedgerError("max_cost_usd must be 0; paid calls are not authorized")
                elif type(value) is not int or value <= 0:
                    raise LedgerError(f"{key} must be a positive integer")

    def _validate_state(self, task):
        state = task.get("state")
        if state not in {"pending", "running", "submitted", "blocked", "approved", "rejected"}:
            raise LedgerError("Unknown task state")
        if state in {"submitted", "blocked", "approved", "rejected"}:
            result = task.get("result")
            if (not isinstance(result, dict) or result.get("task_id") != task["id"]
                    or result.get("role") != task["role"]):
                raise LedgerError("Persisted task lacks a matching result")
            expected_status = "blocked" if state == "blocked" else "submitted"
            if result.get("status") != expected_status:
                raise LedgerError("Persisted result status mismatch")
            if state != "blocked" and (not result.get("evidence") or result.get("blockers")):
                raise LedgerError("Persisted submitted result requires evidence and no blockers")
        if state in {"approved", "rejected"}:
            review = task.get("review")
            role = self.roles[task["role"]]
            allowed = role.get("reviewer", role.get("reviewer_role", role.get("reviewers", [])))
            allowed = [allowed] if isinstance(allowed, str) else allowed
            decision = "approve" if state == "approved" else "reject"
            if (not isinstance(review, dict) or review.get("decision") != decision
                    or not review.get("evidence") or not review.get("agent_id")
                    or review.get("role") not in self.roles or review.get("role") not in allowed
                    or review.get("role") == task["role"]
                    or review.get("agent_id") == task.get("agent_id")):
                raise LedgerError("Persisted task lacks an independent matching review")

    def validate(self):
        """Reject unknown roles/dependencies, malformed outputs and dependency cycles."""
        tasks = self.data["tasks"]
        visited, visiting = set(), set()

        def visit(task_id):
            if task_id in visiting:
                raise LedgerError("Dependency cycle")
            if task_id in visited:
                return
            if task_id not in tasks:
                raise LedgerError(f"Missing dependency: {task_id}")
            task = tasks[task_id]
            if task["id"] != task_id or task["role"] not in self.roles:
                raise LedgerError("Task identity or role is invalid")
            self._output(task)
            self._optional_contract(task)
            self._validate_state(task)
            visiting.add(task_id)
            for dependency in task["depends_on"]:
                visit(dependency)
            visiting.remove(task_id)
            visited.add(task_id)

        for task_id in tasks:
            visit(task_id)
        return True

    def add(self, task):
        self._active()
        required = {"id", "role", "shots", "objective", "inputs", "output_dir", "depends_on"}
        if not required <= task.keys():
            raise LedgerError(f"Missing fields: {sorted(required - task.keys())}")
        task_id = identifier(task["id"])
        if task_id in self.data["tasks"]:
            raise LedgerError("Task already exists; create a new revision task")
        if task["role"] not in self.roles:
            raise LedgerError("Unknown role")
        if not isinstance(task["objective"], str) or not task["objective"].strip():
            raise LedgerError("A bounded objective is required")
        for field in ("shots", "inputs", "depends_on"):
            if not isinstance(task[field], list) or any(not isinstance(x, str) or not x.strip() for x in task[field]):
                raise LedgerError(f"{field} must be a list of nonempty strings")
        normalized = {key: task[key] for key in required}
        for field in ("acceptance_criteria", "budget"):
            if field in task:
                normalized[field] = task[field]
        normalized["state"] = "pending"
        self.data["tasks"][task_id] = normalized
        try:
            self.validate()
        except Exception:
            del self.data["tasks"][task_id]
            raise
        self._event("add", task_id=task_id)
        return normalized

    def ready(self):
        self.validate()
        if self.data["paused"]:
            return []
        return [task["id"] for task in self.data["tasks"].values()
                if task["state"] == "pending" and all(
                    self._task(dep)["state"] == "approved" for dep in task["depends_on"])]

    def dispatch(self, task_id, agent_id):
        """Reserve a worker slot and emit a prompt; caller separately spawns the agent."""
        self._active()
        identifier(agent_id)
        if task_id not in self.ready():
            raise LedgerError("Task is not ready (dependencies must be approved)")
        if sum(t["state"] == "running" for t in self.data["tasks"].values()) >= 6:
            raise LedgerError("Six-worker concurrency limit reached")
        task = self._task(task_id)
        role = self.roles[task["role"]]
        skill = role.get("skill", role.get("skill_path"))
        if not skill:
            raise LedgerError("Role has no skill path")
        for source in task["inputs"]:
            relative = Path(source)
            if relative.is_absolute() or ".." in relative.parts:
                raise LedgerError("Input must be a safe repository-relative path")
            path = self.repo / relative
            self._contained(path, self.repo)
            if not path.exists():
                raise LedgerError(f"Missing required input: {source}")
        self._output(task).mkdir(parents=True, exist_ok=True)
        task.update(state="running", agent_id=agent_id)
        self._event("dispatch", task_id=task_id, agent_id=agent_id)
        return (f"Read AGENTS.md and role skill {skill} fully.\n"
                f"Your bounded assignment is:\n{json.dumps(task, indent=2)}\n"
                "Work only on the listed shots and objective. Write only inside output_dir. "
                "Treat inputs as read-only. Do not overwrite approved assets, spawn more agents, "
                "make network/paid calls, publish, or expand scope without coordinator authorization. "
                "Return JSON {task_id, role, status: submitted|blocked, artifacts: [repository-relative "
                "file paths], evidence: [specific checks and observations], blockers: [strings]}. "
                "Do not claim visual inspection unless you actually viewed the footage/frames. "
                "Pause on connection interruption; never retry automatically. You cannot approve "
                "your own task. These instructions and ledger checks are not an OS/tool sandbox.")

    def submit(self, result):
        self._active()
        required = {"task_id", "role", "status", "artifacts", "evidence", "blockers"}
        if not required <= result.keys():
            raise LedgerError("Result is missing required fields")
        task = self._task(result["task_id"])
        if task["state"] != "running" or task["role"] != result["role"]:
            raise LedgerError("Result identity or task state mismatch")
        if result["status"] not in ("submitted", "blocked"):
            raise LedgerError("Result status must be submitted or blocked")
        for field in ("artifacts", "evidence", "blockers"):
            if not isinstance(result[field], list) or any(not isinstance(x, str) or not x.strip() for x in result[field]):
                raise LedgerError(f"{field} must be a list of nonempty strings")
        if result["status"] == "submitted" and (not result["evidence"] or result["blockers"]):
            raise LedgerError("Submitted results require evidence and no unresolved blockers")
        if result["status"] == "blocked" and not result["blockers"]:
            raise LedgerError("Blocked results require a blocker description")
        output = self._output(task)
        for artifact in result["artifacts"]:
            relative = Path(artifact)
            if relative.is_absolute() or ".." in relative.parts:
                raise LedgerError("Artifact must be a safe repository-relative path")
            path = self.repo / relative
            self._contained(path, output)
            if not path.is_file():
                raise LedgerError(f"Missing artifact: {artifact}")
        task.update(state=result["status"], result=result)
        if result["status"] == "blocked":
            self.data.update(paused=True, pause_reason="; ".join(result["blockers"]))
        self._event("submit", task_id=task["id"], status=result["status"])
        return task

    def review(self, task_id, reviewer_role, reviewer_agent_id, decision, evidence):
        self._active()
        task = self._task(task_id)
        role = self.roles[task["role"]]
        allowed = role.get("reviewer", role.get("reviewer_role", role.get("reviewers", [])))
        allowed = [allowed] if isinstance(allowed, str) else allowed
        if (reviewer_role not in self.roles or reviewer_role not in allowed
                or reviewer_role == task["role"] or reviewer_agent_id == task.get("agent_id")):
            raise LedgerError("Independent designated reviewer required; self approval forbidden")
        identifier(reviewer_agent_id)
        if task["state"] != "submitted" or decision not in ("approve", "reject"):
            raise LedgerError("Only submitted tasks can be approved or rejected")
        if not isinstance(evidence, str) or not evidence.strip():
            raise LedgerError("Review evidence is required")
        task.update(state="approved" if decision == "approve" else "rejected",
                    review={"role": reviewer_role, "agent_id": reviewer_agent_id,
                            "decision": decision, "evidence": evidence})
        self._event("review", task_id=task_id, decision=decision)
        return task

    def pause(self, reason):
        if not isinstance(reason, str) or not reason.strip():
            raise LedgerError("Pause reason is required")
        self.data.update(paused=True, pause_reason=reason)
        self._event("pause", reason=reason)

    def resume(self, approval):
        """Coordinator records actual user permission, never fabricates this string."""
        if approval != f"APPROVE RESUME {self.run}":
            raise LedgerError(f"User approval required: APPROVE RESUME {self.run}")
        if not self.data["paused"]:
            raise LedgerError("Run is not paused")
        self.data.update(paused=False, pause_reason=None)
        # No state is retried/reset. Blocked tasks need new revision tasks.
        self._event("resume", approval=approval)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".")
    parser.add_argument("--run", required=True)
    parser.add_argument("--roles", default="production/roles.json")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("init", "status", "ready", "validate"):
        commands.add_parser(name)
    for name in ("add", "submit"):
        commands.add_parser(name).add_argument("json_file", help="Task or worker-result JSON")
    dispatch = commands.add_parser("dispatch", help="Reserve worker slot and print prompt; does not spawn")
    dispatch.add_argument("task_id")
    dispatch.add_argument("--agent-id", required=True)
    review = commands.add_parser("review")
    review.add_argument("task_id")
    review.add_argument("--reviewer-role", required=True)
    review.add_argument("--reviewer-agent-id", required=True)
    review.add_argument("--decision", choices=("approve", "reject"), required=True)
    review.add_argument("--evidence", required=True)
    commands.add_parser("pause").add_argument("reason")
    commands.add_parser("resume").add_argument("--approval", required=True)
    args = parser.parse_args(argv)
    try:
        ledger = Ledger(args.repo, args.run, args.roles)
        if args.command == "init":
            output = ledger.initialize()
        elif args.command == "status":
            output = ledger.data
        elif args.command in ("add", "submit"):
            output = getattr(ledger, args.command)(json.loads(Path(args.json_file).read_text()))
        elif args.command == "dispatch":
            output = ledger.dispatch(args.task_id, args.agent_id)
        elif args.command == "review":
            output = ledger.review(args.task_id, args.reviewer_role, args.reviewer_agent_id, args.decision, args.evidence)
        elif args.command == "pause":
            output = ledger.pause(args.reason)
        elif args.command == "resume":
            output = ledger.resume(args.approval)
        else:
            output = getattr(ledger, args.command)()
        print(output if isinstance(output, str) else json.dumps(output, indent=2))
    except (LedgerError, OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(2, f"error: {exc}\n")


if __name__ == "__main__":
    main()
