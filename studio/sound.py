"""Sound tools: dialogue extraction, mouth exposures, and the mix.

* ``lines``  pulls every quoted line from the script with its shot, frame range
             and a speaker guess (marked ``speaker_inferred`` until the script
             supervisor confirms it). This is the voice department's worklist.
* ``mouth``  turns a recorded take into a 3-drawing mouth flap (closed / narrow /
             open) on the shot's exposure rate; lips close on pauses.
* ``mix``    places stems at frame offsets with gain/pan, sums, normalizes to a
             loudness target and reports measured loudness and peak.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import wave

import numpy as np

from studio.engine.io import ffmpeg_bin
from studio.paths import EPISODE, load_json, rel, resolve, write_json

QUOTE = re.compile(r"“([^”]+)”|\"([^\"]+)\"")
CAST = ["Mr. Rodríguez", "Rodríguez", "Mamá", "Manny", "Sofía", "Abuela", "Amaia", "Dairon", "Yara", "Beheto",
        "Vale", "Mikey", "JC", "son", "counterman", "kid", "thin man", "ledger man", "soldier"]
SPEAKER = re.compile(r"(?:^|[.;]\s+|\s)(VO\s+)?([A-ZÁÉÍÓÚÑ][\w.áéíóúñ’']+(?:\s[A-ZÁÉÍÓÚÑ][\w.áéíóúñ’']+){0,2})"
                     r"(?:\s*\([^)]*\))?(?:,[^:“]{0,40})?:\s*$")
NON_SPEAKERS = {"Action", "Sound", "FX", "Super", "Lower", "Small", "Cream", "Then", "Present", "Before"}


def lines(shots=None):
    """Dialogue worklist from episode.json."""
    episode = load_json(EPISODE)
    out = []
    for shot in episode["shots"]:
        if shots and shot["id"] not in shots:
            continue
        n = 0
        for field in ("Action", "Sound"):
            m = re.search(rf"\*\*{field}:\*\*\s*(.*)", shot["script"])
            if not m:
                continue
            text = m.group(1)
            for q in QUOTE.finditer(text):
                line = (q.group(1) or q.group(2)).strip()
                if len(line) < 2:
                    continue
                before = text[:q.start()].rstrip()
                speaker, inferred = None, True
                sm = SPEAKER.search(before[-80:])
                if sm and sm.group(2).split()[0] not in NON_SPEAKERS:
                    speaker = sm.group(2)
                    inferred = sm.group(2) not in CAST
                if speaker is None:
                    # nearest cast name since the previous closing quote, same paragraph
                    tail = before[before.rfind("”") + 1:][-140:]
                    hits = [(tail.rfind(name), name) for name in CAST if tail.rfind(name) >= 0]
                    if hits:
                        speaker = max(hits)[1]
                n += 1
                out.append({"id": f"{shot['id']}-L{n:02d}", "shot": shot["id"], "text": line,
                            "speaker": speaker, "speaker_inferred": speaker is None or inferred,
                            "voiceover": bool(sm and sm.group(1)), "field": field.lower(),
                            "shot_start_frame": shot["start_frame"], "shot_frames": shot["frames"],
                            "max_seconds": round(shot["frames"] / 24, 2)})
    return out


def read_wav(path):
    with wave.open(str(path)) as w:
        rate, channels, width = w.getframerate(), w.getnchannels(), w.getsampwidth()
        raw = w.readframes(w.getnframes())
    dtype = {1: np.uint8, 2: np.int16, 4: np.int32}.get(width)
    if dtype is None:  # 24-bit
        data = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3)
        ints = (data[:, 0].astype(np.int32) | (data[:, 1].astype(np.int32) << 8) | (data[:, 2].astype(np.int32) << 16))
        ints = np.where(ints & 0x800000, ints - 0x1000000, ints)
        samples = ints.astype(np.float32) / 0x800000
    else:
        samples = np.frombuffer(raw, dtype=dtype).astype(np.float32)
        samples = (samples - 128) / 128 if dtype is np.uint8 else samples / np.iinfo(dtype).max
    return samples.reshape(-1, channels).mean(axis=1), rate


def mouth(take, rate_frames=3, offset_frames=0, drawings=None, silence_db=-42.0):
    """Recorded take -> mouth exposures [{start, end, source}] (shot-relative)."""
    drawings = drawings or {"closed": "mouth_closed.png", "narrow": "mouth_narrow.png", "open": "mouth_open.png"}
    samples, sr = read_wav(take)
    per_frame = sr / 24
    n_frames = int(np.ceil(len(samples) / per_frame))
    rms = np.array([np.sqrt(np.mean(samples[int(i * per_frame):int((i + 1) * per_frame)] ** 2) + 1e-12)
                    for i in range(n_frames)])
    db = 20 * np.log10(rms + 1e-9)
    voiced = db > silence_db
    loud = db[voiced]
    lo, hi = (np.percentile(loud, 35), np.percentile(loud, 70)) if loud.size else (0, 0)
    exposures = []
    for start in range(0, n_frames, rate_frames):
        window = db[start:start + rate_frames]
        if not (window > silence_db).any():
            shape = "closed"
        else:
            level = window.max()
            shape = "open" if level >= hi else ("narrow" if level >= lo else "closed")
        s, e = start + offset_frames, min(start + rate_frames, n_frames) + offset_frames
        if exposures and exposures[-1]["shape"] == shape:
            exposures[-1]["end"] = e
        else:
            exposures.append({"start": s, "end": e, "shape": shape, "source": drawings[shape]})
    return {"take": rel(take), "frames": n_frames, "rate": rate_frames, "exposures": exposures,
            "note": "Mouth timing from amplitude only; refine consonants and expression by hand."}


def mix(spec, out):
    """spec: {sample_rate, frames, loudness_lufs, tracks: [{file, start_frame, gain_db, pan, label}]}"""
    sr = int(spec.get("sample_rate", 48000))
    frames = int(spec["frames"])
    duration = frames / 24
    tracks = spec.get("tracks", [])
    if not tracks:
        raise ValueError("mix needs at least one track")
    cmd = [ffmpeg_bin(), "-hide_banner", "-loglevel", "error", "-y"]
    graph = []
    for i, track in enumerate(tracks):
        cmd += ["-i", str(resolve(track["file"]))]
        delay = int(round(int(track.get("start_frame", 0)) / 24 * 1000))
        gain = float(track.get("gain_db", 0))
        pan = float(track.get("pan", 0))
        left, right = min(1.0, 1 - pan), min(1.0, 1 + pan)
        graph.append(f"[{i}:a]aresample={sr},aformat=channel_layouts=stereo,"
                     f"pan=stereo|c0={left:.3f}*c0|c1={right:.3f}*c1,"
                     f"adelay={delay}|{delay},volume={gain}dB[a{i}]")
    target = float(spec.get("loudness_lufs", -24))
    graph.append("".join(f"[a{i}]" for i in range(len(tracks))) +
                 f"amix=inputs={len(tracks)}:normalize=0,apad,atrim=0:{duration:.6f},"
                 f"loudnorm=I={target}:TP=-2:LRA=11,aresample={sr}[out]")
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd += ["-filter_complex", ";".join(graph), "-map", "[out]", "-c:a", "pcm_s24le", "-ar", str(sr), str(out)]
    subprocess.run(cmd, check=True)
    measured = measure(out)
    report = {"output": rel(out), "duration_s": round(duration, 3), "sample_rate": sr,
              "target_lufs": target, **measured, "tracks": [t.get("label", t["file"]) for t in tracks]}
    write_json(out.with_suffix(".mix.json"), report)
    return report


def measure(path):
    """Integrated loudness and true peak via ffmpeg ebur128."""
    result = subprocess.run([ffmpeg_bin(), "-hide_banner", "-nostats", "-i", str(path),
                             "-filter_complex", "ebur128=peak=true", "-f", "null", "-"],
                            capture_output=True, text=True)
    text = result.stderr
    integrated = re.findall(r"I:\s+(-?[\d.]+) LUFS", text)
    peak = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", text)
    return {"integrated_lufs": float(integrated[-1]) if integrated else None,
            "true_peak_dbfs": float(peak[-1]) if peak else None}
