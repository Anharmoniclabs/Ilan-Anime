"""Frame writers: lossless masters, tagged review copies, PNG sequences.

* ``master``  FFV1 RGB in Matroska. Lossless; use for intermediates and edit.
* ``review``  H.264 yuv420p with explicit BT.709 matrix/tags so the navy/amber
              palette doesn't shift between players. Never use for masters.
* ``frames``  numbered PNGs (``0000.png``...).
"""
from __future__ import annotations

from pathlib import Path
import shutil
import subprocess

from PIL import Image, ImageDraw

from studio.engine.fx import font
from studio.paths import timecode

READY_STATUSES = {"animation_ready", "approved", "author-approved", "canonical"}


class ExportError(RuntimeError):
    pass


def ffmpeg_bin():
    path = shutil.which("ffmpeg")
    if not path:
        raise ExportError("ffmpeg not found on PATH")
    return path


def burn_in(image: Image.Image, shot_id: str, frame: int, absolute: int | None = None, label=None):
    """Debug overlay: shot ID, local frame, episode timecode and a label."""
    draw = ImageDraw.Draw(image)
    h = image.height
    fnt = font("mono", max(10, int(16 * h / 720)))
    text = f"{shot_id}  f{frame:04d}"
    if absolute is not None:
        text += f"  {timecode(absolute)}"
    if label:
        text += f"  {label}"
    box = draw.textbbox((0, 0), text, font=fnt)
    pad = 6
    draw.rectangle([0, h - (box[3] - box[1]) - 3 * pad, box[2] + 2 * pad, h], fill=(0, 0, 0))
    draw.text((pad, h - (box[3] - box[1]) - 2 * pad), text, font=fnt, fill=(237, 230, 214))
    return image


class Writer:
    """Context manager accepting PIL RGB frames."""

    def __init__(self, out, size, mode="review", fps=24, audio=None, duration=None):
        self.out = Path(out)
        self.size = tuple(size)
        self.mode = mode
        self.count = 0
        self.out.parent.mkdir(parents=True, exist_ok=True)
        self.proc = None
        if mode == "frames":
            self.out.mkdir(parents=True, exist_ok=True)
            return
        w, h = self.size
        cmd = [ffmpeg_bin(), "-hide_banner", "-loglevel", "error", "-y",
               "-f", "rawvideo", "-pixel_format", "rgb24", "-video_size", f"{w}x{h}",
               "-framerate", str(fps), "-i", "pipe:0"]
        if audio:
            cmd += ["-i", str(audio)]
        if mode == "master":
            cmd += ["-c:v", "ffv1", "-level", "3", "-pix_fmt", "gbrp", "-g", "1"]
            if audio:
                cmd += ["-c:a", "pcm_s24le"]
        elif mode == "review":
            cmd += ["-vf", "scale=out_color_matrix=bt709:out_range=tv",
                    "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p",
                    "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
                    "-color_range", "tv", "-movflags", "+faststart"]
            if audio:
                cmd += ["-c:a", "aac", "-b:a", "192k"]
        else:
            raise ExportError(f"unknown mode {mode}")
        if audio and duration:
            cmd += ["-af", "apad", "-t", f"{duration:.6f}"]
        cmd.append(str(self.out))
        self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    def write(self, image: Image.Image):
        if image.size != self.size or image.mode != "RGB":
            raise ExportError("frame size/mode mismatch")
        if self.mode == "frames":
            image.save(self.out / f"{self.count:04d}.png", compress_level=3)
        else:
            self.proc.stdin.write(image.tobytes())
        self.count += 1

    def close(self):
        if self.proc is not None:
            self.proc.stdin.close()
            if self.proc.wait():
                raise ExportError(f"ffmpeg failed writing {self.out}")
            self.proc = None

    def __enter__(self):
        return self

    def __exit__(self, kind, value, tb):
        if self.proc is not None and kind is not None:
            self.proc.kill()
            self.proc = None
            return False
        self.close()
        return False


def probe_frames(path) -> int:
    """Count decoded frames (ffprobe)."""
    probe = shutil.which("ffprobe")
    if not probe:
        raise ExportError("ffprobe not found on PATH")
    result = subprocess.run([probe, "-v", "error", "-select_streams", "v:0", "-count_frames",
                             "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0", str(path)],
                            capture_output=True, text=True, check=True)
    return int(result.stdout.strip().split(",")[0])
