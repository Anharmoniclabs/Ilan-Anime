"""Bind opted-in ledger tasks to real creator and reviewer host agents.

This registry records identities reported by an agent-capable host. It does not
spawn agents, authenticate the host, restrict tools, or provide an OS sandbox.
One coordinator must be the sole writer for a run.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from production.runtime import Ledger, LedgerError
except ModuleNotFoundError:  # Direct `python production/host_handoff.py` execution.
    from runtime import Ledger, LedgerError


class HandoffRegistry:
    """Registry for distinct real host identities assigned to one target task."""

    def __init__(self, repo, run):
        self.repo = Path(repo).resolve()
        self.ledger = Ledger(self.repo, run)
        self.path = self.ledger.run_dir / "handoffs.json"
        self.data = self.ledger._load_handoffs()
        self.validate()

    def _save(self):
        self.validate()
        self.ledger._save_handoffs(self.data)

    @staticmethod
    def _text(value, label):
        if not isinstance(value, str) or not value.strip():
            raise LedgerError(f"{label} is required")
        return value

    def _used_host_ids(self):
        return {
            binding["host_agent_id"]
            for entry in self.data["bindings"].values()
            for binding in (entry.get("creator"), entry.get("reviewer"))
            if isinstance(binding, dict)
        }

    def validate(self):
        # Runtime owns the complete schema and ledger/binding state machine.
        original = self.ledger._load_handoffs
        self.ledger._load_handoffs = lambda: self.data
        try:
            self.ledger._validate_host_bindings()
        finally:
            self.ledger._load_handoffs = original
        return True

    def bind_creator(self, task_id, host, host_agent_id):
        task = self.ledger._task(task_id)
        if not task.get("require_host_bindings"):
            raise LedgerError("Task did not opt in to required host bindings")
        if task["state"] != "running" or not task.get("agent_id"):
            raise LedgerError("Bind a creator only after ledger dispatch")
        if task_id in self.data["bindings"]:
            raise LedgerError("Task already has a creator binding; never silently replace it")
        self._text(host, "Host")
        self._text(host_agent_id, "Actual host agent ID")
        if host_agent_id == task["agent_id"]:
            raise LedgerError("Actual host agent ID must not be a fabricated ledger alias")
        if host_agent_id in self._used_host_ids():
            raise LedgerError("One host agent cannot hold multiple production bindings")
        self.data["bindings"][task_id] = {"creator": {
            "ledger_alias": task["agent_id"], "host": host,
            "host_agent_id": host_agent_id, "role": task["role"],
            "state": "active", "note": "Creator bound after host spawn"}}
        self._save()
        return self.data["bindings"][task_id]["creator"]

    def bind_reviewer(self, task_id, reviewer_role, host, host_agent_id):
        task = self.ledger._task(task_id)
        entry = self.data["bindings"].get(task_id)
        creator = entry.get("creator") if isinstance(entry, dict) else None
        if (not task.get("require_host_bindings") or task["state"] != "submitted"
                or not isinstance(creator, dict) or creator.get("state") != "submitted"):
            raise LedgerError("Bind a reviewer only after a bound creator submits")
        if "reviewer" in entry:
            raise LedgerError("Task already has a reviewer binding; never silently replace it")
        role = self.ledger.roles[task["role"]]
        allowed = role.get("reviewer", role.get("reviewer_role", role.get("reviewers", [])))
        allowed = [allowed] if isinstance(allowed, str) else allowed
        if reviewer_role not in self.ledger.roles or reviewer_role not in allowed or reviewer_role == task["role"]:
            raise LedgerError("Reviewer role is not the task's separate designated reviewer")
        self._text(host, "Host")
        self._text(host_agent_id, "Actual reviewer host agent ID")
        if host_agent_id in {task.get("agent_id"), creator["host_agent_id"]}:
            raise LedgerError("Reviewer must be a distinct real host agent, not an alias or creator")
        if host_agent_id in self._used_host_ids():
            raise LedgerError("One host agent cannot hold multiple production bindings")
        entry["reviewer"] = {
            "host": host, "host_agent_id": host_agent_id, "role": reviewer_role,
            "state": "active", "note": "Reviewer bound after host spawn"}
        self._save()
        return entry["reviewer"]

    # Backward-compatible spelling for callers that only bind creators.
    bind = bind_creator

    def interrupt(self, task_id, kind, note):
        if kind not in {"creator", "reviewer"}:
            raise LedgerError("Binding kind must be creator or reviewer")
        self._text(note, "Concrete interruption note")
        try:
            binding = self.data["bindings"][task_id][kind]
        except KeyError as exc:
            raise LedgerError(f"No {kind} host binding for task") from exc
        if binding["state"] != "active":
            raise LedgerError("Only an active binding can be interrupted")
        binding.update(state="interrupted", note=note)
        self.ledger.pause(f"Host {kind} {binding['host_agent_id']} interrupted: {note}")
        # Ledger pause is saved first. A process failure before the registry save
        # leaves a fail-closed mismatch rather than permitting an automatic retry.
        self._save()
        return binding

    def update(self, task_id, state, note, kind="creator"):
        if state != "interrupted":
            raise LedgerError("Submission/completion states are owned by ledger transitions")
        return self.interrupt(task_id, kind, note)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".")
    parser.add_argument("--run", required=True)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("status")
    commands.add_parser("validate")
    creator = commands.add_parser("bind-creator")
    creator.add_argument("task_id"); creator.add_argument("--host", required=True); creator.add_argument("--host-agent-id", required=True)
    legacy_creator = commands.add_parser("bind", help="Backward-compatible alias for bind-creator")
    legacy_creator.add_argument("task_id"); legacy_creator.add_argument("--host", required=True); legacy_creator.add_argument("--host-agent-id", required=True)
    reviewer = commands.add_parser("bind-reviewer")
    reviewer.add_argument("task_id"); reviewer.add_argument("--reviewer-role", required=True)
    reviewer.add_argument("--host", required=True); reviewer.add_argument("--host-agent-id", required=True)
    interrupt = commands.add_parser("interrupt")
    interrupt.add_argument("task_id"); interrupt.add_argument("--kind", choices=("creator", "reviewer"), required=True)
    interrupt.add_argument("--note", required=True)
    legacy_update = commands.add_parser("update", help="Backward-compatible interruption command")
    legacy_update.add_argument("task_id"); legacy_update.add_argument("--state", choices=("interrupted",), required=True)
    legacy_update.add_argument("--kind", choices=("creator", "reviewer"), default="creator")
    legacy_update.add_argument("--note", required=True)
    args = parser.parse_args(argv)
    try:
        registry = HandoffRegistry(args.repo, args.run)
        if args.command == "status": output = registry.data
        elif args.command == "validate": output = registry.validate()
        elif args.command in {"bind-creator", "bind"}: output = registry.bind_creator(args.task_id, args.host, args.host_agent_id)
        elif args.command == "bind-reviewer": output = registry.bind_reviewer(args.task_id, args.reviewer_role, args.host, args.host_agent_id)
        else: output = registry.interrupt(args.task_id, args.kind, args.note)
        print(json.dumps(output, indent=2) if not isinstance(output, bool) else str(output).lower())
    except (LedgerError, OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(2, f"error: {exc}\n")


if __name__ == "__main__":
    main()
