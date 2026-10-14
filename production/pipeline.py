"""Build and validate drawing-led, ledger-compatible shot-production DAGs.

This module plans work; it does not spawn agents, generate images, approve art,
or bypass ``production.runtime``.  Technical review and author approval are
separate gates.  Python standard library only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

try:
    from production.asset_registry import AssetRegistry, AssetRegistryError
except ModuleNotFoundError:  # ``python production/pipeline.py`` from repo root
    from asset_registry import AssetRegistry, AssetRegistryError


class PipelineError(ValueError):
    """The pipeline contract is incomplete, unsafe, or contradictory."""


ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}")
ACTION_FIELDS = ("character", "prop", "environment", "effects", "camera")
ART_DIRECTION_MODES = {"CHARACTER_ASSET", "ENVIRONMENT_PLATE", "STORY_FRAME", "EDITORIAL_MOODBOARD"}
SOURCE_SUFFIXES = {".md", ".json", ".csv", ".txt", ".fountain"}
FORBIDDEN_INPUT_PARTS = {"rejected", "renders", "replacement_cels"}
COMPARISON_PURPOSES = {"visual-style-comparison-only"}
HASH_RE = re.compile(r"[0-9a-f]{64}\Z")


def _identifier(value: object, label: str) -> str:
    if not isinstance(value, str) or not ID_RE.fullmatch(value):
        raise PipelineError(f"{label} must be a 1-80 character identifier")
    return value


def _strings(value: object, label: str, *, allow_empty: bool = False) -> list[str]:
    if not isinstance(value, list) or (not value and not allow_empty):
        raise PipelineError(f"{label} must be {'a' if allow_empty else 'a nonempty'} list")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise PipelineError(f"{label} entries must be nonempty strings")
    return value


def load_json(path: str | Path) -> dict:
    data = json.loads(Path(path).read_text())
    if not isinstance(data, dict):
        raise PipelineError(f"Expected a JSON object: {path}")
    return data


def _roles(raw: dict) -> dict:
    roles = raw.get("roles", raw)
    if isinstance(roles, list):
        roles = {role["id"]: role for role in roles}
    if not isinstance(roles, dict) or not roles:
        raise PipelineError("roles.json must contain a nonempty role mapping")
    return roles


def _generation_budget(repo, roles_raw, role_id) -> float:
    """Per-task paid budget: 0 unless policy.json enables generation for this role."""
    if repo is None:
        return 0
    path = Path(repo) / "production" / "policy.json"
    if not path.exists():
        return 0
    generation = json.loads(path.read_text()).get("generation", {})
    rights = _roles(roles_raw).get(role_id, {}).get("generate", [])
    if not generation.get("enabled") or not rights:
        return 0
    return float(generation.get("max_per_task_usd", 0))


def _safe_relative(path: str, label: str) -> str:
    candidate = Path(path)
    if candidate.is_absolute() or ".." in candidate.parts or not candidate.parts:
        raise PipelineError(f"{label} must be a safe repository-relative path")
    return candidate.as_posix()


def _existing_repo_path(repo: str | Path, relative: str, label: str) -> Path:
    root = Path(repo).resolve()
    path = (root / relative).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise PipelineError(f"{label} escapes the repository") from exc
    if not path.exists():
        raise PipelineError(f"Missing {label}: {relative}")
    return path


def _forbidden_input_path(relative: str) -> bool:
    path = Path(relative)
    lowered = {part.lower() for part in path.parts}
    return bool(lowered & FORBIDDEN_INPUT_PARTS) or "unapproved" in path.name.lower()


def _source_input(value: str) -> str:
    relative = _safe_relative(value, "source input")
    if Path(relative).suffix.lower() not in SOURCE_SUFFIXES:
        raise PipelineError(f"Source input must be canonical text/data, not media or binary: {relative}")
    if _forbidden_input_path(relative):
        raise PipelineError(f"Forbidden rejected/render/replacement source input: {relative}")
    return relative


def _verify_text_data_file(path: Path, relative: str) -> None:
    try:
        raw = path.read_bytes()
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PipelineError(f"Source input is not UTF-8 text/data: {relative}") from exc
    if "\x00" in text:
        raise PipelineError(f"Source input contains binary NUL bytes: {relative}")
    if path.suffix.lower() == ".json":
        try:
            json.loads(text)
        except json.JSONDecodeError as exc:
            raise PipelineError(f"Source JSON is invalid: {relative}") from exc


def _registry_state(repo: str | Path) -> tuple[AssetRegistry, dict]:
    try:
        registry = AssetRegistry(repo)
        return registry, registry.verify(check_files=True)
    except (AssetRegistryError, OSError, ValueError, json.JSONDecodeError) as exc:
        raise PipelineError(f"Production asset registry verification failed: {exc}") from exc


def _verified_production_assets(spec: dict, repo: str | Path | None) -> list[dict]:
    refs = spec.get("production_assets", [])
    if not isinstance(refs, list):
        raise PipelineError("production_assets must be a list of registry references")
    if not refs:
        return []
    if repo is None:
        raise PipelineError("Production assets require repository-backed registry verification")
    _, state = _registry_state(repo)
    verified = []
    for ref in refs:
        required = {"asset_id", "version", "sha256", "final_use_id"}
        if not isinstance(ref, dict) or set(ref) != required:
            raise PipelineError(f"Production asset references require exactly {sorted(required)}")
        if (not isinstance(ref["asset_id"], str) or type(ref["version"]) is not int
                or ref["version"] < 1 or not isinstance(ref["sha256"], str)
                or not HASH_RE.fullmatch(ref["sha256"])
                or not isinstance(ref["final_use_id"], str) or not ref["final_use_id"].strip()):
            raise PipelineError("Malformed production asset registry reference")
        key = (ref["asset_id"], ref["version"])
        record = state["assets"].get(key)
        if record is None or record["sha256"] != ref["sha256"]:
            raise PipelineError(f"Registry identity/digest mismatch for production asset: {key}")
        if state["states"].get(key) != "canonical" or record.get("mode") != "production":
            raise PipelineError(f"Production asset is not canonical/final-use eligible: {key}")
        link = state["final_uses"].get(ref["final_use_id"])
        if (not link or (link.get("asset_id"), link.get("version")) != key):
            raise PipelineError(f"Production asset lacks the exact active final-use link: {key}")
        requested_shots = set(spec.get("shots", []))
        if not requested_shots <= set(record["shots"]):
            raise PipelineError(f"Pipeline shots exceed registered asset shot scope: {key}")
        if not requested_shots <= set(link["shots"]):
            raise PipelineError(f"Pipeline shots exceed active final-use link shot scope: {key}")
        path = record["path"]
        if _forbidden_input_path(path):
            raise PipelineError(f"Registry cannot promote a forbidden production path: {path}")
        actual = hashlib.sha256(_existing_repo_path(repo, path, "production asset").read_bytes()).hexdigest()
        if actual != ref["sha256"]:
            raise PipelineError(f"Production asset file hash mismatch: {path}")
        verified.append({**ref, "path": path, "kind": record["kind"],
                         "shots": record["shots"], "final_use_shots": link["shots"]})
    return verified


def _comparison_references(spec: dict, repo: str | Path | None) -> list[dict]:
    references = spec.get("comparison_references", [])
    if not isinstance(references, list):
        raise PipelineError("comparison_references must be a list")
    checked = []
    for reference in references:
        required = {"path", "purpose", "production_input"}
        if not isinstance(reference, dict) or set(reference) != required:
            raise PipelineError(f"Comparison references require exactly {sorted(required)}")
        path = _safe_relative(reference["path"], "comparison reference")
        if (reference["purpose"] not in COMPARISON_PURPOSES
                or reference["production_input"] is not False
                or _forbidden_input_path(path)):
            raise PipelineError("Comparison reference purpose is not allowlisted or attempts production use")
        if Path(path).suffix.lower() in SOURCE_SUFFIXES:
            raise PipelineError("Text/data belongs in source_inputs, not comparison_references")
        if repo is not None:
            _existing_repo_path(repo, path, "comparison reference")
        checked.append(dict(reference))
    return checked


def _verified_final_author_binding(decision: dict, spec: dict, repo: str | Path | None) -> dict:
    required = {
        "status", "author_id", "qa_task_id", "qa_artifact_path", "qa_artifact_sha256",
        "viewed_artifact", "approval_reference", "registry_ref",
    }
    if not isinstance(decision, dict) or set(decision) != required or decision.get("status") != "approved":
        raise PipelineError(f"Final author approval must contain exactly {sorted(required)}")
    if decision["author_id"] != "luis-m-minier":
        raise PipelineError("Final author approval is restricted to luis-m-minier")
    expected_task = f"{spec['pipeline_id']}-qa"
    if decision["qa_task_id"] != expected_task:
        raise PipelineError("Final author approval is bound to the wrong QA task")
    artifact = _safe_relative(decision["qa_artifact_path"], "QA artifact")
    if decision["viewed_artifact"] != artifact:
        raise PipelineError("Author approval must identify the exact viewed QA artifact")
    digest = decision["qa_artifact_sha256"]
    if not isinstance(digest, str) or not HASH_RE.fullmatch(digest):
        raise PipelineError("QA artifact digest must be an exact lowercase SHA-256")
    if not isinstance(decision["approval_reference"], str) or not decision["approval_reference"].strip():
        raise PipelineError("Final author approval needs a recorded approval reference")
    if repo is None:
        raise PipelineError("Final author approval requires repository and registry verification")
    actual = hashlib.sha256(_existing_repo_path(repo, artifact, "QA artifact").read_bytes()).hexdigest()
    if actual != digest:
        raise PipelineError("Final author approval QA artifact digest mismatch")

    ref = decision["registry_ref"]
    required_ref = {"asset_id", "version", "sha256", "final_use_id", "author_approval_id"}
    if not isinstance(ref, dict) or set(ref) != required_ref or ref.get("sha256") != digest:
        raise PipelineError(f"Final approval registry_ref requires exactly {sorted(required_ref)} and matching digest")
    _, state = _registry_state(repo)
    key = (ref.get("asset_id"), ref.get("version"))
    record = state["assets"].get(key)
    approval = state["approvals"].get(ref.get("author_approval_id"))
    link = state["final_uses"].get(ref.get("final_use_id"))
    if (record is None or record["path"] != artifact or record["sha256"] != digest
            or record.get("mode") != "production" or state["states"].get(key) != "canonical"
            or not link or (link.get("asset_id"), link.get("version")) != key
            or not set(spec["shots"]) <= set(record["shots"])
            or not set(spec["shots"]) <= set(link["shots"])):
        raise PipelineError("Final author approval does not match a canonical active registry asset")
    if (not approval or approval.get("type") != "author" or approval.get("approver_id") != "luis-m-minier"
            or approval.get("approver_role") != "author" or approval.get("asset_sha256") != digest
            or (approval.get("asset_id"), approval.get("version")) != key):
        raise PipelineError("Final author approval does not match Luis's registry approval record")
    return {key: decision[key] for key in required}


def _verified_timing_author_binding(decision: dict, spec: dict, repo: str | Path | None) -> dict:
    required = {
        "status", "author_id", "timing_task_id", "decision_record_path",
        "decision_record_sha256", "viewed_record", "approval_reference", "resolved_conflicts",
    }
    if not isinstance(decision, dict) or set(decision) != required or decision.get("status") != "approved":
        raise PipelineError(f"Timing author approval must contain exactly {sorted(required)}")
    if spec.get("timing", {}).get("status") != "resolved":
        raise PipelineError("Timing author approval cannot pass while timing.status remains unresolved")
    if decision["author_id"] != "luis-m-minier":
        raise PipelineError("Timing author approval is restricted to luis-m-minier")
    expected_task = f"{spec['pipeline_id']}-script-timing"
    if decision["timing_task_id"] != expected_task:
        raise PipelineError("Timing author approval is bound to the wrong timing task")
    path = _safe_relative(decision["decision_record_path"], "timing decision record")
    if decision["viewed_record"] != path:
        raise PipelineError("Timing author approval must identify the exact viewed decision record")
    digest = decision["decision_record_sha256"]
    if not isinstance(digest, str) or not HASH_RE.fullmatch(digest):
        raise PipelineError("Timing decision digest must be an exact lowercase SHA-256")
    if not isinstance(decision["approval_reference"], str) or not decision["approval_reference"].strip():
        raise PipelineError("Timing author approval needs a recorded approval reference")
    conflicts = spec["timing"].get("conflicts", [])
    allowed = {item["id"]: set(item["choices"]) for item in conflicts}
    selections = decision["resolved_conflicts"]
    if (not isinstance(selections, dict) or set(selections) != set(allowed)
            or any(choice not in allowed[conflict_id] for conflict_id, choice in selections.items())):
        raise PipelineError("Timing approval must resolve every conflict with one declared choice")
    if repo is None:
        raise PipelineError("Timing author approval requires a repository-backed decision record")
    record_path = _existing_repo_path(repo, path, "timing decision record")
    raw = record_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != digest:
        raise PipelineError("Timing author approval decision-record digest mismatch")
    try:
        record = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PipelineError("Timing decision record must be valid UTF-8 JSON") from exc
    expected_record = {
        "pipeline_id": spec["pipeline_id"], "shots": spec["shots"],
        "author_id": "luis-m-minier", "timing_task_id": expected_task,
        "resolved_conflicts": selections, "approval_reference": decision["approval_reference"],
    }
    if record != expected_record:
        raise PipelineError("Timing decision record content does not match the approved binding")
    return {key: decision[key] for key in required}


def validate_template(template: dict, roles_raw: dict) -> None:
    roles = _roles(roles_raw)
    stages = template.get("stages")
    if not isinstance(stages, list) or not stages:
        raise PipelineError("Template needs stages")
    by_id: dict[str, dict] = {}
    for stage in stages:
        if not isinstance(stage, dict):
            raise PipelineError("Each template stage must be an object")
        stage_id = _identifier(stage.get("id"), "stage id")
        if stage_id in by_id:
            raise PipelineError(f"Duplicate stage: {stage_id}")
        role = stage.get("role")
        reviewer = stage.get("reviewer")
        if role not in roles or reviewer not in roles:
            raise PipelineError(f"Unknown role or reviewer on {stage_id}")
        allowed = roles[role].get("reviewer", roles[role].get("reviewer_role", []))
        allowed = [allowed] if isinstance(allowed, str) else allowed
        if reviewer == role or reviewer not in allowed:
            raise PipelineError(f"{stage_id} lacks its independent designated reviewer")
        for field in ("depends_on", "artifact_kinds", "evidence_kinds", "acceptance"):
            _strings(stage.get(field), f"{stage_id}.{field}", allow_empty=field == "depends_on")
        if "requires_author_approval" in stage and type(stage["requires_author_approval"]) is not bool:
            raise PipelineError(f"{stage_id}.requires_author_approval must be true or false")
        if stage.get("requires_author_approval") and stage.get("author_approver") != "luis-m-minier":
            raise PipelineError(f"{stage_id}.author_approver must be luis-m-minier")
        if stage.get("art_direction_mode") not in ART_DIRECTION_MODES | {None}:
            raise PipelineError(f"Unknown art_direction_mode on {stage_id}")
        by_id[stage_id] = stage

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(stage_id: str) -> None:
        if stage_id in visiting:
            raise PipelineError("Stage dependency cycle")
        if stage_id in visited:
            return
        visiting.add(stage_id)
        for dependency in by_id[stage_id]["depends_on"]:
            if dependency not in by_id:
                raise PipelineError(f"Missing stage dependency: {dependency}")
            visit(dependency)
        visiting.remove(stage_id)
        visited.add(stage_id)

    for stage_id in by_id:
        visit(stage_id)

    gates = template.get("gates", [])
    gate_ids: set[str] = set()
    for gate in gates:
        gate_id = _identifier(gate.get("id"), "gate id")
        if gate_id in gate_ids or gate.get("kind") != "author":
            raise PipelineError("Gates must have unique ids and kind=author")
        if gate.get("after_stage") not in by_id:
            raise PipelineError(f"Gate {gate_id} has no valid after_stage")
        blocks = _strings(gate.get("blocks"), f"{gate_id}.blocks")
        if any(block not in by_id and block != "canonical delivery" for block in blocks):
            raise PipelineError(f"Gate {gate_id} blocks an unknown target")
        _strings(gate.get("required_evidence"), f"{gate_id}.required_evidence")
        gate_ids.add(gate_id)
    for stage in stages:
        if stage.get("gate_after") and stage["gate_after"] not in gate_ids:
            raise PipelineError(f"Unknown gate_after on {stage['id']}")
        if stage.get("gate_after") and not stage.get("requires_author_approval"):
            raise PipelineError(f"{stage['id']} has an author gate but is not ledger author-gated")
    for gate in gates:
        after = by_id[gate["after_stage"]]
        if after.get("gate_after") != gate["id"]:
            raise PipelineError(f"Author gate {gate['id']} is not linked from its after_stage")


def validate_spec(spec: dict, repo: str | Path | None = None) -> None:
    _identifier(spec.get("pipeline_id"), "pipeline_id")
    _identifier(spec.get("run"), "run")
    _strings(spec.get("shots"), "shots")
    sources = _strings(spec.get("source_inputs"), "source_inputs")
    for source in sources:
        safe = _source_input(source)
        if repo is not None:
            _verify_text_data_file(_existing_repo_path(repo, safe, "source input"), safe)
    if "assets" in spec:
        raise PipelineError("Caller-declared asset status is forbidden; use exact production_assets registry references")
    _verified_production_assets(spec, repo)
    _comparison_references(spec, repo)

    action = spec.get("full_scene_action")
    if not isinstance(action, dict) or set(action) != set(ACTION_FIELDS):
        raise PipelineError(f"full_scene_action must define exactly: {', '.join(ACTION_FIELDS)}")
    for field in ACTION_FIELDS:
        _strings(action[field], f"full_scene_action.{field}", allow_empty=field == "camera")
    non_camera = sum(len(action[field]) for field in ACTION_FIELDS if field != "camera")
    if not action["character"] or not action["environment"] or non_camera < 4:
        raise PipelineError("Full-scene action needs character and environmental motion; camera alone cannot qualify")

    timing = spec.get("timing")
    if not isinstance(timing, dict) or timing.get("status") not in {"resolved", "unresolved"}:
        raise PipelineError("timing.status must be resolved or unresolved")
    conflicts = timing.get("conflicts", [])
    if not isinstance(conflicts, list):
        raise PipelineError("timing.conflicts must be a list")
    if timing["status"] == "unresolved" and not conflicts:
        raise PipelineError("Unresolved timing requires explicit conflicts")
    for conflict in conflicts:
        if not isinstance(conflict, dict):
            raise PipelineError("Each timing conflict must be an object")
        _identifier(conflict.get("id"), "timing conflict id")
        _strings(conflict.get("sources"), "timing conflict sources")
        _strings(conflict.get("choices"), "timing conflict choices")
        if not isinstance(conflict.get("question"), str) or not conflict["question"].strip():
            raise PipelineError("Timing conflicts require a question")

    decisions = spec.get("gate_decisions", {})
    if not isinstance(decisions, dict):
        raise PipelineError("gate_decisions must be an object")
    for gate_id, decision in decisions.items():
        _identifier(gate_id, "gate decision id")
        if not isinstance(decision, dict) or decision.get("status") not in {"unresolved", "approved", "changes_requested"}:
            raise PipelineError(f"Invalid gate decision: {gate_id}")
        if decision["status"] == "approved":
            if gate_id == "final-author-approval":
                _verified_final_author_binding(decision, spec, repo)
            elif gate_id == "timing-author-approval":
                _verified_timing_author_binding(decision, spec, repo)
            else:
                raise PipelineError(f"Unsupported author gate: {gate_id}")


def build_pipeline(spec: dict, template: dict, roles_raw: dict, repo: str | Path | None = None) -> dict:
    """Return a deterministic DAG plus task envelopes accepted by Ledger.add."""
    validate_template(template, roles_raw)
    validate_spec(spec, repo)
    if repo is not None and any(stage.get("art_direction_mode") for stage in template["stages"]):
        _existing_repo_path(repo, "production/art_direction.json", "art direction contract")
    roles = _roles(roles_raw)
    run = spec["run"]
    prefix = spec["pipeline_id"]
    verified_assets = _verified_production_assets(spec, repo)
    comparison_references = _comparison_references(spec, repo)
    sources = list(dict.fromkeys(spec["source_inputs"] + [asset["path"] for asset in verified_assets]))
    gate_decisions = spec.get("gate_decisions", {})
    known_gates = {gate["id"] for gate in template.get("gates", [])}
    unknown_gates = set(gate_decisions) - known_gates
    if unknown_gates:
        raise PipelineError(f"Unknown gate decisions: {sorted(unknown_gates)}")
    gates: list[dict] = []
    for gate in template.get("gates", []):
        decision = gate_decisions.get(gate["id"], {"status": "unresolved", "evidence": []})
        built_gate = {**gate, "status": decision["status"], "evidence": decision.get("evidence", [])}
        if decision["status"] == "approved":
            if gate["id"] == "final-author-approval":
                built_gate["binding"] = _verified_final_author_binding(decision, spec, repo)
            elif gate["id"] == "timing-author-approval":
                built_gate["binding"] = _verified_timing_author_binding(decision, spec, repo)
        gates.append(built_gate)

    task_ids = {stage["id"]: _identifier(f"{prefix}-{stage['id']}", "generated task id")
                for stage in template["stages"]}
    tasks = []
    for stage in template["stages"]:
        stage_id = stage["id"]
        task_id = task_ids[stage_id]
        output_dir = f"production/runs/{run}/tasks/{task_id}"
        dependencies = [task_ids[item] for item in stage["depends_on"]]
        upstream_dirs = [f"production/runs/{run}/tasks/{task_ids[item]}" for item in stage["depends_on"]]
        blocked_by = [gate["id"] for gate in gates
                      if gate["status"] != "approved" and stage_id in gate["blocks"]]
        objective = (
            f"Complete {stage_id} for {', '.join(spec['shots'])} using only approved inputs. "
            "Produce every contracted artifact and evidence item; submit for independent review."
        )
        task = {
            "id": task_id,
            "role": stage["role"],
            "reviewer_role": stage["reviewer"],
            "shots": spec["shots"],
            "objective": objective,
            "inputs": list(dict.fromkeys(sources + upstream_dirs)),
            "output_dir": output_dir,
            "depends_on": dependencies,
            "acceptance_criteria": stage["acceptance"],
            "budget": {"max_tool_calls": 40, "max_seconds": 3600, "max_output_tokens": 20000,
                       "max_cost_usd": _generation_budget(repo, roles_raw, stage["role"])},
            "completion_contract": {
                "required_artifact_kinds": stage["artifact_kinds"],
                "required_evidence_kinds": stage["evidence_kinds"],
                "independent_review_required": True,
                "technical_gate": bool(stage.get("technical_gate", False)),
                "author_gate": stage.get("gate_after")
            },
            "full_scene_action": spec["full_scene_action"],
            "blocked_by_gates": blocked_by,
            "require_host_bindings": True,
        }
        if stage.get("requires_author_approval") is not None:
            task["requires_author_approval"] = stage["requires_author_approval"]
            if stage["requires_author_approval"]:
                task["author_approver"] = stage["author_approver"]
        if stage.get("art_direction_mode"):
            task["art_direction_mode"] = stage["art_direction_mode"]
            task["inputs"] = list(dict.fromkeys(task["inputs"] + ["production/art_direction.json"]))
        # Runtime persists the action and deliverable contracts for workers,
        # reviewers and revisions. Gate snapshots remain planning metadata;
        # live author-gated dependencies determine runtime eligibility.
        tasks.append(task)

    ready = [task["id"] for task in tasks if not task["depends_on"] and not task["blocked_by_gates"]]
    stage_ids = {stage["id"] for stage in template["stages"]}
    production_blocked = any(
        gate["status"] != "approved" and any(block in stage_ids for block in gate["blocks"])
        for gate in gates
    )
    return {
        "version": 1,
        "template": template["name"],
        "pipeline_id": prefix,
        "run": run,
        "shots": spec["shots"],
        "status": "blocked" if production_blocked else "planned",
        "timing_status": spec["timing"]["status"],
        "timing_conflicts": spec["timing"].get("conflicts", []),
        "verified_production_assets": verified_assets,
        "comparison_references": comparison_references,
        "gates": gates,
        "tasks": tasks,
        "ready_tasks": ready,
        "canonical_delivery_blocked": next(
            (gate["status"] != "approved" for gate in gates if gate["id"] == "final-author-approval"), True
        ),
    }


def ledger_task(task: dict) -> dict:
    """Return only the fields persisted by ``Ledger.add``."""
    fields = {
        "id", "role", "shots", "objective", "inputs", "output_dir",
        "depends_on", "acceptance_criteria", "budget", "requires_author_approval", "author_approver",
        "art_direction_mode", "require_host_bindings",
        "full_scene_action", "completion_contract",
    }
    return {key: task[key] for key in fields if key in task}


def validate_completion(pipeline: dict, task_id: str, record: dict, repo: str | Path) -> bool:
    """Require real artifacts/evidence and an independent designated review."""
    try:
        task = next(task for task in pipeline["tasks"] if task["id"] == task_id)
    except StopIteration as exc:
        raise PipelineError(f"Unknown pipeline task: {task_id}") from exc
    if task["blocked_by_gates"]:
        raise PipelineError(f"Task is blocked by author gate: {', '.join(task['blocked_by_gates'])}")
    if record.get("status") != "approved":
        raise PipelineError("A completed stage requires approved status")
    artifacts = record.get("artifacts")
    evidence = record.get("evidence")
    if not isinstance(artifacts, list) or not artifacts:
        raise PipelineError("Actual artifacts are required")
    if not isinstance(evidence, list) or not evidence:
        raise PipelineError("Specific evidence is required")
    kinds = {item.get("kind") for item in artifacts if isinstance(item, dict)}
    missing = set(task["completion_contract"]["required_artifact_kinds"]) - kinds
    if missing:
        raise PipelineError(f"Missing artifact kinds: {sorted(missing)}")
    evidence_kinds = {item.get("kind") for item in evidence if isinstance(item, dict)
                      and isinstance(item.get("detail"), str) and item["detail"].strip()}
    missing_evidence = set(task["completion_contract"]["required_evidence_kinds"]) - evidence_kinds
    if missing_evidence:
        raise PipelineError(f"Missing evidence kinds: {sorted(missing_evidence)}")
    repo_root = Path(repo).resolve()
    output_root = (repo_root / task["output_dir"]).resolve()
    try:
        output_root.relative_to(repo_root)
    except ValueError as exc:
        raise PipelineError("Task output directory escapes the repository") from exc
    for artifact in artifacts:
        if not isinstance(artifact, dict) or not isinstance(artifact.get("path"), str):
            raise PipelineError("Artifact entries require path and kind")
        relative = _safe_relative(artifact["path"], "artifact")
        path = (Path(repo) / relative).resolve()
        try:
            path.relative_to(output_root)
        except ValueError as exc:
            raise PipelineError("Artifact escapes the task output directory") from exc
        if not path.is_file():
            raise PipelineError(f"Missing artifact file: {relative}")
    review = record.get("review")
    if (not isinstance(review, dict) or review.get("decision") != "approve"
            or review.get("role") != task["reviewer_role"]
            or not review.get("agent_id") or review.get("agent_id") == record.get("agent_id")
            or not review.get("evidence")):
        raise PipelineError("Independent designated technical review with evidence is required")
    return True


def validate_author_gate(pipeline: dict, gate_id: str, repo: str | Path | None = None) -> bool:
    """Validate author approval without confusing it with technical review."""
    try:
        gate = next(gate for gate in pipeline["gates"] if gate["id"] == gate_id)
    except StopIteration as exc:
        raise PipelineError(f"Unknown author gate: {gate_id}") from exc
    if gate.get("kind") != "author" or gate.get("status") != "approved":
        raise PipelineError(f"Author gate is not approved: {gate_id}")
    if gate_id == "final-author-approval":
        binding = gate.get("binding")
        if not isinstance(binding, dict):
            raise PipelineError("Final author gate lacks a verified artifact binding")
        _verified_final_author_binding(binding, {
            "pipeline_id": pipeline["pipeline_id"], "shots": pipeline["shots"]
        }, repo)
        return True
    if gate_id == "timing-author-approval":
        binding = gate.get("binding")
        if not isinstance(binding, dict):
            raise PipelineError("Timing author gate lacks a verified decision-record binding")
        _verified_timing_author_binding(binding, {
            "pipeline_id": pipeline["pipeline_id"], "shots": pipeline["shots"],
            "timing": {"status": pipeline["timing_status"], "conflicts": pipeline["timing_conflicts"]},
        }, repo)
        return True
    evidence = gate.get("evidence", [])
    if len(evidence) < len(gate["required_evidence"]):
        raise PipelineError(f"Author gate lacks its required evidence: {gate_id}")
    return True


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec")
    parser.add_argument("--repo", default=".")
    parser.add_argument("--template", default="production/pipeline_templates/complete_shot.json")
    parser.add_argument("--roles", default="production/roles.json")
    parser.add_argument("--ledger-tasks-dir", help="Optionally write one Ledger.add JSON file per task")
    args = parser.parse_args(argv)
    repo = Path(args.repo).resolve()
    pipeline = build_pipeline(
        load_json(repo / args.spec), load_json(repo / args.template), load_json(repo / args.roles), repo
    )
    if args.ledger_tasks_dir:
        destination = (repo / _safe_relative(args.ledger_tasks_dir, "ledger tasks directory"))
        destination.mkdir(parents=True, exist_ok=True)
        for task in pipeline["tasks"]:
            (destination / f"{task['id']}.json").write_text(json.dumps(ledger_task(task), indent=2) + "\n")
    print(json.dumps(pipeline, indent=2))


if __name__ == "__main__":
    main()
