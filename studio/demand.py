"""On-demand, one-image Codex turns with frozen references and reviewed handoff.

No episode-wide generation queue, automatic retries, or creative approvals.
The coordinator is the sole ledger/asset writer. A fresh worker and reviewer
handle each explicitly requested shot revision. Existing artwork is reused.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
import fcntl
import json
from pathlib import Path
import re
import shutil

from PIL import Image

from production.asset_registry import AssetRegistry, _continuity
from production.runtime import Ledger
from studio.paths import ROOT, load_json, sha256, write_json
from studio.runner import CodexRunner, RunnerError

EPISODE = "projects/cemi_episode_01/data/episode.json"
PROJECT = "projects/cemi_episode_01"
BASE = "production/image-demand"
CHECKS = ("identity", "costume", "props_and_contact", "composition", "lighting",
          "line_and_color", "neighbor_continuity", "script_fidelity")
DOCS = ("production/art_direction.json", "research/earlier_cemi_pipeline/docs/ART_DIRECTION.md",
        "research/earlier_cemi_pipeline/data/character_bible.txt")
STYLE = "research/supplied_references/approved_style_reference.png"


class DemandError(RuntimeError):
    pass


def safe(root, relative):
    root = Path(root).resolve()
    p = Path(relative)
    if p.is_absolute() or ".." in p.parts:
        raise DemandError("Use repository-relative paths without traversal")
    raw = root / p
    if raw.resolve() != raw or not raw.is_relative_to(root):
        raise DemandError("Symlinked or escaping paths are not allowed")
    return raw


@contextmanager
def coordinator(root):
    directory = safe(root, BASE)
    directory.mkdir(parents=True, exist_ok=True)
    with safe(root, f"{BASE}/coordinator.lock").open("a") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise DemandError("Another image coordinator is active") from exc
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def key(shot, revision):
    if not re.fullmatch(r"S\d{2}-\d{2}[A-Z]?", shot):
        raise DemandError("Use a canonical shot ID, e.g. S01-01")
    if type(revision) is not int or revision < 1:
        raise DemandError("Revision must be a positive integer")
    return f"image-{shot.lower()}-v{revision}"


def registry_assets(root):
    registry = AssetRegistry(root)
    registry.verify(check_files=True)
    assets = registry.summary()["assets"]
    for asset in assets:
        parts = Path(asset["path"]).parts
        if len(parts) > 3 and parts[:2] == ("production", "runs"):
            path = safe(root, f"{BASE}/{parts[2]}/packet.json")
            if path.exists():
                task = Ledger(root, parts[2]).data["tasks"].get("image", {})
                asset["demand_state"] = task.get("state")
    return assets


def shot_record(root, shot):
    shots = load_json(safe(root, EPISODE))["shots"]
    for index, record in enumerate(shots):
        if record["id"] == shot:
            return shots, index, record
    raise DemandError(f"Unknown episode shot {shot}")


def eligible_image(asset):
    return (asset["state"] != "rejected" and asset.get("demand_state") not in {"rejected", "author-rejected"} and
            Path(asset["path"]).suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"} and
            asset["kind"] in {"story-frame", "keyframe", "layout"})


def rejected(asset):
    return asset.get("state") == "rejected" or asset.get("demand_state") in {"rejected", "author-rejected"}


def canonical_for(root, shot):
    return [a for a in registry_assets(root) if a["state"] == "canonical"
            and shot in a["shots"] and eligible_image(a)]


def verify_packet(root, packet):
    for record in packet["references"] + packet["documents"]:
        for name in ("path", "snapshot"):
            p = safe(root, record[name])
            if not p.is_file() or sha256(p) != record["sha256"]:
                raise DemandError(f"Reference changed: {record[name]}; prepare a new revision")
    # Approval state can change even when image bytes do not.
    states = {(a["asset_id"], a["version"]): a["state"] for a in registry_assets(root)}
    for record in packet["references"]:
        if record.get("asset"):
            ref = record["asset"]
            current = states.get((ref["asset_id"], ref["version"]))
            if current == "rejected" or (record["state"] == "canonical" and current != "canonical"):
                raise DemandError("Reference approval changed; prepare a new revision")
    records = {a["path"]: a for a in registry_assets(root)}
    if any(rejected(records.get(r["path"], {})) for r in packet["references"]):
        raise DemandError("Reference was rejected; prepare a new revision")


def prepare(root, shot, revision=1, refs=(), candidate=None, correction=None):
    root = Path(root).resolve()
    run = key(shot, revision)
    shots, index, record = shot_record(root, shot)
    if shot.startswith("S00-"):
        return {"shot": shot, "route": "local-editorial", "generation_needed": False,
                "reason": "Opening sigil/title typography already have local engine specifications."}
    canonical = canonical_for(root, shot)
    if canonical:
        return {"shot": shot, "route": "reuse-canonical", "asset": canonical[-1]}
    directory = safe(root, f"{BASE}/{run}")
    packet_path = directory / "packet.json"
    if (directory / "superseded.json").exists():
        raise DemandError("This demand was superseded; use its recorded replacement revision")
    if packet_path.exists():
        packet = load_json(packet_path)
        if (list(refs) != packet["requested_refs"] or candidate != packet["requested_candidate"]
                or correction != packet.get("correction")):
            raise DemandError("Demand exists with different inputs; use a new revision")
        verify_packet(root, packet)
        return packet
    if directory.exists():
        raise DemandError("Incomplete preparation exists; inspect it before creating a new revision")
    if safe(root, f"production/runs/{run}/ledger.json").exists():
        raise DemandError("Run name already exists without a demand packet")
    superseded = []
    for prior_path in safe(root, BASE).glob("*/packet.json"):
        prior = load_json(prior_path)
        if prior["shot"]["id"] != shot:
            continue
        if (prior_path.parent / "superseded.json").exists():
            continue
        previous = Ledger(root, prior["run"])
        state = previous.data["tasks"].get("image", {}).get("state")
        # A new explicit correction may replace a stale never-launched packet.
        # Interrupted/running work is different: inspect its possible output first.
        if state == "pending" and not previous.data["paused"] and correction:
            runner_state = previous.run_dir / "runner_state.json"
            inflight = load_json(runner_state).get("inflight") if runner_state.exists() else None
            outputs = previous.run_dir / "tasks/image"
            if not inflight and not outputs.exists():
                try:
                    verify_packet(root, prior)
                except DemandError:
                    superseded.append(prior_path.parent)
                    continue
        if previous.data["paused"] or state not in {"blocked", "rejected", "author-rejected"}:
            raise DemandError(f"Existing demand {prior['run']} is {state}; inspect/collect it instead of generating twice")
        if not (candidate or correction):
            raise DemandError("A revision needs an explicit --correction or revised --candidate")
    assets = registry_assets(root)
    by_path = {}
    for a in assets:
        by_path[a["path"]] = a
    # Prefer a registered saved candidate to generating the same missing image again.
    saved = [a["path"] for a in assets if shot in a["shots"] and eligible_image(a)]
    saved += [f"{PROJECT}/{p}" for p in record.get("keyframes", [])]
    selected = candidate or next((p for p in saved if safe(root, p).is_file()
                                 and not rejected(by_path.get(p, {}))), None)
    reference_paths = [(STYLE, "style")]
    if selected:
        reference_paths.append((selected, "existing-candidate"))
    # Same-sequence anchors only: never carry a river costume into another era.
    sequence = shot.split("-")[0]
    neighbors = [{"id": shots[i]["id"], "script": shots[i]["script"]}
                 for i in (index - 1, index + 1) if 0 <= i < len(shots)
                 and shots[i]["id"].split("-")[0] == sequence]
    for indices in (range(index - 1, -1, -1), range(index + 1, len(shots))):
        for i in indices:
            neighbor = shots[i]
            if neighbor["id"].split("-")[0] != sequence:
                break
            anchors = [a["path"] for a in assets if a["state"] == "canonical"
                       and neighbor["id"] in a["shots"] and eligible_image(a)]
            anchors += [f"{PROJECT}/{p}" for p in neighbor.get("keyframes", [])]
            anchors = [p for p in anchors if safe(root, p).is_file()
                       and not rejected(by_path.get(p, {}))]
            if anchors:
                reference_paths.append((anchors[0], f"continuity:{neighbor['id']}"))
                break
    reference_paths.extend((p, "explicit-identity-or-layout") for p in refs)
    # These are historical proposals, explicitly subordinate to current script/canon.
    # Attach named cast sheets for inspection; never silently approve their costumes.
    cast_dir = "research/archive_imports/river_2026_10_11/Cemi-River-Scene/01-Characters"
    cast = {"Amaia": "01-Amaia.png", "Dairon": "03-Dairon.png",
            "Yara": "04-Yara-Corrected.png", "Beheto": "05-Beheto.png"}
    for name, filename in cast.items():
        path = f"{cast_dir}/{filename}"
        if re.search(rf"\b{name}\b", record["script"], re.IGNORECASE) and safe(root, path).is_file():
            reference_paths.append((path, f"historical-identity-proposal:{name}"))
    # Preserve exact shot/script and historical identity sources for worker inspection.
    paths = [(p, purpose, True) for p, purpose in reference_paths]
    paths += [(p, "contract", False) for p in (*DOCS, EPISODE)]
    frozen, documents, seen = [], [], set()
    for path, purpose, is_image in paths:
        if path in seen:
            continue
        seen.add(path)
        source = safe(root, path)
        if not source.is_file():
            raise DemandError(f"Missing reference {path}")
        asset = by_path.get(path)
        if asset and rejected(asset):
            raise DemandError(f"Rejected reference {path}")
        if is_image:
            with Image.open(source) as img:
                img.verify()
        item = {"path": path, "purpose": purpose, "sha256": sha256(source),
                "state": asset["state"] if asset else "baseline-unreviewed",
                "asset": {"asset_id": asset["asset_id"], "version": asset["version"]} if asset else None,
                "snapshot": f"{BASE}/{run}/references/{len(seen):02d}{source.suffix}"}
        (frozen if is_image else documents).append(item)
    packet = {"version": 1, "run": run, "shot": record, "neighbors": neighbors,
              "requested_refs": list(refs), "requested_candidate": candidate,
              "correction": correction,
              "route": "review-existing" if selected and not correction else "generate-one",
              "candidate_source": selected, "references": frozen, "documents": documents,
              "backend": "host-image-tool", "max_images": 0 if selected and not correction else 1,
              "checks": list(CHECKS), "truth": "References guide consistency; review must establish it."}
    directory.mkdir(parents=True)
    for item in frozen + documents:
        target = safe(root, item["snapshot"])
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(safe(root, item["path"]), target)
    write_json(packet_path, packet)
    out = f"production/runs/{run}/tasks/image"
    ledger = Ledger(root, run)
    ledger.initialize()
    ledger.add({"id": "image", "role": "layout-artist", "shots": [shot],
                "objective": f"One on-demand story frame for {shot}. Read {BASE}/{run}/packet.json. "
                             "Follow docs/IMAGE_DEMAND.md and the packet route/correction. "
                             "For review-existing, reuse; for generate-one, make at most ONE image with the host's "
                             "built-in image tool. Never call paid APIs or batch other shots. "
                             "Inspect all images. Write candidate.png and continuity.json in output_dir. "
                             "If likeness sources or the image tool are unavailable, return blocked.",
                "inputs": [f"{BASE}/{run}/packet.json", "docs/IMAGE_DEMAND.md"] +
                          [x["snapshot"] for x in frozen + documents],
                "output_dir": out, "depends_on": [], "art_direction_mode": "STORY_FRAME",
                "require_host_bindings": True, "requires_author_approval": True,
                "author_approver": "luis-m-minier", "budget": {"max_cost_usd": 0},
                "acceptance_criteria": ["Exactly one 16:9 candidate PNG, no text-only substitute",
                    "Every reference is visually inspected and its digest recorded in continuity.json",
                    "Specific evidence for " + ", ".join(CHECKS),
                    "Original cast, ages, costumes, handedness, props, era and lighting are preserved",
                    "New artwork remains exploratory; no creative approval is fabricated"]})
    for prior_dir in superseded:
        write_json(prior_dir / "superseded.json", {"replacement": run,
                   "reason": "Explicit correction replaces changed references before any worker launch"})
    return packet


class ImageTurnRunner(CodexRunner):
    image_demand_runner = True
    def __init__(self, packet, *, root=ROOT, dry_run=False):
        policy = deepcopy(load_json(Path(root) / "production/policy.json"))
        policy.setdefault("revisions", {})["auto_create_on_reject"] = False
        super().__init__(packet["run"], root=root, policy=policy, dry_run=dry_run, parallel=1)
        self.packet = packet

    def _codex(self, prompt, schema, out_dir, label, network=False, images=()):
        verify_packet(self.root, self.packet)
        images = [safe(self.root, x["snapshot"]) for x in self.packet["references"]]
        if label == "reviewer":
            images.append(self.root / self.ledger._task("image")["output_dir"] / "candidate.png")
        return super()._codex(prompt, schema, out_dir, label, network=False, images=images)

    def submit(self, task_id, thread, final):
        verify_packet(self.root, self.packet)
        if final is None:
            final = load_json(safe(self.root, f"{self.ledger._task(task_id)['output_dir']}/result.json"))
        if isinstance(final, dict) and final.get("status") == "submitted":
            out = self.ledger._task(task_id)["output_dir"]
            candidate = safe(self.root, f"{out}/candidate.png")
            report = load_json(safe(self.root, f"{out}/continuity.json"))
            with Image.open(candidate) as img:
                if img.format != "PNG" or img.width * 9 != img.height * 16:
                    raise DemandError("Candidate must be a 16:9 PNG")
                img.verify()
            source = self.packet.get("candidate_source")
            if self.packet["route"] == "review-existing" and source:
                if Path(source).suffix.lower() == ".png" and sha256(candidate) != sha256(safe(self.root, source)):
                    raise DemandError("Existing PNG candidate must be reused byte-for-byte")
            expected = {r["snapshot"]: r["sha256"] for r in self.packet["references"]}
            if report.get("references") != expected or report.get("candidate_sha256") != sha256(candidate):
                raise DemandError("Continuity report does not bind the inspected images")
            _continuity(report.get("continuity"))
            if any(not isinstance(report.get("checks", {}).get(k), str) or
                   not report["checks"][k].strip() for k in CHECKS):
                raise DemandError("Continuity evidence is incomplete")
            for path in (f"{out}/candidate.png", f"{out}/continuity.json"):
                if path not in final.get("artifacts", []):
                    raise DemandError("Candidate and continuity report must both be submitted")
            write_json(safe(self.root, f"{BASE}/{self.run}/submission.json"), {
                "candidate_sha256": sha256(candidate),
                "report_sha256": sha256(safe(self.root, f"{out}/continuity.json")),
                "creator": thread})
        return super().submit(task_id, thread, final)


def collect(root, packet):
    """Register only bytes covered by a completed independent technical review."""
    verify_packet(root, packet)
    ledger = Ledger(root, packet["run"])
    task = ledger._task("image")
    if task["state"] not in {"approved", "author-approved"}:
        return {"run": packet["run"], "state": task["state"], "paused": ledger.data["paused"]}
    candidate_rel = f"{task['output_dir']}/candidate.png"
    report = load_json(safe(root, f"{task['output_dir']}/continuity.json"))
    submission = load_json(safe(root, f"{BASE}/{packet['run']}/submission.json"))
    digest = sha256(safe(root, candidate_rel))
    if (digest != report["candidate_sha256"] or digest != submission["candidate_sha256"] or
            sha256(safe(root, f"{task['output_dir']}/continuity.json")) != submission["report_sha256"]):
        raise DemandError("Candidate changed after submission")
    review = load_json(safe(root, f"production/runs/{packet['run']}/reviews/image/review.json"))
    creator = task["result"]["host_agent_id"]
    if (review["decision"] != "approve" or review["host_agent_id"] == creator or
            creator != submission["creator"]):
        raise DemandError("Independent approval required")
    registry = AssetRegistry(root)
    asset_id = f"{packet['run']}.frame"
    assets = [a for a in registry.summary()["assets"] if a["asset_id"] == asset_id]
    if assets:
        asset = assets[-1]
        if asset["sha256"] != digest:
            raise DemandError("Registered output changed")
    else:
        asset = registry.register(asset_id=asset_id, path=candidate_rel, kind="story-frame",
            mode="work-in-progress", shots=[packet["shot"]["id"]],
            provenance={"origin": "On-demand isolated image turn", "creator": creator,
                "license": "Project candidate; source rights and author approval retained",
                "source_assets": [r["asset"] for r in packet["references"] if r["asset"]],
                "notes": f"Reference digests and continuity evidence: {task['output_dir']}/continuity.json"},
            continuity=report["continuity"])
        asset = {**asset, "state": "exploratory"}
    if asset["state"] == "exploratory":
        registry.transition(asset_id, asset["version"], "submitted")
        asset["state"] = "submitted"
    if asset["state"] == "submitted":
        registry.transition(asset_id, asset["version"], "technical-approved", approval={
            "approval_id": f"{packet['run']}.technical", "type": "technical", "asset_id": asset_id,
            "version": asset["version"], "asset_sha256": digest,
            "approver_id": review["host_agent_id"], "approver_role": review["reviewer_role"],
            "evidence": review["evidence"], "at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")})
    current = next(a for a in registry.summary()["assets"] if a["asset_id"] == asset_id
                   and a["version"] == asset["version"])
    return {"run": packet["run"], "asset": current,
            "next": "Luis reviews this exact file through the existing asset approval workflow."}


def work(root, shot, revision=1, dry_run=False):
    if safe(root, f"{BASE}/{key(shot, revision)}/superseded.json").exists():
        raise DemandError("This demand was superseded; use its recorded replacement revision")
    packet = load_json(safe(root, f"{BASE}/{key(shot, revision)}/packet.json"))
    verify_packet(root, packet)
    runner = ImageTurnRunner(packet, root=root, dry_run=dry_run)
    try:
        result = runner.loop(max_tasks=1)
    except BaseException as exc:
        # Includes Ctrl+C and unexpected validation failures. Never silently re-launch.
        if not dry_run and not runner.ledger.data.get("paused"):
            runner.ledger.pause(f"Image turn interrupted: {type(exc).__name__}: {exc}")
        raise
    return result if dry_run else collect(root, packet)


def ensure(root, shot, revision=1, refs=(), candidate=None, correction=None, dry_run=False):
    """The production coordinator calls this only when it reaches this shot."""
    packet = prepare(root, shot, revision, refs, candidate, correction)
    if packet["route"] in {"local-editorial", "reuse-canonical"}:
        return packet
    return work(root, shot, revision, dry_run)


def video_handoff(root, shot, out, frames=None, offset=0):
    assets = canonical_for(root, shot)
    if not assets:
        raise DemandError("A canonical, digest-verified image for this shot is required before HF video handoff")
    if len(assets) != 1:
        raise DemandError("Multiple canonical images for this shot; choose the intended composition before video")
    asset = assets[-1]
    from studio import video
    # Only prepares a bounded existing HF job; its submission is explicit and at most once.
    result = video.prepare(shot, safe(root, asset["path"]), safe(root, out), frames=frames, offset=offset)
    write_json(safe(root, f"{out}/image-source.json"), {"asset_id": asset["asset_id"],
               "version": asset["version"], "sha256": asset["sha256"], "shot": shot})
    return result


def verify_video_source(root, directory):
    """Recheck the demand asset immediately before any external submission."""
    binding = load_json(Path(directory) / "image-source.json")
    matches = [a for a in canonical_for(root, binding["shot"])
               if a["asset_id"] == binding["asset_id"] and a["version"] == binding["version"]
               and a["sha256"] == binding["sha256"]]
    if len(matches) != 1:
        raise DemandError("Video source is no longer canonical or its reviewed bytes changed")
    job = load_json(Path(directory) / "job.json")
    ref = job["references"]["first"]
    if (job["shot"] != binding["shot"] or ref["original_sha256"] != binding["sha256"] or
            Path(ref["original"]).resolve() != safe(root, matches[0]["path"])):
        raise DemandError("Video job does not match its canonical image binding")


def status(root):
    assets = registry_assets(root)
    shots = load_json(safe(root, EPISODE))["shots"]
    rows = []
    for s in shots:
        saved = [a for a in assets if s["id"] in a["shots"] and eligible_image(a)]
        baseline = [p for p in s.get("keyframes", []) if safe(root, f"{PROJECT}/{p}").is_file()]
        route = ("local-editorial" if s["id"].startswith("S00-") else
                 "canonical" if any(a["state"] == "canonical" for a in saved) else
                 "review-existing" if saved or baseline else "needs-image")
        rows.append({"shot": s["id"], "route": route})
    demands = []
    for p in sorted(safe(root, BASE).glob("*/packet.json")):
        packet = load_json(p)
        ledger = Ledger(root, packet["run"])
        demands.append({"run": packet["run"], "shot": packet["shot"]["id"],
                        "state": "superseded" if (p.parent / "superseded.json").exists() else
                        ledger.data["tasks"].get("image", {}).get("state", "incomplete"),
                        "paused": ledger.data["paused"]})
    return {"counts": {route: sum(r["route"] == route for r in rows) for route in
            ("local-editorial", "canonical", "review-existing", "needs-image")},
            "demands": demands, "shots": rows, "automatic_batch": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status")
    for command in ("ensure", "need", "work", "collect"):
        p = sub.add_parser(command)
        p.add_argument("shot")
        p.add_argument("--revision", type=int, default=1)
        if command in {"ensure", "need"}:
            p.add_argument("--ref", action="append", default=[])
            p.add_argument("--candidate")
            p.add_argument("--correction", help="specific repair objective for a new revision")
        if command in {"ensure", "work"}:
            p.add_argument("--dry-run", action="store_true")
    p = sub.add_parser("video")
    p.add_argument("shot"); p.add_argument("--out", required=True)
    p.add_argument("--frames", type=int); p.add_argument("--offset", type=int, default=0)
    args = parser.parse_args(argv)
    try:
        with coordinator(ROOT):
            if args.command == "status":
                result = status(ROOT)
            elif args.command == "ensure":
                result = ensure(ROOT, args.shot, args.revision, args.ref, args.candidate,
                                args.correction, args.dry_run)
            elif args.command == "need":
                result = prepare(ROOT, args.shot, args.revision, args.ref, args.candidate, args.correction)
            elif args.command == "work":
                result = work(ROOT, args.shot, args.revision, args.dry_run)
            elif args.command == "collect":
                packet = load_json(safe(ROOT, f"{BASE}/{key(args.shot, args.revision)}/packet.json"))
                result = collect(ROOT, packet)
            else:
                result = video_handoff(ROOT, args.shot, args.out, args.frames, args.offset)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except (DemandError, RunnerError, ValueError, OSError) as exc:
        raise SystemExit(f"demand stopped: {exc}") from exc


if __name__ == "__main__":
    main()
