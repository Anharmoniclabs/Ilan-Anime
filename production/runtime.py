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

    def _policy(self):
        path = self.repo / "production" / "policy.json"
        return json.loads(path.read_text()) if path.exists() else {"generation": {"enabled": False}}

    def _optional_contract(self, task):
        """Validate prompt budgets; the host, not this ledger, meters tool use.

        Paid budgets (max_cost_usd > 0) are allowed only when production/policy.json
        enables generation, the role has a generation right, and the amount fits
        the per-task cap. studio.policy enforces the actual spend per call."""
        if "acceptance_criteria" in task:
            criteria = task["acceptance_criteria"]
            if (not isinstance(criteria, list) or not criteria
                    or any(not isinstance(x, str) or not x.strip() for x in criteria)):
                raise LedgerError("acceptance_criteria must be a nonempty list of nonempty strings")
        if "requires_author_approval" in task and type(task["requires_author_approval"]) is not bool:
            raise LedgerError("requires_author_approval must be true or false")
        if "require_host_bindings" in task and type(task["require_host_bindings"]) is not bool:
            raise LedgerError("require_host_bindings must be true or false")
        if task.get("requires_author_approval"):
            if task.get("author_approver") != "luis-m-minier":
                raise LedgerError("author_approver must be luis-m-minier for an author-gated task")
        if "art_direction_mode" in task:
            modes = {"CHARACTER_ASSET", "ENVIRONMENT_PLATE", "STORY_FRAME", "EDITORIAL_MOODBOARD"}
            if task["art_direction_mode"] not in modes:
                raise LedgerError("Unknown art_direction_mode")
        if "budget" in task:
            budget = task["budget"]
            allowed = {"max_tool_calls", "max_seconds", "max_output_tokens", "max_cost_usd"}
            if not isinstance(budget, dict) or not budget or not budget.keys() <= allowed:
                raise LedgerError("Invalid budget keys; use max_tool_calls, max_seconds, max_output_tokens, max_cost_usd")
            for key, value in budget.items():
                if key == "max_cost_usd":
                    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
                        raise LedgerError("max_cost_usd must be a number >= 0")
                    if value > 0:
                        generation = self._policy().get("generation", {})
                        rights = self.roles.get(task.get("role"), {}).get("generate", [])
                        if not generation.get("enabled") or not rights:
                            raise LedgerError("max_cost_usd must be 0; paid generation is not enabled for this role")
                        if value > float(generation.get("max_per_task_usd", 0)):
                            raise LedgerError("max_cost_usd exceeds policy max_per_task_usd")
                elif type(value) is not int or value <= 0:
                    raise LedgerError(f"{key} must be a positive integer")

    def _validate_state(self, task):
        state = task.get("state")
        if state not in {"pending", "running", "submitted", "blocked", "approved", "rejected",
                         "author-approved", "author-rejected"}:
            raise LedgerError("Unknown task state")
        if state in {"submitted", "blocked", "approved", "rejected", "author-approved", "author-rejected"}:
            result = task.get("result")
            if (not isinstance(result, dict) or result.get("task_id") != task["id"]
                    or result.get("role") != task["role"]):
                raise LedgerError("Persisted task lacks a matching result")
            expected_status = "blocked" if state == "blocked" else "submitted"
            if result.get("status") != expected_status:
                raise LedgerError("Persisted result status mismatch")
            if state != "blocked" and (not result.get("evidence") or result.get("blockers")):
                raise LedgerError("Persisted submitted result requires evidence and no blockers")
        if state in {"approved", "rejected", "author-approved", "author-rejected"}:
            review = task.get("review")
            role = self.roles[task["role"]]
            allowed = role.get("reviewer", role.get("reviewer_role", role.get("reviewers", [])))
            allowed = [allowed] if isinstance(allowed, str) else allowed
            decision = "reject" if state == "rejected" else "approve"
            if (not isinstance(review, dict) or review.get("decision") != decision
                    or not review.get("evidence") or not review.get("agent_id")
                    or review.get("role") not in self.roles or review.get("role") not in allowed
                    or review.get("role") == task["role"]
                    or review.get("agent_id") == task.get("agent_id")):
                raise LedgerError("Persisted task lacks an independent matching review")
        if state in {"author-approved", "author-rejected"}:
            if not task.get("requires_author_approval"):
                raise LedgerError("Author review recorded for a task that did not require it")
            author_review = task.get("author_review")
            decision = "approve" if state == "author-approved" else "reject"
            if (not isinstance(author_review, dict) or author_review.get("decision") != decision
                    or author_review.get("author") != task.get("author_approver")
                    or not author_review.get("evidence")):
                raise LedgerError("Persisted task lacks a matching author review")

    def _load_handoffs(self):
        path = self.run_dir / "handoffs.json"
        if not path.exists():
            return {"version": 2, "run": self.run, "bindings": {}}
        data = json.loads(path.read_text())
        if (data.get("version") != 2 or data.get("run") != self.run
                or not isinstance(data.get("bindings"), dict)):
            raise LedgerError("Handoff registry identity, version, or shape mismatch")
        return data

    def _save_handoffs(self, data):
        """Atomically replace the registry; the coordinator is the sole writer."""
        self.run_dir.mkdir(parents=True, exist_ok=True)
        path = self.run_dir / "handoffs.json"
        fd, name = tempfile.mkstemp(prefix=".handoff-", suffix=".tmp", dir=self.run_dir)
        try:
            with os.fdopen(fd, "w") as handle:
                json.dump(data, handle, indent=2)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(name, path)
        finally:
            if os.path.exists(name):
                os.unlink(name)

    def _validate_host_bindings(self):
        """Fail closed when an opted-in task and its persisted host identities diverge."""
        data = self._load_handoffs()
        used_ids = set()
        for task_id, entry in data["bindings"].items():
            identifier(task_id)
            task = self._task(task_id)
            if not task.get("require_host_bindings"):
                raise LedgerError("Host binding exists for a task that did not opt in")
            if not isinstance(entry, dict) or not isinstance(entry.get("creator"), dict):
                raise LedgerError("Host-bound task requires a creator binding")
            creator = entry["creator"]
            for field in ("ledger_alias", "host", "host_agent_id", "role", "state", "note"):
                if not isinstance(creator.get(field), str):
                    raise LedgerError(f"Creator binding requires string field {field}")
            if (not creator["host"] or not creator["host_agent_id"]
                    or creator["ledger_alias"] != task.get("agent_id")
                    or creator["role"] != task["role"]
                    or creator["state"] not in {"active", "submitted", "completed", "interrupted"}):
                raise LedgerError("Creator binding does not match the dispatched task")
            if creator["host_agent_id"] in used_ids:
                raise LedgerError("One host agent cannot hold multiple production bindings")
            used_ids.add(creator["host_agent_id"])
            reviewer = entry.get("reviewer")
            if reviewer is not None:
                if not isinstance(reviewer, dict):
                    raise LedgerError("Invalid reviewer binding")
                for field in ("host", "host_agent_id", "role", "state", "note"):
                    if not isinstance(reviewer.get(field), str):
                        raise LedgerError(f"Reviewer binding requires string field {field}")
                role = self.roles[task["role"]]
                allowed = role.get("reviewer", role.get("reviewer_role", role.get("reviewers", [])))
                allowed = [allowed] if isinstance(allowed, str) else allowed
                if (not reviewer["host"] or not reviewer["host_agent_id"]
                        or reviewer["role"] not in self.roles or reviewer["role"] not in allowed
                        or reviewer["role"] == task["role"]
                        or reviewer["host_agent_id"] == creator["host_agent_id"]
                        or reviewer["state"] not in {"active", "completed", "interrupted"}):
                    raise LedgerError("Reviewer binding is not a separate designated host agent")
                if reviewer["host_agent_id"] in used_ids:
                    raise LedgerError("One host agent cannot hold multiple production bindings")
                used_ids.add(reviewer["host_agent_id"])

            state = task["state"]
            if state == "running":
                if creator["state"] not in {"active", "interrupted"} or reviewer is not None:
                    raise LedgerError("Running task and host binding states are inconsistent")
            elif state == "submitted":
                if creator["state"] != "submitted":
                    raise LedgerError("Submitted task requires a submitted creator binding")
                if reviewer and reviewer["state"] not in {"active", "interrupted"}:
                    raise LedgerError("Submitted task and reviewer binding states are inconsistent")
            elif state == "blocked":
                if creator["state"] != "interrupted" or reviewer is not None:
                    raise LedgerError("Blocked host-bound task must retain its interrupted creator binding")
            elif state in {"approved", "rejected", "author-approved", "author-rejected"}:
                if creator["state"] != "completed" or not reviewer or reviewer["state"] != "completed":
                    raise LedgerError("Reviewed task requires completed creator and reviewer bindings")
            elif state == "pending":
                raise LedgerError("Pending task cannot have a host binding")

        for task in self.data["tasks"].values():
            if task.get("require_host_bindings") and task["state"] not in {"pending", "running"}:
                if task["id"] not in data["bindings"]:
                    raise LedgerError("Host-bound task has no persisted binding")
        return data

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
        self._validate_host_bindings()
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
        for field in ("acceptance_criteria", "budget", "requires_author_approval", "author_approver", "art_direction_mode", "require_host_bindings", "supersedes"):
            if field in task:
                normalized[field] = task[field]
        if "supersedes" in normalized:
            old = self.data["tasks"].get(normalized["supersedes"])
            if (old is None or old["role"] != normalized["role"]
                    or old["state"] not in {"rejected", "author-rejected", "blocked"}):
                raise LedgerError("supersedes must name a rejected or blocked task of the same role")
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
        def done(task):
            expected = "author-approved" if task.get("requires_author_approval") else "approved"
            return task["state"] == expected

        def dependency_complete(dependency, depth=0):
            upstream = self._task(dependency)
            if done(upstream):
                return True
            # an approved revision task that supersedes the dependency satisfies it
            return depth < 10 and any(
                t.get("supersedes") == dependency and dependency_complete(t["id"], depth + 1)
                for t in self.data["tasks"].values())
        return [task["id"] for task in self.data["tasks"].values()
                if task["state"] == "pending" and all(
                    dependency_complete(dep) for dep in task["depends_on"])]

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
        result_extension = ""
        if task.get("require_host_bindings"):
            result_extension += " Include host_agent_id with the exact real creator ID bound by the host registry."
        if task["role"] == "quality-review" and task["id"].endswith("-qa"):
            result_extension += (
                " This release-QA result must also include pipeline_id, qa_report: {path, sha256}, "
                "and release_asset_sha256s containing the exact canonical final picture/audio digests reviewed."
            )
        envelope = dict(task)
        envelope["inputs"] = [self._current_input(path) for path in task["inputs"]]
        return (f"Read AGENTS.md, production/WORKER_CONTRACT.md and role skill {skill} fully.\n"
                f"Your bounded assignment is:\n{json.dumps(envelope, indent=2)}\n"
                "Work only on the listed shots and objective. Write only inside output_dir. "
                "Treat inputs as read-only. Do not overwrite approved assets, spawn more agents, "
                "publish, or expand scope without coordinator authorization. Paid generation only through "
                "`python -m studio generate` and only within the task budget and production/policy.json. "
                "When art_direction_mode is present, read production/art_direction.json and its "
                "canonical document and satisfy the mode-specific contract; do not claim canonical "
                "status because only digest-bound author approval can grant it. "
                "Return JSON {task_id, role, status: submitted|blocked, artifacts: [repository-relative "
                "file paths], evidence: [specific checks and observations], blockers: [strings]}. "
                f"{result_extension} "
                "Do not claim visual inspection unless you actually viewed the footage/frames. "
                "Pause on connection interruption; never retry automatically. You cannot approve "
                "your own task. These instructions and ledger checks are not an OS/tool sandbox.")

    def _current_input(self, path):
        """Point an upstream output dir at its approved revision, if it was superseded."""
        for task in self.data["tasks"].values():
            if task["output_dir"].rstrip("/") == path.rstrip("/"):
                current, seen = task, set()
                while current["id"] not in seen:
                    seen.add(current["id"])
                    newer = [t for t in self.data["tasks"].values() if t.get("supersedes") == current["id"]
                             and t["state"] in {"approved", "author-approved"}]
                    if not newer:
                        break
                    current = newer[-1]
                return current["output_dir"]
        return path

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
        if task["role"] == "quality-review" and task["id"].endswith("-qa") and result["status"] == "submitted":
            expected_pipeline = task["id"][:-3]
            report = result.get("qa_report")
            digests = result.get("release_asset_sha256s")
            if result.get("pipeline_id") != expected_pipeline:
                raise LedgerError("Release QA result pipeline_id does not match its task")
            if (not isinstance(report, dict) or set(report) != {"path", "sha256"}
                    or not isinstance(report.get("path"), str)
                    or not re.fullmatch(r"[0-9a-f]{64}", report.get("sha256", ""))
                    or report["path"] not in result["artifacts"]):
                raise LedgerError("Release QA result requires an artifact-bound qa_report SHA-256")
            if (not isinstance(digests, list) or not digests or len(digests) != len(set(digests))
                    or any(not isinstance(item, str) or not re.fullmatch(r"[0-9a-f]{64}", item)
                           for item in digests)):
                raise LedgerError("Release QA result requires unique canonical release_asset_sha256s")
        handoffs = None
        if task.get("require_host_bindings"):
            handoffs = self._load_handoffs()
            entry = handoffs["bindings"].get(task["id"])
            creator = entry.get("creator") if isinstance(entry, dict) else None
            if (not isinstance(creator, dict) or creator.get("state") != "active"
                    or creator.get("ledger_alias") != task.get("agent_id")
                    or creator.get("role") != task["role"]
                    or result.get("host_agent_id") != creator.get("host_agent_id")):
                raise LedgerError("Submission requires the matching real creator host binding")
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
        if handoffs is not None:
            creator = handoffs["bindings"][task["id"]]["creator"]
            creator.update(state="submitted" if result["status"] == "submitted" else "interrupted",
                           note="Result submitted" if result["status"] == "submitted" else "; ".join(result["blockers"]))
            self._save_handoffs(handoffs)
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
        if task["state"] != "submitted" or decision not in ("approve", "reject"):
            raise LedgerError("Only submitted tasks can be approved or rejected")
        if not isinstance(evidence, str) or not evidence.strip():
            raise LedgerError("Review evidence is required")
        handoffs = None
        if task.get("require_host_bindings"):
            handoffs = self._load_handoffs()
            entry = handoffs["bindings"].get(task_id)
            creator = entry.get("creator") if isinstance(entry, dict) else None
            reviewer = entry.get("reviewer") if isinstance(entry, dict) else None
            if (not isinstance(creator, dict) or creator.get("state") != "submitted"
                    or not isinstance(reviewer, dict) or reviewer.get("state") != "active"
                    or reviewer.get("role") != reviewer_role
                    or reviewer.get("host_agent_id") != reviewer_agent_id
                    or reviewer_agent_id == creator.get("host_agent_id")):
                raise LedgerError("Review requires its matching separate real reviewer host binding")
        else:
            identifier(reviewer_agent_id)
        task.update(state="approved" if decision == "approve" else "rejected",
                    review={"role": reviewer_role, "agent_id": reviewer_agent_id,
                            "decision": decision, "evidence": evidence})
        if handoffs is not None:
            entry = handoffs["bindings"][task_id]
            entry["creator"].update(state="completed", note="Independent review completed")
            entry["reviewer"].update(state="completed", note=evidence)
            self._save_handoffs(handoffs)
        self._event("review", task_id=task_id, decision=decision)
        return task

    def author_review(self, task_id, author, decision, evidence):
        """Record an explicit human creative decision after technical approval."""
        self._active()
        task = self._task(task_id)
        if not task.get("requires_author_approval"):
            raise LedgerError("Task does not require author approval")
        if task["state"] != "approved":
            raise LedgerError("Author review requires prior independent technical approval")
        if decision not in ("approve", "reject"):
            raise LedgerError("Author decision must be approve or reject")
        if author != task.get("author_approver"):
            raise LedgerError("Author identity does not match the task's designated approver")
        if not isinstance(evidence, str) or not evidence.strip():
            raise LedgerError("Author identity and decision evidence are required")
        task.update(state="author-approved" if decision == "approve" else "author-rejected",
                    author_review={"author": author, "decision": decision, "evidence": evidence})
        self._event("author-review", task_id=task_id, decision=decision, author=author)
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
    author_review = commands.add_parser("author-review", help="Record explicit human creative approval/rejection")
    author_review.add_argument("task_id")
    author_review.add_argument("--author", required=True)
    author_review.add_argument("--decision", choices=("approve", "reject"), required=True)
    author_review.add_argument("--evidence", required=True)
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
        elif args.command == "author-review":
            output = ledger.author_review(args.task_id, args.author, args.decision, args.evidence)
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
