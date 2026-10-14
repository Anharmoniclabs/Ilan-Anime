from pathlib import Path
import shutil
import subprocess
import tempfile
import types
import unittest
from unittest.mock import patch

from PIL import Image

from studio import video
from studio.paths import load_json, sha256, write_json


class VideoTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.ref = self.tmp / "reference.png"
        Image.new("RGB", (80, 80), "navy").save(self.ref)
        self.job = self.tmp / "job"

    def prepare(self, frames=48):
        return video.prepare("S01-02", self.ref, self.job, frames=frames)

    def test_inventory_preserves_every_frame(self):
        result = video.episode_plan()
        self.assertEqual(result["total_frames"], 27120)
        self.assertEqual(len(result["shots"]), 128)
        for shot in result["shots"]:
            offset = 0
            for segment in shot["segments"]:
                self.assertEqual(segment["offset"], offset)
                self.assertLessEqual(segment["frames"], 336)
                offset += segment["frames"]
            self.assertEqual(offset, shot["frames"])

    def test_reference_preserved_and_job_does_not_overwrite(self):
        original = sha256(self.ref)
        job = self.prepare()
        self.assertEqual(sha256(self.ref), original)
        self.assertEqual(job["expected_remote_frames"], 56)
        with Image.open(self.job / "first.png") as image:
            self.assertEqual(image.size, (1024, 576))
        with self.assertRaises(FileExistsError):
            self.prepare()

    def test_changed_reference_refused_before_network(self):
        self.prepare()
        Image.new("RGB", (16, 16), "red").save(self.job / "first.png")
        with self.assertRaises(video.VideoError):
            video.submit(self.job, client_factory=lambda _: self.fail("network called"))

    def test_out_of_shot_and_invalid_duration_refused(self):
        with self.assertRaises(video.VideoError):
            self.prepare(300)
        self.prepare()
        job = load_json(self.job / "job.json")
        job["request"]["duration"] = 14
        write_json(self.job / "job.json", job)
        with self.assertRaises(video.VideoError):
            video.submit(self.job)

    def fake_client(self, *, fail=False, drift=False):
        owner = self

        class Client:
            def view_api(self, **kwargs):
                names = set(load_json(owner.job / "job.json")["request"]) | {"image_path", "last_image_path"}
                return {"named_endpoints": {} if drift else {"/generate": {
                    "parameters": [{"parameter_name": n} for n in names]}}}

            def predict(self, **kwargs):
                if fail:
                    raise TimeoutError("lost acknowledgement")
                owner.assertEqual(kwargs["api_name"], "/generate")
                dest = owner.job / "downloads" / "output.mp4"
                dest.parent.mkdir()
                dest.write_bytes(b"test-only video stand-in")
                return str(dest), "provider report", ""

        return lambda _: (Client(), lambda p: {"path": p})

    def test_success_persisted_and_duplicate_submission_refused(self):
        self.prepare()
        result = video.submit(self.job, client_factory=self.fake_client())
        self.assertEqual(result["state"], "downloaded")
        self.assertEqual(result["source_sha256"], sha256(self.job / "source.mp4"))
        with self.assertRaises(video.VideoError):
            video.submit(self.job, client_factory=self.fake_client())

    def test_timeout_pauses_and_never_retries(self):
        self.prepare()
        with self.assertRaises(TimeoutError):
            video.submit(self.job, client_factory=self.fake_client(fail=True))
        self.assertEqual(load_json(self.job / "job.json")["state"], "paused")
        with self.assertRaises(video.VideoError):
            video.submit(self.job, client_factory=lambda _: self.fail("repeated submission"))

    def test_api_drift_pauses_before_generation(self):
        self.prepare()
        with self.assertRaises(video.VideoError):
            video.submit(self.job, client_factory=self.fake_client(drift=True))
        self.assertFalse((self.job / "source.mp4").exists())

    def test_client_explicitly_disables_cached_authentication(self):
        seen = {}

        class Client:
            def __init__(self, src, token=None, **kwargs):
                seen.update(src=src, token=token)
                self.headers = {}

        module = types.SimpleNamespace(Client=Client, handle_file=lambda p: p)
        with patch.dict("sys.modules", {"gradio_client": module}):
            video._client(self.job)
        self.assertIs(seen["token"], False)
        self.assertEqual(seen["src"], video.SPACE_URL)

    def test_unexpected_authorization_header_refused(self):
        class Client:
            def __init__(self, src, token=None, **kwargs):
                self.headers = {"x-hf-authorization": "must-not-be-used"}

        module = types.SimpleNamespace(Client=Client, handle_file=lambda p: p)
        with patch.dict("sys.modules", {"gradio_client": module}):
            with self.assertRaises(video.VideoError):
                video._client(self.job)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg required")
    def test_actual_clip_import_and_draft_render(self):
        self.prepare(frames=4)
        clip = self.tmp / "test.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i",
                        "testsrc2=size=160x90:rate=24", "-frames:v", "6", "-threads", "1",
                        "-pix_fmt", "yuv420p", str(clip)], check=True)
        result = video.import_clip(self.job, clip)
        spec = load_json(result["spec"])
        self.assertEqual(spec["frames"], 4)
        self.assertEqual(spec["status"], "exploratory")
        self.assertEqual(spec["camera"], [])
        self.assertIsNone(spec["audio"])
        from studio.render import export_shot
        from studio.engine.io import ExportError
        with self.assertRaises(ExportError):
            export_shot(spec, self.tmp / "final.mp4")
        output = export_shot(spec, self.tmp / "draft.mp4", draft=True)
        self.assertEqual(output["frames"], 4)
        self.assertTrue(output["draft"])
        with self.assertRaises(FileExistsError):
            video.import_clip(self.job, clip)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg required")
    def test_short_clip_refused_without_freezing(self):
        self.prepare(frames=48)
        clip = self.tmp / "short.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i",
                        "color=size=16x16:rate=24", "-frames:v", "2", "-threads", "1", str(clip)], check=True)
        with self.assertRaises(video.VideoError):
            video.import_clip(self.job, clip)


if __name__ == "__main__":
    unittest.main()
