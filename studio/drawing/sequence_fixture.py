"""Reproducible synthetic sleeve-motion fixture. NOT an Amaia character animation.

Run: python -m studio.drawing.sequence_fixture --out production/engineering/drawing-takes/SEPARATION-DEMO-001
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from studio.drawing.sequence import run


def line(a, b):
    return [list(a), [(2*a[0]+b[0])/3, (2*a[1]+b[1])/3],
            [(a[0]+2*b[0])/3, (a[1]+2*b[1])/3], list(b)]


def drawing(t):
    """Generate one clearly labeled synthetic sleeve key; one per real 24-fps frame."""
    gap = 9.0 + 20.0 * abs(math.cos(math.pi*t))
    sway = 24.0 * math.sin(2*math.pi*t)
    y = 172.0 + 15.0 * math.sin(2*math.pi*t)
    centers = [(175,y-14),(247,y-36+sway*.15),
               (351,y+18+sway*.23),(475,y+35+sway*.1)]
    upper = [[x, cy-gap/2] for x,cy in centers]
    lower = [[x, cy+gap/2] for x,cy in centers]
    return {"version":1,"canvas":[640,360],"status":"exploratory",
            "character":"synthetic.sleeve.fixture",
            "primitives":[
                {"id":"arm.sleeve", "kind":"fill", "provenance":"procedural",
                 "color":"#4b657b", "curve":[upper,line(upper[3],lower[3]),
                                              list(reversed(lower)),line(lower[0],upper[0])]},
                {"id":"arm.upper.ink", "kind":"stroke", "provenance":"procedural",
                 "color":"#192b38", "curve":[upper], "width":[3.5,5.5,3.5]},
                {"id":"arm.lower.ink", "kind":"stroke", "provenance":"procedural",
                 "color":"#192b38", "curve":[lower], "width":[3.5,5.5,3.5]}]}


def rules(minimum=28):
    fill=[{"upper":{"id":"arm.sleeve","segment":0,"point":k},
           "lower":{"id":"arm.sleeve","segment":2,"point":3-k},
           "minimum":minimum,"axis":[0,-1]} for k in range(4)]
    ink=[{"upper":{"id":"arm.upper.ink","segment":0,"point":k},
          "lower":{"id":"arm.lower.ink","segment":0,"point":k},
          "minimum":minimum,"axis":[0,-1]} for k in range(4)]
    return fill+ink


def demo(out, fps=24, frames=48, minimum=28.0):
    if not 2 <= frames <= 600 or not 1 <= fps <= 60 or not 0 <= minimum <= 200:
        raise ValueError('out-of-range fixture settings')
    out=Path(out).resolve()
    src=out.parent/(out.name+'-source-fixture')
    if (out.exists() and any(out.iterdir())) or (src.exists() and any(src.iterdir())):
        raise ValueError('refusing to overwrite a take or source fixture')
    src.mkdir(parents=True,exist_ok=True)
    files=[]
    for i in range(frames):
        name=f'pose-{i:04d}.drawing.json'
        (src/name).write_text(json.dumps(drawing(i/(frames-1)),indent=2)+'\n',encoding='utf-8')
        files.append({'drawing':name})
    manifest={'source_kind':'synthetic-fixture','approved':False,'fps':fps,
              'frames':files,'rules':rules(minimum)}
    (src/'sequence.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    return run(src/'sequence.json',out)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',required=True)
    p.add_argument('--fps',type=int,default=24)
    p.add_argument('--frames',type=int,default=48)
    p.add_argument('--minimum',type=float,default=28.0)
    a=p.parse_args()
    report=demo(a.out,a.fps,a.frames,a.minimum)
    print(json.dumps({k:v for k,v in report.items() if k!='frames'},indent=2))


if __name__=='__main__':
    main()
