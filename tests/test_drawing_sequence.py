"""End-to-end 24 fps separation correction on distinct synthetic draft cels."""
import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from studio.drawing.sequence import run
from studio.motion import compile_spec, MotionError


def _line(a,b):
    return [list(a),[(2*a[0]+b[0])/3,(2*a[1]+b[1])/3],
            [(a[0]+2*b[0])/3,(a[1]+2*b[1])/3],list(b)]


def _frame(gap, sway):
    upper=[[25,35-gap/2],[45,30-gap/2+sway],[75,35-gap/2+sway],[95,35-gap/2]]
    lower=[[x,y+gap] for x,y in upper]
    curve=[upper,_line(upper[3],lower[3]),list(reversed(lower)),_line(lower[0],upper[0])]
    return {"version":1,"canvas":[128,80],"primitives":[
        {"id":"cloth.sleeve","kind":"fill","provenance":"procedural",
         "color":"#52758c","opacity":1.0,"curve":curve}]}


def _rules(m=18):
    return [{"upper":{"id":"cloth.sleeve","segment":0,"point":k},
             "lower":{"id":"cloth.sleeve","segment":2,"point":3-k},
             "minimum":m,"axis":[0,-1]} for k in range(4)]


class EndToEndTest(unittest.TestCase):
    def test_corrects_timed_drawings_non_destructively(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            src=root/"input"
            src.mkdir()
            original=[]
            frames=[]
            for i in range(10):
                d=_frame(6+2*i,1 if i%2 else 0)
                p=src/f"{i:04d}.drawing.json"
                p.write_text(json.dumps(d))
                original.append(p.read_bytes())
                frames.append({"drawing":p.name})
            manifest=src/"sequence.json"
            manifest.write_text(json.dumps({
                "source_kind":"synthetic-fixture","fps":24,
                "frames":frames,"rules":_rules()}))
            report=run(manifest,root/"out")
            self.assertEqual(report["frame_count"],10)
            self.assertGreater(report["original_violating_frames"],0)
            self.assertEqual(report["after_violating_frames"],0)
            self.assertTrue(report["midpoints_preserved"])
            self.assertEqual([p.read_bytes() for p in sorted(src.glob("*.drawing.json"))],original)
            before=json.loads((root/"out"/"before-motion.json").read_text())
            after=json.loads((root/"out"/"after-motion.json").read_text())
            self.assertEqual(len(after["elements"][0]["separation_constraints"]),4)
            with self.assertRaises(MotionError):
                compile_spec(before)
            compiled=compile_spec(after)
            self.assertEqual(compiled["fps"],24)
            self.assertEqual(len(compiled["layers"][0]["sequence"]),10)
            if shutil.which("ffmpeg"):
                self.assertTrue((root/"out"/"comparison.mp4").is_file())
            self.assertTrue((root/"out"/"measurement.png").is_file())

    def test_rejects_approved_sources_and_overwrites(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            d=_frame(6,0)
            d["approved"]=True
            original=root/"input.json"
            original.write_text(json.dumps(d))
            manifest=root/"sequence.json"
            manifest.write_text(json.dumps({
                "frames":[{"drawing":"input.json"}],"rules":_rules()}))
            with self.assertRaisesRegex(ValueError,"approved drawing"):
                run(manifest,root/"out")
            out=root/"existing"
            out.mkdir()
            (out/"keep.txt").write_text("safe")
            with self.assertRaisesRegex(ValueError,"overwrite"):
                run(manifest,out)
            self.assertEqual((out/"keep.txt").read_text(),"safe")


if __name__=="__main__":
    unittest.main()
