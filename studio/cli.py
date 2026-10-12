"""``python -m studio`` - one entry point for Codex and for Luis.

Production loop (Codex):  plan -> run -> (Luis) approve -> run ...
Picture:                  animatic, render, queue, assemble, qa
Drawings:                 layers split|matte|register, motion compile|check
Sound:                    sound lines|mouth|mix
Paid (opt-in):            generate image|voice
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from studio.paths import EPISODE, PROJECT, ROOT, load_json, rel, write_json


def _print(data):
    print(data if isinstance(data, str) else json.dumps(data, indent=2, ensure_ascii=False))


def cmd_status(args):
    from studio import policy as pol
    episode = load_json(EPISODE)
    shots = episode["shots"]
    shot_dir = PROJECT / "data" / "shots"
    specs = [load_json(p) for p in sorted(shot_dir.glob("*.json"))]
    runs = {}
    for ledger in sorted((ROOT / "production" / "runs").glob("*/ledger.json")):
        data = load_json(ledger)
        states = {}
        for task in data["tasks"].values():
            states[task["state"]] = states.get(task["state"], 0) + 1
        runs[data["run"]] = {"paused": data.get("paused"), "pause_reason": data.get("pause_reason"), "tasks": states}
    gen = pol.load().get("generation", {})
    _print({
        "episode": {"shots": len(shots), "frames": sum(s["frames"] for s in shots),
                    "with_keyframes": sum(bool(s["keyframes"]) for s in shots),
                    "approved_animation": sum(s["animation_status"] == "approved" for s in shots),
                    "approved_audio": sum(s["voice_status"] in ("approved", "no_dialogue") for s in shots)},
        "shot_specs": {"total": len(specs), "by_stage": _count(s.get("stage", "template") for s in specs)},
        "registry": "present" if (ROOT / "production" / "asset-registry.json").exists() else "not initialized",
        "runs": runs,
        "generation": {"enabled": bool(gen.get("enabled")), "spent_usd": pol.spent(),
                       "cap_usd": gen.get("max_total_usd", 0)},
        "truth": "Counts describe files and ledger states, not animation quality.",
    })


def _count(items):
    out = {}
    for item in items:
        out[item] = out.get(item, 0) + 1
    return out


def cmd_plan(args):
    sys.path.insert(0, str(ROOT))
    from production.pipeline import build_pipeline, ledger_task
    from production.runtime import Ledger
    spec = load_json(ROOT / args.spec)
    pipeline = build_pipeline(spec, load_json(ROOT / "production/pipeline_templates/complete_shot.json"),
                              load_json(ROOT / "production/roles.json"), ROOT)
    run = args.run or pipeline["run"]
    if run != pipeline["run"]:
        raise SystemExit(f"spec declares run {pipeline['run']}; pass --run {pipeline['run']} or edit the spec")
    ledger = Ledger(ROOT, run)
    ledger.initialize()
    added = []
    for task in pipeline["tasks"]:
        if task["id"] in ledger.data["tasks"]:
            continue
        ledger.add(ledger_task(task))
        added.append(task["id"])
    write_json(ledger.run_dir / "pipeline.json", pipeline)
    _print({"run": run, "added": len(added), "ready": ledger.ready(), "status": pipeline["status"],
            "timing_conflicts": [c["id"] for c in pipeline.get("timing_conflicts", [])]})


def cmd_run(args):
    from studio.runner import CodexRunner, RunnerError
    runner = CodexRunner(args.run, dry_run=args.dry_run, parallel=args.parallel)
    try:
        _print(runner.loop(args.max_tasks))
    except RunnerError as exc:
        raise SystemExit(f"stopped: {exc}")


def cmd_next(args):
    sys.path.insert(0, str(ROOT))
    from production.runtime import Ledger
    ledger = Ledger(ROOT, args.run)
    _print([{"id": t, "role": ledger._task(t)["role"], "objective": ledger._task(t)["objective"][:200]}
            for t in ledger.ready()])


def cmd_approve(args):
    sys.path.insert(0, str(ROOT))
    from production.runtime import Ledger
    if not args.i_am_luis:
        raise SystemExit("Creative approval belongs to Luis M. Minier. Agents must never run this. "
                         "Luis: add --i-am-luis.")
    ledger = Ledger(ROOT, args.run)
    _print(ledger.author_review(args.task, "luis-m-minier", args.decision, args.evidence))


def cmd_render(args):
    from studio.render import export_shot
    spec = load_json(args.spec)
    base = Path(args.base) if args.base else PROJECT
    _print(export_shot(spec, Path(args.out), draft=args.draft, base=base, quality=args.quality,
                       burn=args.burn))


def cmd_animatic(args):
    from studio.animatic import build_all
    from studio.render import RenderQueue, assemble
    shots = set(args.shots.split(",")) if args.shots else None
    jobs = build_all(write=True, shots=shots)
    if args.build_only:
        _print({"specs": len(jobs), "dir": rel(PROJECT / "data" / "shots")})
        return
    out = Path(args.out)
    queue = RenderQueue(out / "shots", mode="master" if args.master else "review", quality="draft",
                        draft=True, burn=True, label="ANIMATIC", workers=args.workers)
    summary = queue.run([(sid, _scaled(spec, args.scale), start) for sid, spec, start in jobs])
    _print(summary)
    if summary["failed"]:
        raise SystemExit("some shots failed; nothing assembled")
    if not shots:
        files = [queue.output_for(sid) for sid, _, _ in jobs]
        total = sum(spec["frames"] for _, spec, _ in jobs)
        _print(assemble(files, out / "animatic", expected_frames=total))


def _scaled(spec, scale):
    """Animatic renders at a fraction of size; the spec stays in episode pixels."""
    if scale >= 1:
        return spec
    spec = dict(spec)
    spec["render_scale"] = scale
    return spec


def cmd_queue(args):
    from studio.render import RenderQueue
    episode = load_json(EPISODE)
    wanted = set(args.shots.split(",")) if args.shots else None
    jobs, start = [], 0
    for shot in episode["shots"]:
        if wanted is None or shot["id"] in wanted:
            jobs.append((shot["id"], load_json(PROJECT / "data" / "shots" / f"{shot['id']}.json"), start))
        start += shot["frames"]
    queue = RenderQueue(args.out, mode=args.mode, quality=args.quality, draft=args.draft,
                        burn=args.burn, workers=args.workers)
    _print(queue.run(jobs))


def cmd_assemble(args):
    from studio.render import assemble
    episode = load_json(EPISODE)
    src = Path(args.src)
    ext = ".mkv" if any(src.glob("*.mkv")) else ".mp4"
    files = [src / f"{s['id']}{ext}" for s in episode["shots"]]
    missing = [rel(f) for f in files if not f.exists()]
    if missing:
        raise SystemExit(f"missing {len(missing)} shot renders, e.g. {missing[:3]}")
    _print(assemble(files, Path(args.out) / "episode", expected_frames=episode["body_frames"], audio=args.audio))


def cmd_qa(args):
    from studio.qa import review
    spec = load_json(args.spec)
    motion = load_json(args.motion) if args.motion else None
    report = review(spec, motion=motion, render=args.render, out_dir=args.out, scale=args.scale)
    _print({k: report[k] for k in ("shot", "flag_count", "sheet")} | {"report": rel(Path(args.out) / "qa_report.json")})


def cmd_layers(args):
    from studio import layers
    if args.action == "split":
        _print(layers.split(args.inputs[0], args.grid, args.out))
    elif args.action == "matte":
        _print(layers.matte(args.inputs[0], args.out, choke=args.choke))
    else:
        box = [float(v) for v in args.box.split(",")] if args.box else None
        scales = [float(v) for v in args.scales.split(",")]
        report = layers.register(args.reference, args.inputs, args.out, lock=args.lock, box=box, scales=scales)
        _print({"cels": [{k: c.get(k) for k in ("cel", "dx", "dy", "scale", "residual_after", "status")}
                         for c in report["cels"]], "report": rel(Path(args.out) / "registration.json")})


def cmd_motion(args):
    from studio import motion
    data = load_json(args.motion)
    if args.action == "check":
        report = motion.check(data)
        _print(report)
        if report["errors"]:
            raise SystemExit(1)
    else:
        spec, report = motion.compile_file(args.motion, args.out)
        _print({"spec": rel(args.out), "warnings": report["warnings"], "contacts": report["contacts"]})


def cmd_sound(args):
    from studio import sound
    if args.action == "lines":
        shots = set(args.shots.split(",")) if args.shots else None
        data = {"source": rel(EPISODE), "lines": sound.lines(shots),
                "note": "Speakers marked speaker_inferred need script-supervisor confirmation before recording."}
        if args.out:
            write_json(args.out, data)
        _print({"lines": len(data["lines"]), "confirmed_speakers": sum(not l["speaker_inferred"] for l in data["lines"]),
                "out": args.out})
    elif args.action == "mouth":
        result = sound.mouth(args.input, rate_frames=args.rate, offset_frames=args.offset)
        if args.out:
            write_json(args.out, result)
        _print(result)
    else:
        _print(sound.mix(load_json(args.input), args.out))


def cmd_generate(args):
    from studio import generate
    try:
        if args.kind == "image":
            _print(generate.image(run=args.run, task_id=args.task, prompt_file=args.prompt_file, refs=args.ref,
                                  out=args.out, mode=args.mode, dry_run=args.dry_run))
        else:
            _print(generate.voice(run=args.run, task_id=args.task, line_id=args.line, out=args.out,
                                  dry_run=args.dry_run))
    except Exception as exc:
        raise SystemExit(f"generation refused: {exc}")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python -m studio", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("status", help="episode, runs, registry and spend summary").set_defaults(func=cmd_status)

    p = sub.add_parser("plan", help="add a pipeline spec's 27 tasks to a ledger run")
    p.add_argument("spec")
    p.add_argument("--run")
    p.set_defaults(func=cmd_plan)

    p = sub.add_parser("run", help="Codex runner: workers, reviewers, revisions")
    p.add_argument("--run", required=True)
    p.add_argument("--max-tasks", type=int)
    p.add_argument("--parallel", type=int, default=1)
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("next", help="list ready tasks")
    p.add_argument("--run", required=True)
    p.set_defaults(func=cmd_next)

    p = sub.add_parser("approve", help="Luis only: creative approval of an author-gated task")
    p.add_argument("--run", required=True)
    p.add_argument("task")
    p.add_argument("--decision", choices=("approve", "reject"), required=True)
    p.add_argument("--evidence", required=True)
    p.add_argument("--i-am-luis", action="store_true")
    p.set_defaults(func=cmd_approve)

    p = sub.add_parser("render", help="render one shot spec")
    p.add_argument("spec")
    p.add_argument("--out", required=True, help=".mp4 review, .mkv lossless master, or a directory for PNGs")
    p.add_argument("--draft", action="store_true")
    p.add_argument("--quality", choices=("draft", "final"), default="final")
    p.add_argument("--burn", action="store_true")
    p.add_argument("--base")
    p.set_defaults(func=cmd_render)

    p = sub.add_parser("animatic", help="build all 128 shot specs and render the animatic")
    p.add_argument("--out", default="projects/cemi_episode_01/renders/animatic")
    p.add_argument("--shots")
    p.add_argument("--scale", type=float, default=0.5)
    p.add_argument("--workers", type=int, default=2)
    p.add_argument("--build-only", action="store_true")
    p.add_argument("--master", action="store_true", help="lossless FFV1 shot files (large) instead of H.264")
    p.set_defaults(func=cmd_animatic)

    p = sub.add_parser("queue", help="render shots from data/shots with checkpoints")
    p.add_argument("--out", required=True)
    p.add_argument("--shots")
    p.add_argument("--mode", choices=("master", "review", "frames"), default="master")
    p.add_argument("--quality", choices=("draft", "final"), default="final")
    p.add_argument("--draft", action="store_true")
    p.add_argument("--burn", action="store_true")
    p.add_argument("--workers", type=int, default=1)
    p.set_defaults(func=cmd_queue)

    p = sub.add_parser("assemble", help="concatenate rendered shot masters in episode order")
    p.add_argument("--src", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--audio")
    p.set_defaults(func=cmd_assemble)

    p = sub.add_parser("qa", help="automated review flags + repair task stubs")
    p.add_argument("spec")
    p.add_argument("--motion")
    p.add_argument("--render")
    p.add_argument("--out", required=True)
    p.add_argument("--scale", type=float, default=0.5)
    p.set_defaults(func=cmd_qa)

    p = sub.add_parser("layers", help="split | matte | register")
    p.add_argument("action", choices=("split", "matte", "register"))
    p.add_argument("inputs", nargs="+")
    p.add_argument("--out", required=True)
    p.add_argument("--grid", default="4x2")
    p.add_argument("--choke", type=int, default=0)
    p.add_argument("--reference")
    p.add_argument("--lock")
    p.add_argument("--box", help="x,y,w,h lock region in reference pixels")
    p.add_argument("--scales", default="1.0")
    p.set_defaults(func=cmd_layers)

    p = sub.add_parser("motion", help="compile | check a motion spec")
    p.add_argument("action", choices=("compile", "check"))
    p.add_argument("motion")
    p.add_argument("--out")
    p.set_defaults(func=cmd_motion)

    p = sub.add_parser("sound", help="lines | mouth | mix")
    p.add_argument("action", choices=("lines", "mouth", "mix"))
    p.add_argument("input", nargs="?")
    p.add_argument("--shots")
    p.add_argument("--out")
    p.add_argument("--rate", type=int, default=3)
    p.add_argument("--offset", type=int, default=0)
    p.set_defaults(func=cmd_sound)

    p = sub.add_parser("generate", help="opt-in paid generation (policy + task budget enforced)")
    p.add_argument("kind", choices=("image", "voice"))
    p.add_argument("--run", required=True)
    p.add_argument("--task", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--prompt-file")
    p.add_argument("--ref", action="append", default=[])
    p.add_argument("--mode")
    p.add_argument("--line")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_generate)

    args = parser.parse_args(argv)
    if args.command == "layers" and args.action == "register" and not args.reference:
        parser.error("layers register needs --reference")
    if args.command == "motion" and args.action == "compile" and not args.out:
        parser.error("motion compile needs --out")
    args.func(args)


if __name__ == "__main__":
    main()
