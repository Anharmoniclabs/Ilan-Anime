"""Studio toolkit tests: engine math, FX, layers, motion, policy, runner, sound.

Fast and offline. Paid APIs are exercised only through a mocked transport and a
fake ``codex`` executable, so no test can spend money or start a real agent.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
import wave

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from studio.engine import Compositor, SpecError  # noqa: E402
from studio.engine.compositor import interpolate  # noqa: E402
from studio import layers, motion, policy as pol, sound  # noqa: E402


def _square(path, size=40, color=(200, 40, 40, 255), canvas=None, at=(0, 0)):
    canvas = canvas or (size, size)
    img = Image.new("RGBA", canvas, (0, 0, 0, 0))
    img.paste(Image.new("RGBA", (size, size), color), at)
    img.save(path)
    return path


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)

    def spec(self, layers, **extra):
        return {"id": "T", "size": [200, 200], "frames": 24, "background": [0, 0, 0, 255], "layers": layers, **extra}

    def red_bbox(self, image):
        arr = np.asarray(image)
        ys, xs = np.nonzero(arr[..., 0] > 100)
        return xs.min(), xs.max(), ys.min(), ys.max(), len(xs)

    def test_rotation_does_not_clip_tight_cutouts(self):
        src = _square(self.tmp / "sq.png", 60)
        spec = self.spec([{"name": "a", "source": str(src), "rate": 1,
                           "keys": [{"frame": 0, "x": 70, "y": 70, "angle": 45}]}])
        *_, area = self.red_bbox(Compositor(spec).draw(0))
        self.assertGreater(area, 60 * 60 * 0.97)  # v1 lost ~17% here

    def test_scale_and_rotation_use_unscaled_pivot(self):
        src = _square(self.tmp / "sq.png", 40)
        # pivot at the square's top-left corner, placed at (100,100): scaling 2x keeps that corner fixed
        spec = self.spec([{"name": "a", "source": str(src), "rate": 1, "pivot": [0, 0],
                           "keys": [{"frame": 0, "x": 100, "y": 100, "scale": 2}]}])
        x0, x1, y0, y1, _ = self.red_bbox(Compositor(spec).draw(0))
        self.assertEqual((x0, y0), (100, 100))
        self.assertAlmostEqual(x1 - x0 + 1, 80, delta=1)

    def test_parallax_scales_camera_motion(self):
        src = _square(self.tmp / "sq.png", 20)
        base = [{"name": "far", "source": str(src), "rate": 1, "parallax": 0.5,
                 "keys": [{"frame": 0, "x": 90, "y": 90}]}]
        cam = [{"frame": 0, "x": 0}, {"frame": 23, "x": 40}]
        x0 = self.red_bbox(Compositor(self.spec(base, camera=cam)).draw(23))[0]
        self.assertAlmostEqual(x0, 110, delta=1)  # moved 20 px for a 40 px camera move

    def test_layer_clock_holds_drawings_on_threes(self):
        a, b = _square(self.tmp / "a.png", 20), _square(self.tmp / "b.png", 20, (40, 200, 40, 255))
        spec = self.spec([{"name": "c", "sequence": [str(a), str(b)], "rate": 3,
                           "keys": [{"frame": 0, "x": 0}, {"frame": 23, "x": 46}]}])
        comp = Compositor(spec)
        self.assertTrue(np.array_equal(np.asarray(comp.draw(3)), np.asarray(comp.draw(5))))
        self.assertFalse(np.array_equal(np.asarray(comp.draw(5)), np.asarray(comp.draw(6))))

    def test_parent_carries_child(self):
        hull = _square(self.tmp / "hull.png", 60, (40, 40, 200, 255))
        rider = _square(self.tmp / "rider.png", 10)
        spec = self.spec([
            {"name": "hull", "source": str(hull), "rate": 1, "keys": [{"frame": 0, "x": 20}, {"frame": 23, "x": 66}]},
            {"name": "rider", "source": str(rider), "rate": 1, "parent": "hull", "keys": [{"frame": 0, "x": 5, "y": 5}]}])
        comp = Compositor(spec)
        self.assertEqual(self.red_bbox(comp.draw(0))[0], 25)
        self.assertEqual(self.red_bbox(comp.draw(23))[0], 71)

    def test_deterministic_and_post_stack_runs(self):
        src = _square(self.tmp / "sq.png", 200, (120, 90, 60, 255))
        post = {"grain": 0.4, "weave": 0.5, "chroma": 0.5, "halation": 0.4, "vignette": 0.3, "grade": "1957",
                "press": [{"frame": 0, "value": 0}, {"frame": 23, "value": 1}],
                "flash": [{"frame": 5, "frames": 1}], "harmony": [{"start": 10, "end": 16}]}
        spec = self.spec([{"name": "bg", "source": str(src), "rate": 1, "tags": ["bg"]}], post=post)
        a, b = Compositor(spec).draw(12), Compositor(spec).draw(12)
        self.assertTrue(np.array_equal(np.asarray(a), np.asarray(b)))
        self.assertTrue((np.asarray(Compositor(spec).draw(5)) > 250).all())  # white flash frame

    def test_generators_render(self):
        for kind, extra in (("sigil", {"draw_frames": 10}), ("text", {"text": ["BEFORE"]}),
                            ("slate", {"shot": "S00", "action": "x"}), ("speed_lines", {}),
                            ("train_strobe", {}), ("ring", {}), ("lanes", {}),
                            ("phone", {"messages": [{"at": 0, "text": "hi"}]})):
            spec = self.spec([{"name": "g", "generator": {"type": kind, **extra}, "rate": 1, "screen_space": True}])
            self.assertEqual(Compositor(spec).draw(12).size, (200, 200), kind)

    def test_invalid_specs_rejected(self):
        with self.assertRaises(SpecError):
            Compositor(self.spec([{"name": "x", "rate": 1}]))
        with self.assertRaises(SpecError):
            Compositor(self.spec([{"name": "x", "generator": {"type": "nope"}}]))

    def test_interpolate_ease(self):
        keys = [{"frame": 0, "x": 0, "ease": "smooth"}, {"frame": 10, "x": 10}]
        self.assertAlmostEqual(interpolate(keys, 5, {"x": 0})["x"], 5)
        self.assertLess(interpolate(keys, 2, {"x": 0})["x"], 2)

    def test_scaled_render_matches_layout(self):
        src = _square(self.tmp / "sq.png", 40)
        spec = self.spec([{"name": "a", "source": str(src), "rate": 1, "keys": [{"frame": 0, "x": 100, "y": 100}]}])
        x0, *_ = self.red_bbox(Compositor(spec, scale=0.5).draw(0))
        self.assertEqual(x0, 50)


class LayerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)

    def _scene(self, path, shift=(0, 0), redraw=False):
        rng = np.random.default_rng(1)
        arr = (rng.uniform(0, 255, (120, 160, 3))).astype(np.uint8)
        img = Image.fromarray(arr).convert("RGBA")
        img = img.transform(img.size, Image.Transform.AFFINE, (1, 0, -shift[0], 0, 1, -shift[1]))
        if redraw:
            noise = (np.random.default_rng(9).uniform(0, 255, (120, 160, 3))).astype(np.uint8)
            img = Image.fromarray(noise).convert("RGBA")
        img.save(path)
        return path

    def test_register_recovers_shift_and_flags_redraws(self):
        ref = self._scene(self.tmp / "ref.png")
        moved = self._scene(self.tmp / "moved.png", shift=(6, -3))
        redrawn = self._scene(self.tmp / "redrawn.png", redraw=True)
        report = layers.register(ref, [moved, redrawn], self.tmp / "out", box=[30, 30, 90, 60])
        first, second = report["cels"]
        self.assertAlmostEqual(first["dx"], -6, delta=0.3)
        self.assertAlmostEqual(first["dy"], 3, delta=0.3)
        self.assertEqual(first["status"], "aligned")
        self.assertEqual(second["status"], "needs_redraw")

    def test_split_and_matte(self):
        atlas = Image.new("RGBA", (80, 40), (0, 0, 0, 0))
        atlas.paste(Image.new("RGBA", (20, 20), (255, 0, 0, 255)), (10, 10))
        atlas.save(self.tmp / "atlas.png")
        report = layers.split(self.tmp / "atlas.png", "2x1", self.tmp / "cels")
        self.assertEqual(len(report["cels"]), 2)
        result = layers.matte(ROOT / report["cels"][0] if not Path(report["cels"][0]).is_absolute()
                              else report["cels"][0], self.tmp / "clean.png")
        self.assertIn("edge_pixels", result)


class MotionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.hull = _square(self.tmp / "hull.png", 60, (40, 40, 200, 255))
        self.a = _square(self.tmp / "pose_a.png", 20)
        self.b = _square(self.tmp / "pose_b.png", 20, (200, 200, 40, 255))

    def motion(self, **override):
        data = {"shot": "T-01", "size": [200, 200], "frames": 24, "elements": [
            {"name": "hull", "kind": "rigid", "source": str(self.hull), "rate": 1,
             "keys": [{"frame": 0, "x": 20, "y": 100}, {"frame": 23, "x": 40, "y": 100}],
             "anchors": {"seat": [10, 0]}},
            {"name": "rider", "kind": "character", "rate": 2, "parent": "hull",
             "poses": [{"frame": 0, "drawing": str(self.a), "points": {"foot": [0, 20]}},
                       {"frame": 12, "drawing": str(self.b), "points": {"foot": [0, 20]}}],
             "keys": [{"frame": 0, "x": 10, "y": -20}]}],
            "contacts": [{"element": "rider", "point": "foot", "anchor": {"element": "hull", "point": "seat"},
                          "start": 0, "end": 24, "tolerance": 0.5}]}
        data.update(override)
        return data

    def test_compile_and_contact_lock_hold(self):
        report = motion.check(self.motion())
        self.assertEqual(report["errors"], [])
        self.assertLessEqual(report["contacts"][0]["max_px"], 0.5)
        spec = motion.compile_spec(self.motion())
        self.assertEqual(spec["layers"][1]["exposures"][1], {"start": 12, "end": 24, "source": str(self.b)})

    def test_contact_drift_and_rules_fail(self):
        bad = self.motion()
        bad["elements"][1]["keys"] = [{"frame": 0, "x": 10, "y": -20}, {"frame": 23, "x": 30, "y": -20}]
        self.assertTrue(any(e.startswith("contact") for e in motion.check(bad)["errors"]))
        warp = self.motion()
        warp["elements"][1]["keys"] = [{"frame": 0, "x": 10, "y": -20, "scale": 1.1}]
        self.assertTrue(any("not acting" in e for e in motion.check(warp)["errors"]))
        offgrid = self.motion()
        offgrid["elements"][1]["poses"][1]["frame"] = 13
        self.assertTrue(any("exposure grid" in e for e in motion.check(offgrid)["errors"]))


class PolicyAndGenerationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.log = self.tmp / "spend.jsonl"
        self.task = {"id": "t1", "role": "key-animator", "state": "running", "budget": {"max_cost_usd": 2}}
        self.policy = {"generation": {"enabled": True, "max_total_usd": 3, "max_per_task_usd": 2}}

    def test_refusals(self):
        off = {"generation": {"enabled": False}}
        with self.assertRaises(pol.PolicyError):
            pol.authorize("image", 0.5, self.task, ["image"], off, self.log)
        with self.assertRaises(pol.PolicyError):
            pol.authorize("image", None, self.task, ["image"], self.policy, self.log)
        with self.assertRaises(pol.PolicyError):
            pol.authorize("voice", 0.5, self.task, ["image"], self.policy, self.log)
        with self.assertRaises(pol.PolicyError):
            pol.authorize("image", 0.5, {**self.task, "state": "submitted"}, ["image"], self.policy, self.log)

    def test_caps_count_sent_calls(self):
        pol.authorize("image", 1.5, self.task, ["image"], self.policy, self.log)
        pol.append({"task_id": "t1", "estimated_usd": 1.5, "status": "sent"}, self.log)
        with self.assertRaises(pol.PolicyError):  # per-task 2.0
            pol.authorize("image", 1.0, self.task, ["image"], self.policy, self.log)
        pol.append({"task_id": "t2", "estimated_usd": 1.4, "status": "ok"}, self.log)
        with self.assertRaises(pol.PolicyError):  # total 3.0
            pol.authorize("image", 0.2, {**self.task, "id": "t3"}, ["image"], self.policy, self.log)

    def test_default_policy_is_off(self):
        data = json.loads((ROOT / "production" / "policy.json").read_text())
        self.assertFalse(data["generation"]["enabled"])
        self.assertEqual(data["generation"]["max_total_usd"], 0)

    def test_image_dry_run_builds_reference_edit(self):
        from studio import generate
        run_dir = ROOT / "production" / "runs" / "unit-gen-test"
        task_dir = run_dir / "tasks" / "t1"
        self.addCleanup(shutil.rmtree, run_dir, True)
        task_dir.mkdir(parents=True)
        (run_dir / "ledger.json").write_text(json.dumps({"tasks": {"t1": {
            "id": "t1", "role": "key-animator", "state": "running", "budget": {"max_cost_usd": 0},
            "output_dir": "production/runs/unit-gen-test/tasks/t1"}}}))
        ref = _square(self.tmp / "ref.png", 8)
        prompt = self.tmp / "p.md"
        prompt.write_text("Beheto, palms pressing the drum.")
        out = generate.image(run="unit-gen-test", task_id="t1", prompt_file=prompt, refs=[ref],
                             out=task_dir / "key.png", dry_run=True)
        self.assertEqual(out["endpoint"], "edits")
        self.assertIn("Match the attached reference drawings", out["prompt"])
        with self.assertRaises(generate.GenerationError):
            generate.image(run="unit-gen-test", task_id="t1", prompt_file=prompt, refs=[ref],
                           out=self.tmp / "outside.png", dry_run=True)


FAKE_CODEX = r'''#!/usr/bin/env python3
import json, os, re, sys, uuid
args = sys.argv[1:]
out = args[args.index("-o") + 1]
schema = json.load(open(args[args.index("--output-schema") + 1]))
prompt = args[-1]
print(json.dumps({"type": "thread.started", "thread_id": str(uuid.uuid4())}))
if "decision" in schema["properties"]:
    res = {"decision": os.environ.get("FAKE_DECISION", "approve"), "evidence": "viewed notes.md", "repair_notes": ["fix"]}
else:
    od = re.search(r'"output_dir": "([^"]+)"', prompt).group(1)
    tid = re.search(r'"id": "([^"]+)"', prompt).group(1)
    role = re.search(r'"role": "([^"]+)"', prompt).group(1)
    os.makedirs(od, exist_ok=True)
    open(os.path.join(od, "notes.md"), "w").write("x")
    res = {"task_id": tid, "role": role, "status": "submitted", "artifacts": [od + "/notes.md"],
           "evidence": ["wrote notes.md"], "blockers": []}
json.dump(res, open(out, "w"))
'''


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.repo = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.repo)
        (self.repo / "production").mkdir()
        roles = {"maker": {"skill": ".agents/skills/anime-maker/SKILL.md", "reviewer": "checker", "generate": []},
                 "checker": {"skill": ".agents/skills/anime-checker/SKILL.md", "reviewer": "maker", "generate": []}}
        (self.repo / "production" / "roles.json").write_text(json.dumps(roles))
        (self.repo / "AGENTS.md").write_text("test")
        codex = self.repo / "fakecodex"
        codex.write_text(FAKE_CODEX)
        codex.chmod(codex.stat().st_mode | stat.S_IEXEC)
        self.policy = {"generation": {"enabled": False}, "codex": {"binary": str(codex)},
                       "revisions": {"auto_create_on_reject": True, "max_revisions_per_task": 1}}
        from production.runtime import Ledger
        ledger = Ledger(self.repo, "r1")
        ledger.initialize()
        for tid, deps in (("a", []), ("b", ["a"])):
            ledger.add({"id": tid, "role": "maker", "shots": ["S01-11"], "objective": f"do {tid}",
                        "inputs": ["AGENTS.md"], "output_dir": f"production/runs/r1/tasks/{tid}",
                        "depends_on": deps, "require_host_bindings": True})

    def runner(self):
        from studio.runner import CodexRunner
        return CodexRunner("r1", policy=self.policy, root=self.repo, log=lambda m: None)

    def test_worker_reviewer_and_dependency(self):
        out = self.runner().loop()
        self.assertEqual(out["states"], {"a": "approved", "b": "approved"})
        handoffs = json.loads((self.repo / "production/runs/r1/handoffs.json").read_text())["bindings"]
        self.assertNotEqual(handoffs["a"]["creator"]["host_agent_id"], handoffs["a"]["reviewer"]["host_agent_id"])

    def test_reject_creates_revision_then_pauses(self):
        import os
        os.environ["FAKE_DECISION"] = "reject"
        self.addCleanup(os.environ.pop, "FAKE_DECISION", None)
        out = self.runner().loop(max_tasks=3)
        self.assertEqual(out["states"]["a"], "rejected")
        self.assertEqual(out["states"]["a-r1"], "rejected")
        self.assertTrue(out["paused"])

    def test_interrupted_run_pauses_instead_of_relaunching(self):
        from studio.runner import RunnerError
        state = self.repo / "production/runs/r1/runner_state.json"
        state.write_text(json.dumps({"inflight": {"a": {"phase": "worker"}}, "history": []}))
        with self.assertRaises(RunnerError):
            self.runner().loop()
        from production.runtime import Ledger
        self.assertTrue(Ledger(self.repo, "r1").data["paused"])


class QATests(unittest.TestCase):
    def test_flags_and_repair_tasks(self):
        from studio import qa
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp)
        rng = np.random.default_rng(3)
        for name in ("a", "b"):  # same silhouette, re-rendered interior = boil
            arr = np.zeros((40, 40, 4), np.uint8)
            arr[5:35, 5:35, :3] = rng.uniform(0, 255, (30, 30, 3))
            arr[5:35, 5:35, 3] = 255
            Image.fromarray(arr, "RGBA").save(tmp / f"{name}.png")
        spec = {"id": "Q-01", "size": [64, 64], "frames": 12, "status": "exploratory", "layers": [
            {"name": "c", "tags": ["character"], "rate": 2, "source": str(tmp / "a.png"),
             "exposures": [{"start": 0, "end": 6, "source": str(tmp / "a.png")},
                           {"start": 6, "end": 12, "source": str(tmp / "b.png")}]}]}
        report = qa.review(spec, out_dir=tmp / "qa", scale=1.0, freeze_limit=100)
        types = {f["type"] for f in report["flags"]}
        self.assertIn("boil", types)
        self.assertNotIn("no_acting", types)
        self.assertEqual(report["revision_tasks"][0]["role"], "key-animator")
        held = dict(spec, stage="animatic")
        self.assertIn("no_acting", {f["type"] for f in qa.review(held, out_dir=tmp / "qa2", scale=1.0)["flags"]})


class RenderTests(unittest.TestCase):
    def test_export_manifest_resume_and_assemble(self):
        from studio.render import RenderQueue, assemble, is_current
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp)
        specs = [(f"T{i}", {"id": f"T{i}", "size": [64, 36], "frames": 6 + i, "status": "exploratory",
                            "layers": [{"name": "s", "generator": {"type": "solid", "color": "#C9A24A"},
                                        "screen_space": True, "rate": 1}]}, 0) for i in range(2)]
        queue = RenderQueue(tmp / "shots", mode="review", draft=True)
        self.assertEqual(queue.run(specs, progress=lambda m: None)["rendered"], 2)
        self.assertTrue(is_current(specs[0][1], queue.output_for("T0"), mode="review"))
        self.assertEqual(queue.run(specs, progress=lambda m: None)["skipped_current"], 2)
        result = assemble([queue.output_for("T0"), queue.output_for("T1")], tmp / "ep", expected_frames=13)
        self.assertEqual(result["frames"], 13)

    def test_unready_spec_needs_draft(self):
        from studio.engine.io import ExportError
        from studio.render import export_shot
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp)
        spec = {"id": "X", "size": [64, 36], "frames": 2, "status": "missing_art",
                "layers": [{"name": "s", "generator": {"type": "solid"}, "screen_space": True, "rate": 1}]}
        with self.assertRaises(ExportError):
            export_shot(spec, tmp / "x.mp4")


class SoundAndAnimaticTests(unittest.TestCase):
    def test_lines_found(self):
        found = sound.lines()
        self.assertGreater(len(found), 50)
        self.assertTrue(all(l["text"] for l in found))

    def test_mouth_closes_on_silence(self):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp)
        sr = 48000
        t = np.arange(sr) / sr
        audio = np.concatenate([np.sin(2 * math.pi * 220 * t[: sr // 2]) * 0.5, np.zeros(sr // 2)])
        with wave.open(str(tmp / "take.wav"), "w") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(sr)
            w.writeframes((audio * 32767).astype(np.int16).tobytes())
        result = sound.mouth(tmp / "take.wav", rate_frames=3)
        self.assertEqual(result["exposures"][-1]["shape"], "closed")
        self.assertEqual(result["frames"], 24)

    def test_animatic_specs_cover_every_frame(self):
        from studio.animatic import build_all
        specs = build_all(write=False)
        self.assertEqual(len(specs), 128)
        self.assertEqual(sum(spec["frames"] for _, spec, _ in specs), 27120)
        self.assertTrue(all(spec["stage"] == "animatic" and spec["status"] not in
                            ("animation_ready", "approved") for _, spec, _ in specs))

    def test_skills_are_generated_and_current(self):
        result = subprocess.run([sys.executable, str(ROOT / "production" / "build_skills.py"), "--check"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout)


if __name__ == "__main__":
    unittest.main()
