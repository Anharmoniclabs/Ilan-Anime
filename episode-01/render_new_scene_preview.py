#!/usr/bin/env python3
"""Render the first four seconds of the newly supplied night-canoe composition."""
import argparse
import json
from episode import ROOT, intake, render_shot


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='build/new-night-scene-take-01')
    args = parser.parse_args()
    out = ROOT/args.output
    out.mkdir(parents=True, exist_ok=True)
    video = out/'animation.mp4'
    if video.exists():
        raise SystemExit('Use a new take directory; existing previews are preserved.')
    data = intake()
    shot = dict(next(s for s in data['shots'] if s['id'] == 'S01-02'))
    shot['frames'] = 96
    plan = json.loads((ROOT/'data/new-night-scene-preview.json').read_text())
    (out/'preview-spec.json').write_text(json.dumps({'shot':shot, 'plan':plan},indent=2)+'\n')
    render_shot(shot, plan, video, 1440, 1080)
    (out/'index.html').write_text('''<!doctype html><meta charset="utf-8">
<meta name="viewport" content="width=device-width"><title>New night-canoe scene</title>
<style>body{background:#101921;color:#ede6d6;font:17px/1.6 system-ui;max-width:1100px;margin:32px auto;padding:20px}video{width:100%;max-height:80vh;background:black}a{color:#7fb7d6}</style>
<h1>Night journey through the mangroves</h1>
<p>First four seconds · 4:3 · 1440×1080 · 24 fps · silent motion preview.</p>
<video controls loop playsinline preload="metadata" poster="S01-02-middle.jpg" src="animation.mp4"></video>
<p>Eight paddle cels, independent background/camera movement, water motion and foreground roots.</p>
<p><a href="animation.mp4">Open video</a> · <a href="../../data/new-night-scene-preview.json">Animation settings</a></p>''')
    print(video)


if __name__ == '__main__': main()
