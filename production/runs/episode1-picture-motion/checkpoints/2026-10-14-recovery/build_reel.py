"""Package existing silent excerpts, without claiming complete episode coverage."""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[5]
RUN = ROOT / 'production/runs/episode1-picture-motion'
OUT = Path(__file__).resolve().parent
sources = [
    ('S00-01', 'editorial-motion/S00-01/native-v1/preview.mp4', 96),
    ('S00-02', 'editorial-motion/S00-02/native-v1/preview.mp4', 120),
    ('S01-01', 'water-motion/S01-01-silent-preview.mp4', 144),
    ('S01-15', 'editorial-motion/S01-15/native-v1/preview.mp4', 96),
    ('S02-01', 'editorial-motion/S02-01/native-v1/preview.mp4', 288),
    ('S14-03', 'research-graph/native-v1/preview.mp4', 384),
    ('S15-09', 'editorial-motion/S15-09/native-v1/preview.mp4', 192),
]

def probe(p):
    return json.loads(subprocess.check_output(['ffprobe', '-v', 'error',
        '-count_frames', '-show_streams', '-of', 'json', str(p)]))

rows = []
offset = 0
for shot, relative, frames in sources:
    source = RUN / 'tasks' / relative
    info = probe(source)
    video = next(s for s in info['streams'] if s['codec_type'] == 'video')
    assert int(video['nb_read_frames']) == frames
    assert video['r_frame_rate'] == '24/1'
    assert not any(s['codec_type'] == 'audio' for s in info['streams'])
    target = OUT / (shot + '.mp4')
    label = f'{shot} | SILENT DRAFT EXCERPT | NOT FULL EPISODE'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(source), '-an',
        '-vf', "scale=1280:720,setsar=1,drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:text='" + label + "':fontsize=18:fontcolor=white:box=1:boxcolor=black@0.85:x=16:y=16",
        '-r', '24', '-c:v', 'libx264', '-crf', '18', '-preset', 'fast',
        '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(target)], check=True)
    rows.append(dict(shot=shot, source=str(source.relative_to(ROOT)),
        source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        frames=frames, reel_start_frame=offset, review='draft; no final author approval'))
    offset += frames

(OUT / 'concat.txt').write_text(''.join(f"file '{shot}.mp4'\n" for shot, _, _ in sources))
reel = OUT / 'silent-motion-excerpts.mp4'
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0',
    '-i', str(OUT / 'concat.txt'), '-c', 'copy', '-an', '-movflags', '+faststart', str(reel)], check=True)
result = probe(reel)
assert int(result['streams'][0]['nb_read_frames']) == offset
subprocess.run(['ffmpeg', '-v', 'error', '-i', str(reel), '-f', 'null', '-'], check=True)
report = dict(status='partial picture checkpoint', fps=24, frames=offset,
    seconds=offset / 24, included_shots=len(rows), episode_shots=128,
    episode_frames=27120, omitted_shots=121, audio='none',
    newly_animated_shots_this_checkpoint=0,
    contents='Existing editorial, water and research-graph drafts; black cards are scripted black.',
    blocker='Independent reviewer process failed initializing Codex app-server client: read-only filesystem. Run paused; no retry.',
    amaia='Six saved raw replacement drawings; registration, compositing and review unfinished.',
    remaining='Character action drawings, registration, contacts, continuity cleanup, camera staging and full sequence review remain across the episode.',
    sources=rows, output_sha256=hashlib.sha256(reel.read_bytes()).hexdigest())
(OUT / 'coverage.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(dict(frames=offset, seconds=offset/24, shots=len(rows), output=str(reel))))
