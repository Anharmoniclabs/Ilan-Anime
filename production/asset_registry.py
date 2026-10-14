"""Append-only production asset registry (Python standard library only).

The registry stores repository-relative paths and SHA-256 content hashes.  State
is reconstructed from a hash-chained event log; existing asset versions and
approval decisions are never edited in place.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import tempfile
from datetime import datetime, timezone
from urllib.parse import urlsplit


STATES = {
    "exploratory", "submitted", "technical-approved", "author-approved",
    "canonical", "rejected",
}
TRANSITIONS = {
    "exploratory": {"submitted", "rejected"},
    "submitted": {"technical-approved", "rejected"},
    "technical-approved": {"author-approved", "rejected"},
    "author-approved": {"canonical", "rejected"},
    "canonical": {"rejected"},
    "rejected": set(),
}
MODES = {"source", "reference", "work-in-progress", "production"}
ID_RE = re.compile(r"[a-z0-9][a-z0-9._-]{0,95}\Z")
SHOT_RE = re.compile(r"[A-Z][A-Z0-9_-]{1,39}\Z")
HASH_RE = re.compile(r"[0-9a-f]{64}\Z")
APPROVAL_TYPES = {"technical", "author"}


class AssetRegistryError(ValueError):
    """Invalid asset data, state transition, approval, or registry history."""


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest(value):
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _identifier(value, label="identifier"):
    if not isinstance(value, str) or not ID_RE.fullmatch(value):
        raise AssetRegistryError(f"{label} must be 1-96 lowercase letters, digits, dot, underscore, or hyphen")
    return value


def _timestamp(value):
    if not isinstance(value, str):
        raise AssetRegistryError("Timestamp must be an ISO-8601 string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise AssetRegistryError("Timestamp must be valid ISO-8601") from exc
    if parsed.tzinfo is None:
        raise AssetRegistryError("Timestamp must include a timezone")
    return value


def _now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _repo_path(value):
    """Return a safe, portable repository-relative POSIX path."""
    if not isinstance(value, str) or not value or "\\" in value or "?" in value or "#" in value:
        raise AssetRegistryError("Asset path must be a clean repository-relative POSIX path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} or part.startswith(".") for part in path.parts):
        raise AssetRegistryError("Asset path must not be absolute, hidden, or traverse directories")
    if urlsplit(value).scheme:
        raise AssetRegistryError("Asset path must not be a URL")
    return path.as_posix()


def _public_url(value):
    if value is None:
        return
    if not isinstance(value, str):
        raise AssetRegistryError("public_source_url must be a string")
    parsed = urlsplit(value)
    host = (parsed.hostname or "").lower()
    if (parsed.scheme != "https" or not host or parsed.username or parsed.password
            or parsed.query or parsed.fragment or host in {"localhost", "127.0.0.1", "::1"}
            or host.endswith(".local")):
        raise AssetRegistryError("Only public HTTPS source URLs without credentials, query strings, or fragments are allowed")


def _strings(value, label, pattern=None):
    if (not isinstance(value, list) or len(value) != len(set(value))
            or any(not isinstance(x, str) or not x.strip() for x in value)):
        raise AssetRegistryError(f"{label} must be a duplicate-free list of nonempty strings")
    if pattern and any(not pattern.fullmatch(x) for x in value):
        raise AssetRegistryError(f"{label} contains an invalid value")
    return list(value)


def _continuity(value):
    required = {"character_ids", "costume_ids", "prop_ids", "time", "location"}
    if not isinstance(value, dict) or set(value) != required:
        raise AssetRegistryError(f"continuity must contain exactly {sorted(required)}")
    result = {name: _strings(value[name], f"continuity.{name}")
              for name in ("character_ids", "costume_ids", "prop_ids")}
    for name in ("time", "location"):
        if not isinstance(value[name], str) or not value[name].strip():
            raise AssetRegistryError(f"continuity.{name} must be a nonempty string")
        result[name] = value[name]
    return result


def _provenance(value):
    required = {"origin", "creator", "license", "source_assets", "notes"}
    allowed = required | {"public_source_url"}
    if not isinstance(value, dict) or not required <= value.keys() or not value.keys() <= allowed:
        raise AssetRegistryError(f"provenance requires {sorted(required)} and only supports public_source_url additionally")
    for name in ("origin", "license", "notes"):
        if not isinstance(value[name], str) or not value[name].strip():
            raise AssetRegistryError(f"provenance.{name} must be a nonempty string")
    _identifier(value["creator"], "provenance creator")
    if not isinstance(value["source_assets"], list):
        raise AssetRegistryError("provenance.source_assets must be a list")
    sources = []
    for ref in value["source_assets"]:
        if not isinstance(ref, dict) or set(ref) != {"asset_id", "version"}:
            raise AssetRegistryError("Each provenance source asset needs asset_id and version")
        sources.append({"asset_id": _identifier(ref["asset_id"], "source asset ID"),
                        "version": _positive_int(ref["version"], "source asset version")})
    result = {name: value[name] for name in ("origin", "creator", "license")}
    result["source_assets"] = sources
    result["notes"] = value["notes"]
    if "public_source_url" in value:
        _public_url(value["public_source_url"])
        result["public_source_url"] = value["public_source_url"]
    return result


def _positive_int(value, label):
    if type(value) is not int or value < 1:
        raise AssetRegistryError(f"{label} must be a positive integer")
    return value


def _reference(value, label="asset reference"):
    if not isinstance(value, dict) or set(value) != {"asset_id", "version"}:
        raise AssetRegistryError(f"{label} must contain exactly asset_id and version")
    return {"asset_id": _identifier(value["asset_id"], "asset ID"),
            "version": _positive_int(value["version"], "asset version")}


def validate_approval(value, expected_type=None):
    required = {"approval_id", "type", "asset_id", "version", "asset_sha256",
                "approver_id", "approver_role", "evidence", "at"}
    if not isinstance(value, dict) or set(value) != required:
        raise AssetRegistryError(f"Approval record must contain exactly {sorted(required)}")
    result = dict(value)
    result["approval_id"] = _identifier(value["approval_id"], "approval ID")
    result["asset_id"] = _identifier(value["asset_id"], "asset ID")
    result["version"] = _positive_int(value["version"], "asset version")
    if not isinstance(value["asset_sha256"], str) or not HASH_RE.fullmatch(value["asset_sha256"]):
        raise AssetRegistryError("Approval asset_sha256 must be a lowercase SHA-256 digest")
    result["approver_id"] = _identifier(value["approver_id"], "approver ID")
    result["approver_role"] = _identifier(value["approver_role"], "approver role")
    if value["type"] not in APPROVAL_TYPES or (expected_type and value["type"] != expected_type):
        raise AssetRegistryError(f"Approval type must be {expected_type or 'technical or author'}")
    if not isinstance(value["evidence"], str) or not value["evidence"].strip():
        raise AssetRegistryError("Approval evidence must be a nonempty string")
    if value["type"] == "author" and (value["approver_id"] != "luis-m-minier"
                                      or value["approver_role"] != "author"):
        raise AssetRegistryError("Author approval must be issued by luis-m-minier with the author role")
    _timestamp(value["at"])
    return result


class AssetRegistry:
    """Hash-chained event registry with atomic, single-writer persistence."""

    def __init__(self, repo=".", path="production/asset-registry.json"):
        self.repo = Path(repo).resolve()
        relative = _repo_path(path)
        self.path = (self.repo / relative).resolve()
        try:
            self.path.relative_to(self.repo)
        except ValueError as exc:
            raise AssetRegistryError("Registry path escapes repository") from exc
        self.data = json.loads(self.path.read_text()) if self.path.exists() else {
            "schema_version": 1, "events": []}
        self.verify()

    def _save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=".asset-registry-", suffix=".tmp", dir=self.path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(self.data, handle, indent=2, ensure_ascii=False)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def _append(self, action, payload, at=None):
        prior = self.data["events"][-1]["event_hash"] if self.data["events"] else None
        event = {"sequence": len(self.data["events"]) + 1, "at": _timestamp(at or _now()),
                 "action": action, "previous_event_hash": prior, "payload": payload}
        event["event_hash"] = _digest(event)
        self.data["events"].append(event)
        try:
            self.verify()
        except Exception:
            self.data["events"].pop()
            raise
        self._save()
        return event

    def _replay(self):
        assets, states, approvals, active_links = {}, {}, {}, {}
        prior = None
        for expected, event in enumerate(self.data.get("events", []), 1):
            if not isinstance(event, dict) or event.get("sequence") != expected:
                raise AssetRegistryError("Event sequence is not contiguous")
            supplied_hash = event.get("event_hash")
            content = {key: event[key] for key in event if key != "event_hash"}
            if event.get("previous_event_hash") != prior or not HASH_RE.fullmatch(supplied_hash or "") or _digest(content) != supplied_hash:
                raise AssetRegistryError(f"Event hash chain failed at sequence {expected}")
            _timestamp(event.get("at"))
            action, payload = event.get("action"), event.get("payload")
            if action == "register":
                record = self._validate_record(payload)
                ref = (record["asset_id"], record["version"])
                if ref in assets:
                    raise AssetRegistryError("Asset version was registered more than once")
                prior_versions = [v for (asset_id, v) in assets if asset_id == ref[0]]
                if record["version"] != (max(prior_versions, default=0) + 1):
                    raise AssetRegistryError("Asset versions must be contiguous and append-only")
                if record["supersedes"]:
                    target = (record["supersedes"]["asset_id"], record["supersedes"]["version"])
                    if target not in assets or target == ref:
                        raise AssetRegistryError("supersedes must reference an existing different asset version")
                for source in record["provenance"]["source_assets"]:
                    if (source["asset_id"], source["version"]) not in assets:
                        raise AssetRegistryError("Provenance source asset must already exist")
                assets[ref], states[ref] = record, record["initial_state"]
            elif action == "transition":
                ref = (_identifier(payload.get("asset_id")), _positive_int(payload.get("version"), "asset version"))
                if ref not in assets or payload.get("from") != states[ref] or payload.get("to") not in TRANSITIONS[states[ref]]:
                    raise AssetRegistryError("Invalid or out-of-order asset transition")
                approval = payload.get("approval")
                expected_type = "technical" if payload["to"] == "technical-approved" else "author" if payload["to"] == "author-approved" else None
                if expected_type:
                    approval = validate_approval(approval, expected_type)
                    if (approval["asset_id"], approval["version"]) != ref or approval["approval_id"] in approvals:
                        raise AssetRegistryError("Approval identity does not match or is duplicated")
                    if approval["asset_sha256"] != assets[ref]["sha256"]:
                        raise AssetRegistryError("Approval digest does not match the exact asset version")
                    if (expected_type == "technical"
                            and approval["approver_id"] == assets[ref]["provenance"]["creator"]):
                        raise AssetRegistryError("Technical approver must differ from the asset creator")
                    approvals[approval["approval_id"]] = approval
                elif approval is not None:
                    raise AssetRegistryError("Approval records only belong on approval transitions")
                if payload["to"] == "canonical" and states[ref] != "author-approved":
                    raise AssetRegistryError("Canonical assets require prior author approval")
                if (payload["to"] == "rejected"
                        and any((link["asset_id"], link["version"]) == ref
                                for link in active_links.values())):
                    raise AssetRegistryError("Unlink final uses before rejecting an asset")
                states[ref] = payload["to"]
            elif action == "link-final":
                use = _identifier(payload.get("use_id"), "final-use ID")
                ref = (_identifier(payload.get("asset_id")), _positive_int(payload.get("version"), "asset version"))
                shots = _strings(payload.get("shots"), "final-use shots", SHOT_RE)
                if ref not in assets or states[ref] != "canonical":
                    raise AssetRegistryError("Final-use links require a canonical, author-approved asset")
                if use in active_links or not shots:
                    raise AssetRegistryError("Final-use ID must be new and include at least one shot")
                if not set(shots) <= set(assets[ref]["shots"]):
                    raise AssetRegistryError("Final-use shots must be declared by the asset version")
                active_links[use] = {"asset_id": ref[0], "version": ref[1], "shots": shots}
            elif action == "unlink-final":
                use = _identifier(payload.get("use_id"), "final-use ID")
                if use not in active_links or not isinstance(payload.get("reason"), str) or not payload["reason"].strip():
                    raise AssetRegistryError("Unlink requires an active final-use ID and reason")
                del active_links[use]
            else:
                raise AssetRegistryError(f"Unknown registry event action: {action}")
            prior = supplied_hash
        return assets, states, approvals, active_links

    @staticmethod
    def _validate_record(value):
        required = {"asset_id", "version", "path", "sha256", "kind", "mode", "shots",
                    "provenance", "continuity", "initial_state", "supersedes"}
        if not isinstance(value, dict) or set(value) != required:
            raise AssetRegistryError(f"Asset record must contain exactly {sorted(required)}")
        record = dict(value)
        record["asset_id"] = _identifier(value["asset_id"], "asset ID")
        record["version"] = _positive_int(value["version"], "asset version")
        record["path"] = _repo_path(value["path"])
        if not isinstance(value["sha256"], str) or not HASH_RE.fullmatch(value["sha256"]):
            raise AssetRegistryError("sha256 must be a lowercase SHA-256 digest")
        record["kind"] = _identifier(value["kind"], "asset kind")
        if value["mode"] not in MODES:
            raise AssetRegistryError(f"mode must be one of {sorted(MODES)}")
        record["shots"] = _strings(value["shots"], "shots", SHOT_RE)
        record["provenance"] = _provenance(value["provenance"])
        record["continuity"] = _continuity(value["continuity"])
        if value["initial_state"] not in {"exploratory", "submitted"}:
            raise AssetRegistryError("initial_state must be exploratory or submitted")
        record["supersedes"] = None if value["supersedes"] is None else _reference(value["supersedes"], "supersedes")
        return record

    def verify(self, check_files=False):
        if not isinstance(self.data, dict) or self.data.get("schema_version") != 1 or set(self.data) != {"schema_version", "events"}:
            raise AssetRegistryError("Unsupported registry document")
        assets, states, approvals, links = self._replay()
        if check_files:
            for record in assets.values():
                raw_path = self.repo / record["path"]
                path = raw_path.resolve()
                try:
                    path.relative_to(self.repo)
                except ValueError as exc:
                    raise AssetRegistryError("Asset file escapes repository") from exc
                if (path != raw_path or raw_path.is_symlink() or not raw_path.is_file()
                        or hashlib.sha256(raw_path.read_bytes()).hexdigest() != record["sha256"]):
                    raise AssetRegistryError(f"Asset file missing or hash mismatch: {record['path']}")
        return {"assets": assets, "states": states, "approvals": approvals, "final_uses": links}

    def register(self, *, asset_id, path, kind, mode, shots, provenance, continuity,
                 initial_state="exploratory", supersedes=None, at=None):
        relative = _repo_path(path)
        raw_path = self.repo / relative
        file_path = raw_path.resolve()
        try:
            file_path.relative_to(self.repo)
        except ValueError as exc:
            raise AssetRegistryError("Asset file escapes repository") from exc
        if file_path != raw_path or raw_path.is_symlink() or not raw_path.is_file():
            raise AssetRegistryError("Registered asset must be an existing regular repository file, not a symlink")
        state = self.verify()
        asset_id = _identifier(asset_id, "asset ID")
        versions = [version for (current_id, version) in state["assets"] if current_id == asset_id]
        record = {"asset_id": asset_id, "version": max(versions, default=0) + 1,
                  "path": relative, "sha256": hashlib.sha256(file_path.read_bytes()).hexdigest(),
                  "kind": kind, "mode": mode, "shots": shots, "provenance": provenance,
                  "continuity": continuity, "initial_state": initial_state, "supersedes": supersedes}
        record = self._validate_record(record)
        self._append("register", record, at)
        return record

    def _assert_file(self, record):
        """Require the registered bytes to exist unchanged at a promotion gate."""
        raw_path = self.repo / record["path"]
        path = raw_path.resolve()
        try:
            path.relative_to(self.repo)
        except ValueError as exc:
            raise AssetRegistryError("Asset file escapes repository") from exc
        if path != raw_path or raw_path.is_symlink() or not raw_path.is_file():
            raise AssetRegistryError(f"Asset file missing or unsafe: {record['path']}")
        if hashlib.sha256(path.read_bytes()).hexdigest() != record["sha256"]:
            raise AssetRegistryError(f"Asset file hash mismatch: {record['path']}")

    def transition(self, asset_id, version, target, approval=None, at=None):
        ref = (_identifier(asset_id, "asset ID"), _positive_int(version, "asset version"))
        state = self.verify()
        if ref not in state["assets"]:
            raise AssetRegistryError("Unknown asset version")
        current = state["states"][ref]
        if target not in TRANSITIONS[current]:
            raise AssetRegistryError(f"Cannot transition {current} to {target}")
        if target in {"technical-approved", "author-approved", "canonical"}:
            self._assert_file(state["assets"][ref])
        payload = {"asset_id": ref[0], "version": ref[1], "from": current,
                   "to": target, "approval": approval}
        self._append("transition", payload, at)
        return target

    def link_final(self, use_id, asset_id, version, shots, at=None):
        state = self.verify()
        ref = (_identifier(asset_id, "asset ID"), _positive_int(version, "asset version"))
        if ref not in state["assets"]:
            raise AssetRegistryError("Unknown asset version")
        self._assert_file(state["assets"][ref])
        payload = {"use_id": _identifier(use_id, "final-use ID"),
                   "asset_id": ref[0], "version": ref[1], "shots": shots}
        self._append("link-final", payload, at)
        return payload

    def unlink_final(self, use_id, reason, at=None):
        payload = {"use_id": _identifier(use_id, "final-use ID"), "reason": reason}
        self._append("unlink-final", payload, at)
        return payload

    def summary(self):
        state = self.verify()
        assets = []
        for ref, record in sorted(state["assets"].items()):
            assets.append({**record, "state": state["states"][ref]})
        uses = [{"use_id": use, **link}
                for use, link in sorted(state["final_uses"].items())]
        return {"assets": assets, "final_uses": uses, "event_count": len(self.data["events"])}


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".")
    parser.add_argument("--registry", default="production/asset-registry.json")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init")
    register = sub.add_parser("register")
    register.add_argument("record", help="JSON containing registration fields except version/hash")
    transition = sub.add_parser("transition")
    transition.add_argument("asset_id"); transition.add_argument("version", type=int)
    transition.add_argument("target", choices=sorted(STATES - {"exploratory"}))
    transition.add_argument("--approval", help="Technical/author approval JSON")
    link = sub.add_parser("link-final")
    link.add_argument("use_id"); link.add_argument("asset_id"); link.add_argument("version", type=int)
    link.add_argument("shots", nargs="+")
    unlink = sub.add_parser("unlink-final")
    unlink.add_argument("use_id"); unlink.add_argument("reason")
    verify = sub.add_parser("verify"); verify.add_argument("--check-files", action="store_true")
    sub.add_parser("show")
    args = parser.parse_args(argv)
    registry = AssetRegistry(args.repo, args.registry)
    if args.command == "init":
        registry._save(); output = registry.summary()
    elif args.command == "register":
        output = registry.register(**_load(args.record))
    elif args.command == "transition":
        output = {"state": registry.transition(args.asset_id, args.version, args.target,
                                                _load(args.approval) if args.approval else None)}
    elif args.command == "link-final":
        output = registry.link_final(args.use_id, args.asset_id, args.version, args.shots)
    elif args.command == "unlink-final":
        output = registry.unlink_final(args.use_id, args.reason)
    elif args.command == "verify":
        registry.verify(args.check_files); output = {"valid": True, "check_files": args.check_files}
    else:
        output = registry.summary()
    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
