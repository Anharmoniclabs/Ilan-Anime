"""Validate Cemí art-review records without claiming to inspect artwork pixels.

The validator proves that a report is complete, internally consistent, bound to
one asset digest, and carries separate technical and author approvals. Human
observations and evidence files remain the evidence; this program cannot decide
whether an image is beautiful, on-model, or actually matches those observations.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath
import re
import sys


SHA256 = re.compile(r"[0-9a-f]{64}")


class ArtDirectionError(ValueError):
    """A report cannot be promoted under the art-direction contract."""


def _object(value, label):
    if not isinstance(value, dict):
        raise ArtDirectionError(f"{label} must be an object")
    return value


def _text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ArtDirectionError(f"{label} must be a nonempty string")
    return value.strip()


def _digest(value, label):
    value = _text(value, label)
    if not SHA256.fullmatch(value):
        raise ArtDirectionError(f"{label} must be a lowercase SHA-256 digest")
    return value


def _relative(value, label):
    value = _text(value, label)
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or value.startswith("./"):
        raise ArtDirectionError(f"{label} must be a safe repository-relative path")
    return value


def validate_report(report, contract):
    """Return a deterministic promotion result or raise ``ArtDirectionError``."""
    report = _object(report, "report")
    contract = _object(contract, "contract")
    if report.get("contract_id") != contract.get("contract_id"):
        raise ArtDirectionError("contract_id does not match")
    if report.get("contract_version") != contract.get("version"):
        raise ArtDirectionError("contract_version does not match")

    asset = _object(report.get("asset"), "asset")
    asset_id = _text(asset.get("id"), "asset.id")
    _relative(asset.get("path"), "asset.path")
    digest = _digest(asset.get("sha256"), "asset.sha256")
    _text(asset.get("creator_id"), "asset.creator_id")
    _text(asset.get("requested_scope"), "asset.requested_scope")
    mode_id = _text(asset.get("mode"), "asset.mode")
    modes = _object(contract.get("modes"), "contract.modes")
    if mode_id not in modes:
        raise ArtDirectionError(f"asset.mode is unknown: {mode_id}")
    mode = _object(modes[mode_id], f"contract.modes.{mode_id}")

    promotion_contract = _object(contract.get("promotion"), "contract.promotion")
    source_status = _text(asset.get("source_status"), "asset.source_status")
    allowed_statuses = promotion_contract.get("allowed_source_statuses", [])
    if source_status not in allowed_statuses:
        if source_status == "rejected":
            raise ArtDirectionError("rejected assets are terminal; create a new revision and review it from the start")
        raise ArtDirectionError("asset.source_status is not eligible for canonical promotion")

    promotion = _object(report.get("promotion"), "promotion")
    expected_target = promotion_contract.get("target_status")
    if promotion.get("target_status") != expected_target:
        raise ArtDirectionError(f"promotion.target_status must be {expected_target}")

    required_tiers = mode.get("required_source_tiers")
    if not isinstance(required_tiers, list) or not all(type(tier) is int for tier in required_tiers):
        raise ArtDirectionError("contract mode has invalid required_source_tiers")
    sources = report.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ArtDirectionError("sources must be a nonempty list")
    authoritative = {}
    last_tier = 0
    known_sources = {item["tier"]: item["id"] for item in contract.get("source_precedence", [])}
    for index, source in enumerate(sources):
        source = _object(source, f"sources[{index}]")
        tier = source.get("tier")
        if type(tier) is not int or tier not in known_sources:
            raise ArtDirectionError(f"sources[{index}].tier is invalid")
        if tier < last_tier:
            raise ArtDirectionError("sources must be listed in canonical precedence order")
        last_tier = tier
        if source.get("id") != known_sources[tier]:
            raise ArtDirectionError(f"sources[{index}].id does not match tier {tier}")
        _text(source.get("reference"), f"sources[{index}].reference")
        usage = source.get("usage")
        status = source.get("status")
        if usage not in {"authoritative", "comparison_only"}:
            raise ArtDirectionError(f"sources[{index}].usage is invalid")
        if usage == "authoritative":
            if status != "approved":
                raise ArtDirectionError("authoritative sources must be approved, never rejected or provisional")
            if tier in authoritative:
                raise ArtDirectionError(f"duplicate authoritative source tier: {tier}")
            authoritative[tier] = source
    missing_tiers = [tier for tier in required_tiers if tier not in authoritative]
    if missing_tiers:
        raise ArtDirectionError(f"missing authoritative source tiers for {mode_id}: {missing_tiers}")

    declared_criteria = _object(contract.get("criteria"), "contract.criteria")
    required_criteria = mode.get("required_criteria")
    if not isinstance(required_criteria, list) or not required_criteria:
        raise ArtDirectionError("contract mode has no required criteria")
    criteria = _object(report.get("criteria"), "criteria")
    unknown = sorted(set(criteria) - set(declared_criteria))
    if unknown:
        raise ArtDirectionError(f"unknown criteria: {unknown}")
    missing = [criterion for criterion in required_criteria if criterion not in criteria]
    if missing:
        raise ArtDirectionError(f"missing required criteria: {missing}")
    for criterion in required_criteria:
        finding = _object(criteria[criterion], f"criteria.{criterion}")
        if finding.get("decision") != "pass":
            raise ArtDirectionError(f"criteria.{criterion}.decision must be pass")
        _text(finding.get("observation"), f"criteria.{criterion}.observation")
        evidence = finding.get("evidence_paths")
        if not isinstance(evidence, list) or not evidence:
            raise ArtDirectionError(f"criteria.{criterion}.evidence_paths must be nonempty")
        for index, path in enumerate(evidence):
            _relative(path, f"criteria.{criterion}.evidence_paths[{index}]")

    technical = _object(report.get("technical_review"), "technical_review")
    if technical.get("decision") != "approve":
        raise ArtDirectionError("technical_review.decision must be approve")
    reviewer = _text(technical.get("reviewer_id"), "technical_review.reviewer_id")
    if reviewer == asset["creator_id"]:
        raise ArtDirectionError("technical reviewer must be independent from the asset creator")
    _text(technical.get("reviewer_role"), "technical_review.reviewer_role")
    _text(technical.get("observation"), "technical_review.observation")
    if _digest(technical.get("asset_sha256"), "technical_review.asset_sha256") != digest:
        raise ArtDirectionError("technical review is not bound to the asset digest")

    author = _object(report.get("author_approval"), "author_approval")
    if author.get("decision") != "approved":
        raise ArtDirectionError("explicit author approval is required for canonical promotion")
    if author.get("author_id") != promotion_contract.get("author_id"):
        raise ArtDirectionError("author_approval.author_id does not match the contract")
    _text(author.get("author_statement"), "author_approval.author_statement")
    _relative(author.get("approval_reference"), "author_approval.approval_reference")
    if _digest(author.get("asset_sha256"), "author_approval.asset_sha256") != digest:
        raise ArtDirectionError("author approval is not bound to the asset digest")

    return {
        "valid": True,
        "contract_id": contract["contract_id"],
        "contract_version": contract["version"],
        "asset_id": asset_id,
        "asset_sha256": digest,
        "mode": mode_id,
        "promotion": expected_target,
        "technical_review": "approved",
        "author_approval": "approved"
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", help="Art acceptance report JSON")
    parser.add_argument("--contract", default="production/art_direction.json")
    args = parser.parse_args(argv)
    try:
        report = json.loads(Path(args.report).read_text())
        contract = json.loads(Path(args.contract).read_text())
        print(json.dumps(validate_report(report, contract), indent=2, sort_keys=True))
        return 0
    except (ArtDirectionError, OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        print(json.dumps({"valid": False, "error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
