"""Generate every department skill from production/roles.json.

roles.json is the single source of truth for role duties, reviewers, rules,
handoffs, deliverables, tools and generation rights. Shared worker rules live
once in production/WORKER_CONTRACT.md. Run after editing roles.json:

    python production/build_skills.py          # write .agents/skills/anime-*/
    python production/build_skills.py --check  # fail if files are out of date
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = "production/WORKER_CONTRACT.md"

RELEASE_QA = """## Release QA result

For a release task whose ID ends in `-qa`, also return `pipeline_id` (the task id without `-qa`), `qa_report` (`{"path": ..., "sha256": ...}` for a report also listed in `artifacts`) and `release_asset_sha256s` (the exact canonical final picture/audio digests you reviewed). Omit these fields on any other review. Never invent a host ID, digest or approval.
"""


def _yaml_str(text: str) -> str:
    return json.dumps(text, ensure_ascii=False)


def render_skill(role_id: str, role: dict) -> str:
    name = Path(role["skill"]).parent.name
    lines = [
        "---",
        f"name: {name}",
        f"description: {_yaml_str(role['description'])}",
        "---",
        "",
        f"# {role['title']}",
        "",
        f"Dispatched worker for the `{role_id}` department. Before anything else, read and follow "
        f"`{CONTRACT}`: envelope, required reading, scope, spending, interruption, canon, evidence and the result JSON.",
    ]
    if role.get("visual"):
        lines += ["", "This is a visual role. Read `production/art_direction.json`, use the task's exact "
                  "`art_direction_mode`, and satisfy every criterion for that mode."]
    for extra in role.get("extra_skills", []):
        extra_name = Path(extra).parent.name
        lines += ["", f"When the task uses Blender or other 3D elements, also read `{extra}` (`${extra_name}`): "
                  "its render contract and quality gates apply to your deliverable."]
    lines += ["", "## Duties", "", role["duties"]]
    if role.get("rules"):
        lines += ["", "## Role rules", ""] + [f"- {rule}" for rule in role["rules"]]
    lines += ["", "## Inputs and handoff", "", role["handoff"],
              "", f"Submit to a separate `{role['reviewer']}` reviewer through the coordinator. "
              "Never self-approve or edit another agent's deliverable."]
    lines += ["", "## Deliverables", "", role["deliverables"]]
    gen = role.get("generate") or []
    tools = role.get("tools") or []
    if tools or gen:
        lines += ["", "## Tools", ""]
        lines += [f"- `{tool}`" for tool in tools]
        if gen:
            lines += ["", f"Generation rights: {', '.join(gen)}. Only through `python -m studio generate`, "
                      "only when the contract's four spending conditions hold."]
        else:
            lines += ["", "No generation rights. Do not call paid services."]
    if role_id == "quality-review":
        lines += ["", RELEASE_QA.rstrip()]
    return "\n".join(lines) + "\n"


def render_yaml(role_id: str, role: dict) -> str:
    name = Path(role["skill"]).parent.name
    short = role["duties"].split(". ")[0].rstrip(".")
    if len(short) > 90:
        short = short[:87].rstrip() + "..."
    return (
        "interface:\n"
        f"  display_name: {_yaml_str(role['title'])}\n"
        f"  short_description: {_yaml_str(short)}\n"
        f"  default_prompt: {_yaml_str(f'Use ${name} for the dispatched ledger task.')}\n"
        "policy:\n"
        "  allow_implicit_invocation: false\n"
    )


def outputs(root: Path = ROOT) -> dict[Path, str]:
    roles = json.loads((root / "production/roles.json").read_text(encoding="utf-8"))
    files: dict[Path, str] = {}
    for role_id, role in roles.items():
        skill = root / role["skill"]
        files[skill] = render_skill(role_id, role)
        files[skill.parent / "agents/openai.yaml"] = render_yaml(role_id, role)
    return files


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="fail if generated skills are stale")
    parser.add_argument("--root", default=str(ROOT))
    args = parser.parse_args(argv)
    stale = []
    for path, text in outputs(Path(args.root)).items():
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current != text:
            stale.append(path)
            if not args.check:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")
    if args.check and stale:
        print("stale skills (run python production/build_skills.py):")
        for path in stale:
            print(f"  {path.relative_to(args.root)}")
        return 1
    print(f"{'checked' if args.check else 'wrote'} {len(outputs(Path(args.root)))} files; {len(stale)} changed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
