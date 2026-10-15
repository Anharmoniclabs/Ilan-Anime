"""Reproducible 168-frame bell mechanics blockout for S01-05.

Geometry only. THIS IS NOT AUTHOR ART, DRAWN PERFORMANCE, OR A FINISHED SHOT.
A cloud animator can use anchors as guides for character key drawings, and must
then validate actual observed positions from the rendered footage separately.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from studio.cloud_rig import (
    lock_hand_to_pole, solve_two_bone_ik, validate_action,
)

FRAMES = 168
FPS = 24
IMPACT_FRAMES = (86, 100, 112)


def ease(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


def pose(frame):
    if not 0 <= frame < FRAMES:
        raise ValueError("Frame outside S01-05 contract")
    lift = ease((frame - 20) / 48)
    settle = ease((frame - 124) / 35)
    angle_degrees = 5 - 38 * lift + 18 * settle
    if frame > 64:
        angle_degrees += 2.4 * math.sin(2 * math.pi * (frame - 64) / 11) * (1 - settle)
    angle = math.radians(angle_degrees)
    a = [480, 418 - 20 * lift + 7 * settle]
    b = [a[0] + 240 * math.cos(angle), a[1] + 240 * math.sin(angle)]
    hands, arms = {}, {}
    for side, grip, shoulder, bend in (
        ("left", .18, [472, 506], 1),
        ("right", .47, [522, 506], -1),
    ):
        hand = lock_hand_to_pole(a, b, grip)
        elbow = solve_two_bone_ik(shoulder, hand, 90, 105, bend=bend)
        hands[side] = {"point": hand, "grip_t": grip}
        arms[side] = {"shoulder": shoulder, "elbow": elbow, "wrist": hand}
    # Each impact is its own authored exact-frame contact: the clapper is
    # independently animated and otherwise separated from the bell rim.
    displacement = sum(
        (1 if impact != 100 else -1) * max(0.0, 1 - abs(frame - impact) / 4)
        for impact in IMPACT_FRAMES
    )
    bell = {"pivot": b, "clapper_anchor": [b[0], b[1] + 16],
            "rim": [[b[0] - 18, b[1] + 56], [b[0] + 18, b[1] + 56]]}
    return {
        "frame": frame,
        "pole": {"a": a, "b": b},
        "hands": hands,
        "arms": arms,
        "bell": bell,
        "clapper": {
            "hinge": bell["clapper_anchor"],
            "tip": [b[0] + 18 * displacement, b[1] + 56],
        },
    }


def build():
    measured = {
        "shot": "S01-05", "fps": FPS, "frames": FRAMES,
        "impact_frames": list(IMPACT_FRAMES),
        "poses": [pose(i) for i in range(FRAMES)],
        "note": "Procedural rig positions only; original artist cels, acting and sound are absent.",
    }
    checked = validate_action(measured)
    if not checked["mechanics_verified"]:
        raise ValueError(f"Mechanical blockout failed: {checked['errors']}")
    return measured, checked


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", required=True, help="New JSON destination; never overwrites existing files")
    args = p.parse_args(argv)
    out = Path(args.out)
    if out.exists():
        p.error("Output exists; use a different filename for each attempt")
    evidence, review = build()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    out.with_suffix(".validation.json").write_text(
        json.dumps(review, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "evidence": str(out),
        "measured_frames": 168,
        "mechanics_verified_in_procedural_blockout": True,
        "original_character_animation_verified": False,
        "final_eligible": False,
    }, indent=2))


if __name__ == "__main__":
    main()
