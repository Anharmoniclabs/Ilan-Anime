import copy
import json
import math
import tempfile
import unittest

import numpy as np

from studio.drawing.schema import DrawingError, validate_drawing, validate_identity

try:
    import cv2  # noqa: F401
except ImportError:  # pragma: no cover
    cv2 = None


def _identity():
    L = {"eye_l.outer": [40, 60], "eye_l.inner": [70, 62], "eye_l.top": [55, 53], "eye_l.bottom": [55, 66],
         "eye_l.iris": [55, 60], "eye_r.inner": [90, 62], "eye_r.outer": [120, 60], "eye_r.top": [105, 53],
         "eye_r.bottom": [105, 66], "eye_r.iris": [105, 60], "brow_l.outer": [36, 46], "brow_l.peak": [54, 42],
         "brow_l.inner": [72, 48], "brow_r.inner": [88, 48], "brow_r.peak": [106, 42], "brow_r.outer": [124, 46],
         "nose.tip": [80, 85], "mouth.l": [62, 105], "mouth.r": [98, 105], "mouth.top": [80, 101],
         "mouth.bottom": [80, 112], "chin": [80, 135]}
    P = {"skin": "#b16a3c", "brow": "#000000", "ink": "#010000", "ink_soft": "#814d2b", "eye_white": "#e3d7cc",
         "iris": "#663820", "iris_dark": "#2a1409", "pupil": "#120806", "mouth_dark": "#3b1712",
         "teeth": "#efe4d8", "lip_shadow": "#532914", "lip_lower": "#a15b36"}
    return {"character": "test", "view": "front", "canvas": [160, 160], "source": "x.png", "source_sha256": "0",
            "status": "candidate", "landmarks": L, "palette": P}


def _stroke(pid="a.b", **kw):
    p = {"id": pid, "kind": "stroke", "provenance": "procedural", "color": "#112233",
         "curve": [[[1, 1], [5, 1], [9, 5], [9, 9]]], "width": [1, 3, 1]}
    p.update(kw)
    return p


class SchemaTest(unittest.TestCase):
    def _d(self, *prims):
        return {"version": 1, "canvas": [64, 64], "primitives": list(prims)}

    def test_valid(self):
        validate_drawing(self._d(_stroke()))

    def test_rejects_bad_input(self):
        cases = {
            "space in id": _stroke("head silhouette"),
            "nan": _stroke(curve=[[[1, 1], [math.nan, 1], [9, 5], [9, 9]]]),
            "unbounded": _stroke(curve=[[[1, 1], [1e9, 1], [9, 5], [9, 9]]]),
            "bad provenance": _stroke(provenance="claude"),
            "bad color": _stroke(color="brown"),
            "short segment": _stroke(curve=[[[1, 1], [5, 1], [9, 9]]]),
            "no width": _stroke(width=[2]),
            "open fill": _stroke(kind="fill"),
            "unknown clip": _stroke(clip="nothing.here"),
        }
        for name, prim in cases.items():
            with self.subTest(name):
                with self.assertRaises(DrawingError):
                    validate_drawing(self._d(prim))

    def test_rejects_duplicate_ids_and_broken_chain(self):
        with self.assertRaises(DrawingError):
            validate_drawing(self._d(_stroke(), _stroke()))
        with self.assertRaises(DrawingError):
            validate_drawing(self._d(_stroke(curve=[[[1, 1], [2, 2], [3, 3], [4, 4]], [[9, 9], [1, 1], [2, 2], [3, 3]]])))

    def test_resource_limit(self):
        with self.assertRaises(DrawingError):
            validate_drawing(self._d(*[_stroke(f"p.n{i}") for i in range(2001)]))

    def test_identity_status_gate(self):
        ident = _identity()
        validate_identity(ident)
        ident["status"] = "approved-by-model"
        with self.assertRaises(DrawingError):
            validate_identity(ident)


