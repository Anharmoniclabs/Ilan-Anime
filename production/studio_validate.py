"""Validate AnimeStudio architecture separately from episode completion."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

try:
    from production.asset_registry import AssetRegistry, validate_approval
    from production.host_handoff import HandoffRegistry
    from production.pipeline import ART_DIRECTION_MODES, build_pipeline, validate_template
    from production.runtime import Ledger
except ModuleNotFoundError:
    from asset_registry import AssetRegistry, validate_approval
    from host_handoff import HandoffRegistry
    from pipeline import ART_DIRECTION_MODES, build_pipeline, validate_template
    from runtime import Ledger


VISUAL_ROLES = {
    "storyboard", "layout-artist", "character-designer", "prop-designer",
    "background-painter", "art-director", "color-designer", "key-animator",
    "animation-supervisor", "inbetweener", "cleanup-artist", "ink-paint-artist",
    "effects-animator", "character-rigger", "cg-director", "compositor",
    "editor", "quality-review",
}

FINAL_PICTURE_KINDS = {"final-animation", "final-picture", "picture-master"}
FINAL_AUDIO_KINDS = {"final-audio", "final-mix", "audio-master"}
SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")

COMPONENTS = [
    "production/runtime.py", "production/host_handoff.py", "production/roles.json",
    "production/art_direction.json", "production/validate_art_direction.py",
    "production/asset_registry.py", "production/pipeline.py",
    "production/pipeline_templates/complete_shot.json", "production/dashboard.py",
    "production/examples/s01_11_12_pipeline.json",
    "production/examples/asset_registry.json",
    "production/examples/approval_record.json",
    "production/schemas/approval-record.schema.json",
    "production/schemas/asset-record.schema.json",
    "production/schemas/asset-registry.schema.json",
    "docs/STUDIO_STANDARD.md", "docs/ART_ACCEPTANCE.md", "docs/ASSET_PIPELINE.md",
    "docs/SHOT_PIPELINE.md", "docs/HOST_HANDOFF.md", "docs/DASHBOARD.md",
]


class StudioValidationError(ValueError):
    pass


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def validate_role_contracts(root, roles_raw):
    roles = roles_raw.get("roles", roles_raw) if isinstance(roles_raw, dict) else {}
    if not isinstance(roles, dict) or not roles:
        raise StudioValidationError("production/roles.json must be a nonempty mapping")
    for role_id, role in roles.items():
        if not isinstance(role, dict):
            raise StudioValidationError(f"{role_id}: role record is not an object")
        reviewer = role.get("reviewer")
        if reviewer == role_id or reviewer not in roles:
            raise StudioValidationError(f"{role_id}: missing independent registered reviewer")
        skill = role.get("skill")
        if not isinstance(skill, str) or not (root / skill).is_file():
            raise StudioValidationError(f"{role_id}: missing skill file")
        text = (root / skill).read_text(encoding="utf-8")
        if "TODO" in text:
            raise StudioValidationError(f"{role_id}: skill contains TODO")
        if role_id in VISUAL_ROLES and "production/art_direction.json" not in text:
            raise StudioValidationError(
                f"{role_id}: visual skill does not require the machine art contract")
    return roles


def validate_art_contract(contract):
    required = {"contract_id", "version", "artist", "canonical_document",
                "source_precedence", "global_rules", "criteria", "modes", "promotion"}
    if not isinstance(contract, dict) or not required <= contract.keys():
        raise StudioValidationError("art direction contract is incomplete")
    modes = contract.get("modes")
    if not isinstance(modes, dict) or set(modes) != ART_DIRECTION_MODES:
        raise StudioValidationError("art direction modes differ from the runtime contract")
    criteria = contract.get("criteria")
    tiers = {item.get("tier") for item in contract.get("source_precedence", [])
             if isinstance(item, dict)}
    for mode_id, mode in modes.items():
        if (not isinstance(mode, dict)
                or not set(mode.get("required_source_tiers", [])) <= tiers
                or not set(mode.get("required_criteria", [])) <= set(criteria or {})):
            raise StudioValidationError(f"{mode_id}: invalid art-direction requirements")
    promotion = contract.get("promotion")
    if not isinstance(promotion, dict) or promotion.get("author_id") != "luis-m-minier":
        raise StudioValidationError("canonical art promotion must be restricted to luis-m-minier")


def _qa_release_shots(task, required, asset_digests_by_shot, root):
    """Return shots covered by one genuine, artifact- and asset-bound QA task."""
    task_id = task.get("id", "")
    if not task_id.endswith("-qa"):
        return set()
    prefix = task_id[:-3]
    expected_dependencies = {
        f"{prefix}-edit", f"{prefix}-final-manifest", f"{prefix}-pipeline-contract",
    }
    if (task.get("role") != "quality-review" or task.get("state") != "author-approved"
            or task.get("require_host_bindings") is not True
            or task.get("requires_author_approval") is not True
            or task.get("author_approver") != "luis-m-minier"
            or task.get("art_direction_mode") != "STORY_FRAME"
            or not expected_dependencies <= set(task.get("depends_on", []))):
        return set()
    author = task.get("author_review", {})
    result = task.get("result", {})
    if (author.get("author") != "luis-m-minier" or author.get("decision") != "approve"
            or result.get("pipeline_id") != prefix):
        return set()
    task_shots = required & set(task.get("shots", []))
    if not task_shots:
        return set()
    expected_digests = set().union(*(asset_digests_by_shot.get(shot, set()) for shot in task_shots))
    declared_digests = result.get("release_asset_sha256s")
    if (not expected_digests or not isinstance(declared_digests, list)
            or len(declared_digests) != len(set(declared_digests))
            or any(not isinstance(item, str) or not SHA256_RE.fullmatch(item)
                   for item in declared_digests)
            or set(declared_digests) != expected_digests):
        return set()
    report = result.get("qa_report")
    if not isinstance(report, dict) or set(report) != {"path", "sha256"}:
        return set()
    report_path = report.get("path")
    if (not isinstance(report_path, str) or report_path not in result.get("artifacts", [])
            or not isinstance(report.get("sha256"), str)
            or not SHA256_RE.fullmatch(report["sha256"])):
        return set()
    path = (root / report_path).resolve()
    output = (root / task.get("output_dir", "")).resolve()
    try:
        path.relative_to(output)
        output.relative_to(root)
    except ValueError:
        return set()
    if (not path.is_file() or path.is_symlink()
            or hashlib.sha256(path.read_bytes()).hexdigest() != report["sha256"]):
        return set()
    return task_shots


def episode_release_evidence(root, shots):
    """Derive release coverage from canonical bytes and author-approved QA, never labels alone."""
    required = {shot.get("id") for shot in shots if isinstance(shot, dict) and shot.get("id")}
    result = {"picture_shots": 0, "audio_shots": 0, "qa_shots": 0, "missing": []}
    registry_path = root / "production/asset-registry.json"
    if not required or not registry_path.is_file():
        result["missing"].append("canonical production asset registry")
        return False, result
    try:
        state = AssetRegistry(root).verify(check_files=True)
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        result["missing"].append(f"valid canonical asset registry: {exc}")
        return False, result

    picture, audio = set(), set()
    asset_digests_by_shot = {shot: set() for shot in required}
    for link in state["final_uses"].values():
        if not isinstance(link, dict):
            continue
        ref = (link.get("asset_id"), link.get("version"))
        record = state["assets"].get(ref)
        if (not record or state["states"].get(ref) != "canonical"
                or record.get("mode") != "production"):
            continue
        covered = required & set(link.get("shots", [])) & set(record.get("shots", []))
        if record.get("kind") in FINAL_PICTURE_KINDS:
            picture |= covered
            for shot in covered:
                asset_digests_by_shot[shot].add(record["sha256"])
        if record.get("kind") in FINAL_AUDIO_KINDS:
            audio |= covered
            for shot in covered:
                asset_digests_by_shot[shot].add(record["sha256"])

    qa = set()
    runs_root = root / "production/runs"
    if runs_root.is_dir():
        for ledger_path in runs_root.glob("*/ledger.json"):
            try:
                ledger = Ledger(root, ledger_path.parent.name)
                ledger.validate()
            except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError):
                continue
            for task in ledger.data["tasks"].values():
                qa |= _qa_release_shots(task, required, asset_digests_by_shot, root)

    result.update(picture_shots=len(picture), audio_shots=len(audio), qa_shots=len(qa))
    for label, covered in (("canonical final picture", picture), ("canonical final audio", audio),
                           ("author-approved QA", qa)):
        missing = sorted(required - covered)
        if missing:
            result["missing"].append(f"{label}: {len(missing)} shots")
    return picture == required and audio == required and qa == required, result


def validate_studio(repo):
    root = Path(repo).resolve()
    errors, warnings = [], []
    for relative in COMPONENTS:
        if not (root / relative).is_file():
            errors.append(f"missing component: {relative}")

    roles_raw, roles = {}, {}
    try:
        roles_raw = _load(root / "production/roles.json")
        roles = validate_role_contracts(root, roles_raw)
    except (OSError, json.JSONDecodeError, KeyError, TypeError, StudioValidationError) as exc:
        errors.append(f"role contracts: {exc}")

    try:
        validate_art_contract(_load(root / "production/art_direction.json"))
    except (OSError, json.JSONDecodeError, KeyError, TypeError, StudioValidationError) as exc:
        errors.append(f"art direction contract: {exc}")

    schema_dir = root / "production/schemas"
    if not schema_dir.is_dir():
        errors.append("missing schema directory: production/schemas")
    for schema_path in sorted(schema_dir.glob("*.json")):
        try:
            schema = _load(schema_path)
            if not isinstance(schema, dict) or not schema.get("$schema") or schema.get("type") != "object":
                raise StudioValidationError("must declare $schema and type=object")
        except (OSError, json.JSONDecodeError, StudioValidationError) as exc:
            errors.append(f"schema {schema_path.name}: {exc}")

    try:
        template = _load(root / "production/pipeline_templates/complete_shot.json")
        validate_template(template, roles_raw)
        spec = _load(root / "production/examples/s01_11_12_pipeline.json")
        pipeline = build_pipeline(spec, template, roles_raw, root)
        if len(pipeline["tasks"]) != len(template["stages"]):
            raise StudioValidationError("built task count differs from template stage count")
        if not pipeline["tasks"] or any(not task.get("require_host_bindings")
                                        for task in pipeline["tasks"]):
            raise StudioValidationError("every generated task must require real host bindings")
        expected_ready = [f"{spec['pipeline_id']}-script-timing"]
        if pipeline["status"] != "blocked" or pipeline["ready_tasks"] != expected_ready:
            raise StudioValidationError("reference pipeline no longer fails closed on timing approval")
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        errors.append(f"shot pipeline: {exc}")

    try:
        AssetRegistry(root, "production/examples/asset_registry.json").verify(check_files=True)
        validate_approval(_load(root / "production/examples/approval_record.json"))
        if (root / "production/asset-registry.json").exists():
            AssetRegistry(root).verify(check_files=True)
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        errors.append(f"asset registry: {exc}")

    runs_root = root / "production/runs"
    if runs_root.is_dir():
        for ledger_path in sorted(runs_root.glob("*/ledger.json")):
            try:
                ledger = Ledger(root, ledger_path.parent.name)
                ledger.validate()
                if (ledger_path.parent / "handoffs.json").exists():
                    HandoffRegistry(root, ledger.run).validate()
            except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
                errors.append(f"run {ledger_path.parent.name}: {exc}")

    episode_path = root / "projects/cemi_episode_01/data/episode.json"
    try:
        episode = _load(episode_path)
        shots = episode.get("shots", [])
    except (OSError, json.JSONDecodeError, AttributeError, TypeError) as exc:
        errors.append(f"episode data: {exc}")
        episode, shots = {}, []
    cursor = 0
    for shot in shots:
        if shot.get("start_frame") != cursor:
            errors.append(f"{shot.get('id', 'unknown')}: timeline is not contiguous")
        cursor = shot.get("end_frame", cursor)
    if cursor != episode.get("body_frames"):
        errors.append("episode body frame count does not match shot timeline")
    approved_animation = sum(shot.get("animation_status") == "approved" for shot in shots)
    approved_voice = sum(shot.get("voice_status") in {"approved", "no_dialogue"} for shot in shots)
    release_evidence_ready, release_evidence = episode_release_evidence(root, shots)
    if approved_animation != len(shots):
        warnings.append(f"episode unfinished: {approved_animation}/{len(shots)} animated shots approved")
    if approved_voice != len(shots):
        warnings.append(f"episode unfinished: {approved_voice}/{len(shots)} shot audio states approved/no-dialogue")

    return {
        "architecture_valid": not errors,
        "episode_ready": bool(shots) and not errors and release_evidence_ready
                         and approved_animation == len(shots) and approved_voice == len(shots),
        "roles": len(roles),
        "visual_roles": len(VISUAL_ROLES & set(roles)),
        "shots": len(shots),
        "approved_animation_shots": approved_animation,
        "approved_audio_shots": approved_voice,
        "release_evidence": release_evidence,
        "errors": errors,
        "warnings": warnings,
        "truth": "Architecture validation never proves visual quality or finished animation."
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".")
    args = parser.parse_args(argv)
    try:
        report = validate_studio(args.repo)
        print(json.dumps(report, indent=2))
        return 0 if report["architecture_valid"] else 2
    except (OSError, json.JSONDecodeError, KeyError, TypeError, StudioValidationError) as exc:
        print(json.dumps({"architecture_valid": False, "errors": [str(exc)]}, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
