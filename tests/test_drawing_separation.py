"""Regression tests for the shared drawing/motion separation tool."""
import copy
import unittest

from studio.drawing.separation import (
    SeparationError, scalar_pair, vector_pair, apply_drawing, check_pose_points
)


def sample_drawing():
    return {"version": 1, "canvas": [100, 100], "primitives": [
        {"id": "fabric.panel", "kind": "fill", "provenance": "procedural",
         "color": "#112233",
         "curve": [
             [[20, 20], [20, 30], [40, 30], [40, 20]],
             [[40, 20], [40, 50], [20, 50], [20, 20]],
         ]}
    ]}


def rules():
    return [{"upper": {"id": "fabric.panel", "segment": 0, "point": 0},
             "lower": {"id": "fabric.panel", "segment": 1, "point": 2},
             "minimum": 40, "axis": [0, -1]}]


class SeparationTest(unittest.TestCase):
    def test_scalar_matches_requested_formula(self):
        self.assertEqual(scalar_pair(3, 1, 6), (5, -1, 4))
        self.assertEqual(scalar_pair(9, 1, 6), (9, 1, 0))

    def test_screen_y_and_midpoint_preservation(self):
        a, b, d = vector_pair([10, 20], [10, 24], 8)
        self.assertEqual((a, b, d), ([10, 18], [10, 26], 4))
        self.assertEqual((a[1] + b[1]) / 2, 22)

    def test_nonvertical_axis(self):
        a, b, d = vector_pair([0, 0], [2, 0], 4, axis=[-1, 0])
        self.assertEqual((a, b, d), ([-1, 0], [3, 0], 2))

    def test_drawing_closed_and_original_untouched(self):
        orig = sample_drawing()
        before = copy.deepcopy(orig)
        new, changes = apply_drawing(orig, rules())
        self.assertEqual(orig, before)
        self.assertAlmostEqual(changes[0]["delta"], 10)
        self.assertEqual(new["primitives"][0]["curve"][0][0], [20, 15])
        self.assertEqual(new["primitives"][0]["curve"][-1][-1], [20, 15])

    def test_embedded_rule_and_fail_closed(self):
        orig = sample_drawing()
        orig["separation_constraints"] = rules()
        new, changes = apply_drawing(orig)
        self.assertNotIn("separation_constraints", new)
        self.assertEqual(len(changes), 1)
        orig["separation_constraints"][0]["minimum"] = float("nan")
        with self.assertRaises(SeparationError):
            apply_drawing(orig)
        orig["separation_constraints"][0]["minimum"] = 40
        orig["status"] = "author-approved"
        with self.assertRaises(SeparationError):
            apply_drawing(orig)

    def test_pair_names_motion_check(self):
        poses = {"upper": [5, 10], "lower": [5, 12]}
        pair = [{"upper": "upper", "lower": "lower", "minimum": 6}]
        self.assertEqual(len(check_pose_points(poses, pair)), 1)
        self.assertEqual(check_pose_points({"upper": [5, 10], "lower": [5, 20]}, pair), [])
        self.assertEqual(poses["upper"], [5, 10])

    def test_both_renderers_honor_constraint(self):
        import numpy as np
        from studio.drawing import render
        source = sample_drawing()
        corrected, _ = apply_drawing(source, rules())
        source["separation_constraints"] = rules()
        self.assertTrue(np.array_equal(np.asarray(render.render(source)),
                                       np.asarray(render.render(corrected))))
        self.assertEqual(render.to_svg(source), render.to_svg(corrected))

    def test_motion_qa_reports_separation_without_rewriting(self):
        from studio.motion import check
        shot = {"shot": "TEST-001", "frames": 24, "elements": [
            {"name": "cloth", "kind": "character", "rate": 2,
             "poses": [{"frame": 0, "drawing": "missing.png",
                        "points": {"upper": [5, 10], "lower": [5, 12]}}],
             "separation_constraints": [{"upper": "upper", "lower": "lower", "minimum": 6}]}
        ]}
        before = copy.deepcopy(shot)
        report = check(shot)
        self.assertEqual(shot, before)
        self.assertTrue(any("need 4.000px more separation" in x for x in report["errors"]))
        from studio.motion import compile_spec, MotionError
        with self.assertRaises(MotionError):
            compile_spec(shot)



if __name__ == "__main__":
    unittest.main()