@unittest.skipIf(cv2 is None, "OpenCV not installed")
class FaceTest(unittest.TestCase):
    def test_expressions_build_valid_distinct_drawings(self):
        from studio.drawing import face, render
        ident = _identity()
        outs = {}
        for name in face.EXPRESSIONS:
            d = validate_drawing(face.construct(ident, face.expression(name)))
            self.assertTrue(all(p["provenance"] == "procedural" for p in d["primitives"]))
            outs[name] = np.asarray(render.render(d), dtype=np.float32)
        self.assertGreater(np.abs(outs["fear"] - outs["neutral"]).mean(), 0.5)
        self.assertGreater(np.abs(outs["fear"] - outs["sorrow"]).mean(), 0.5)

    def test_fear_raises_brows_and_opens_eyes(self):
        from studio.drawing import face
        ident = _identity()
        n = {p["id"]: p for p in face.construct(ident, face.expression("neutral"))["primitives"]}
        f = {p["id"]: p for p in face.construct(ident, face.expression("fear"))["primitives"]}
        inner = lambda d: d["face.brow.l"]["curve"][0][3][1]  # noqa: E731
        self.assertLess(inner(f), inner(n) - 2)  # inner brow end higher (smaller y)
        top = lambda d: min(pt[1] for pt in d["face.eye.l.white"]["curve"][0])  # noqa: E731
        self.assertLess(top(f), top(n))
        self.assertIn("face.mouth.interior", f)
        self.assertNotIn("face.mouth.interior", n)

    def test_expression_parameters_are_bounded(self):
        from studio.drawing import face
        with self.assertRaises(DrawingError):
            face.expression("fear", brow_raise=3)
        with self.assertRaises(DrawingError):
            face.expression("rage")
        with self.assertRaises(DrawingError):
            face.expression(nose_size=1)


class ModelPlanTest(unittest.TestCase):
    def test_validate_plan(self):
        from studio.drawing.model import validate_plan
        self.assertEqual(validate_plan('{"expression":"fear","intensity":0.5,"gaze":"left"}')["expression"], "fear")
        for raw in ['{"expression":"fear","intensity":0.5', '{"expression":"rage","intensity":0.5,"gaze":"left"}',
                    '{"expression":"fear","intensity":2,"gaze":"left"}',
                    '{"expression":"fear","intensity":0.5,"gaze":"left","shapes":[]}', '[]']:
            with self.subTest(raw):
                with self.assertRaises(DrawingError):
                    validate_plan(raw)

    def test_bounded_retries_then_fail_with_receipt(self):
        from studio.drawing import model
        calls = []

        def bad(prompt, **kw):
            calls.append(prompt)
            return {"message": {"content": '{"shapes": [{"id": "head silhouette"'}}  # truncated, as in take-001

        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(DrawingError):
                model.plan_expression("Amaia is afraid", tmp, retries=2, chat=bad)
            receipt = json.load(open(f"{tmp}/plan-receipt.json"))
        self.assertEqual(len(calls), 3)
        self.assertIsNone(receipt["plan"])
        self.assertEqual(len(receipt["attempts"]), 3)

    def test_recovers_on_retry_and_scales_intensity(self):
        from studio.drawing import model
        replies = iter(['not json', '{"expression":"fear","intensity":0.5,"gaze":"left"}'])
        chat = lambda prompt, **kw: {"message": {"content": next(replies)}}  # noqa: E731
        with tempfile.TemporaryDirectory() as tmp:
            plan, receipt = model.plan_expression("x", tmp, chat=chat)
        self.assertEqual(len(receipt["attempts"]), 2)
        expr = model.plan_to_expression(plan)
        full = model.plan_to_expression({**plan, "intensity": 1.0})
        self.assertAlmostEqual(expr["brow_inner"], full["brow_inner"] / 2, places=3)
        self.assertEqual(expr["gaze_x"], -1.0)


if __name__ == "__main__":
    unittest.main()


class FluxCommandTest(unittest.TestCase):
    def test_command_is_bounded_and_reference_conditioned(self):
        from studio.drawing import flux
        argv = flux.command("ref.png", "Amaia, three-quarter view", "out.png", root="/x")
        self.assertIn("-r", argv)
        self.assertEqual(argv[argv.index("-r") + 1], "ref.png")
        self.assertEqual(argv[argv.index("--steps") + 1], "4")
        for bad in ({"width": 500}, {"width": 4096, "height": 4096}, {"steps": 50}):
            with self.subTest(bad):
                with self.assertRaises(flux.FluxError):
                    flux.command("ref.png", "x", "out.png", root="/x", **bad)
        with self.assertRaises(flux.FluxError):
            flux.command("ref.png", "", "out.png", root="/x")

    def test_generate_refuses_without_backend_and_never_downloads(self):
        from studio.drawing import flux
        with tempfile.TemporaryDirectory() as tmp:
            self.assertFalse(flux.doctor(root=tmp)["ready"])
            with self.assertRaises(flux.FluxError):
                flux.generate("ref.png", "x", f"{tmp}/take", root=tmp)


class CliTest(unittest.TestCase):
    def test_help_for_every_command(self):
        import contextlib
        import io
        from studio.drawing.__main__ import main
        for command in ("extract", "face", "plan", "flux", "gate"):
            with self.subTest(command):
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf), self.assertRaises(SystemExit) as ctx:
                    main([command, "--help"])
                self.assertEqual(ctx.exception.code, 0)
                self.assertIn("usage", buf.getvalue())
