# SPDX-License-Identifier: CC-BY-4.0
# © 2026 Design House (https://designhouse.me)
"""Integration tests of actual final-file decoding and evidence, no browser or Pillow."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/motion-design/scripts/review_frames.py"


def frame(kind):
    pixels = bytearray()
    for y in range(36):
        for x in range(64):
            if kind == "black":
                color = (0, 0, 0)
            elif kind == "white":
                color = (255, 255, 255)
            elif kind == "a":
                color = (240, 180, 80) if x < 32 else (20, 30, 90)
            else:
                color = (20, 90, 30) if y < 18 else (240, 90, 200)
            pixels.extend(color)
    return bytes(pixels)


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "ffmpeg and ffprobe required")
class MotionReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="motion-review-test-")
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def film(self, kinds, name="film.mp4", fps="10"):
        path = self.root / name
        result = subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", "-y", "-f", "rawvideo",
                                 "-pixel_format", "rgb24", "-video_size", "64x36", "-framerate", fps,
                                 "-i", "pipe:0", "-an", "-c:v", "libx264", "-threads", "1", "-crf", "0",
                                 "-pix_fmt", "yuv444p", "-movflags", "+faststart", str(path)],
                                input=b"".join(frame(k) for k in kinds), capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr.decode())
        return path

    def review(self, film, contract=None, legacy=False, out="review"):
        outdir = self.root / out
        cmd = [sys.executable, str(SCRIPT), "--film", str(film), "--outdir", str(outdir), "--timeout", "30"]
        if contract is not None:
            source = self.root / "timeline.json"
            source.write_text(json.dumps(contract))
            cmd += ["--cues" if legacy else "--timeline", str(source)]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        self.assertTrue((outdir / "review.json").is_file(), proc.stderr)
        return proc.returncode, json.loads((outdir / "review.json").read_text()), outdir

    def test_declared_cut_and_still_holds_are_not_anomalies(self):
        film = self.film(["a"] * 10 + ["b"] * 10)
        code, report, out = self.review(film, {"fps": 10, "durationFrames": 20, "cuts": [1], "cues": []})
        self.assertEqual(code, 0)
        self.assertEqual(report["status"], "passed", report)
        self.assertFalse(any(f["code"] == "isolated_temporal_outlier" for f in report["findings"]))
        self.assertTrue(report["coverage"]["all_frames_decoded"])
        self.assertEqual(report["coverage"]["decoded_frames"], 20)
        self.assertTrue({9, 10, 11}.issubset({c["frame"] for c in report["candidates"]}))
        self.assertEqual(report["checks"]["visual_inspection"], "not_checked")
        for sheet in report["sheets"]:
            self.assertEqual(hashlib.sha256((out / sheet["path"]).read_bytes()).hexdigest(), sheet["sha256"])

    def test_isolated_blank_anywhere_is_detected_from_actual_video(self):
        film = self.film(["a"] * 17 + ["black"] + ["a"] * 12)
        code, report, _ = self.review(film)
        self.assertEqual(code, 0)
        self.assertEqual(report["status"], "warning")
        blank = [f for f in report["findings"] if f["code"] == "black_frames"]
        self.assertEqual([(f["first_frame"], f["last_frame"]) for f in blank], [(17, 17)])
        self.assertAlmostEqual(blank[0]["t"], 1.7)
        self.assertTrue(any(f["code"] == "isolated_temporal_outlier" for f in report["findings"]))
        self.assertEqual(report["coverage"]["timestamped_frames"], 30)

    def test_flash_can_be_a_declared_cut_without_temporal_warning(self):
        film = self.film(["a"] * 10 + ["white"] + ["a"] * 9)
        cues = {"duration": 2, "cues": [{"id": "flash-in", "t": 1, "type": "cut"},
                                         {"id": "flash-out", "t": 1.1, "type": "cut"},
                                         {"id": "hold", "t": 0, "d": 1, "type": "hold"}]}
        code, report, _ = self.review(film, cues, legacy=True)
        self.assertEqual(code, 0)
        self.assertTrue(any(f["code"] == "declared_cut_transition" and f["status"] == "passed" for f in report["findings"]))
        self.assertFalse(any(f["code"] == "isolated_temporal_outlier" for f in report["findings"]))
        # Uniform white still requires human judgement; cut declarations don't certify content.
        self.assertTrue(any(f["code"] == "uniform_frames" for f in report["findings"]))

    def test_truncated_corrupt_and_audio_only_fail_and_replace_old_report(self):
        good = self.film(["a", "b"] * 15)
        self.assertEqual(self.review(good)[0], 0)
        truncated = self.root / "truncated.mp4"
        data = good.read_bytes()
        truncated.write_bytes(data[:int(len(data) * 0.75)])
        corrupt = self.root / "corrupt.mp4"
        corrupt.write_bytes(b"not a video")
        audio = self.root / "audio.wav"
        subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=8000:cl=mono",
                        "-t", "0.1", str(audio)], check=True, capture_output=True)
        for path in (truncated, corrupt, audio):
            with self.subTest(path=path.name):
                code, report, _ = self.review(path)
                self.assertNotEqual(code, 0)
                self.assertEqual(report["status"], "failed")
                self.assertEqual(report["sheets"], [])
                self.assertTrue(any(f["code"] == "review_incomplete" for f in report["findings"]))
                self.assertEqual(report["artifact"]["sha256"], hashlib.sha256(path.read_bytes()).hexdigest())

    def test_legacy_top_level_cuts_are_preserved(self):
        film = self.film(["a"] * 10 + ["white"] + ["a"] * 9)
        code, report, _ = self.review(film, {"duration": 2, "cuts": [1, 1.1], "cues": []}, legacy=True)
        self.assertEqual(code, 0)
        self.assertEqual(report["timeline"]["cuts"], [1, 1.1])
        self.assertTrue(any(f["code"] == "declared_cut_transition" for f in report["findings"]))

    def test_report_hash_tracks_replaced_final_artifact(self):
        path = self.film(["a"] * 12)
        code, before, _ = self.review(path)
        self.assertEqual(code, 0)
        self.film(["b"] * 12)
        code, after, _ = self.review(path)
        self.assertEqual(code, 0)
        self.assertNotEqual(before["artifact"]["sha256"], after["artifact"]["sha256"])
        self.assertEqual(after["artifact"]["sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertNotEqual(before["sheets"][0]["path"], after["sheets"][0]["path"])

    def test_timestamp_strip_is_legible_independently_of_source_brightness(self):
        strips = []
        for kind in ("black", "white"):
            film = self.film([kind] * 12, name=f"{kind}.mp4")
            code, report, out = self.review(film, out=f"review-{kind}")
            self.assertEqual(code, 0)
            self.assertEqual(report["candidates"][0]["t"], 0)
            sheet = out / report["sheets"][0]["path"]
            # Decode published evidence, not intermediate images or the filter string.
            # Both first cells say 00:00:00.000, despite opposite source brightness.
            crop = subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", "-i", str(sheet),
                                   "-vf", "crop=320:28:4:4,format=gray", "-frames:v", "1",
                                   "-f", "rawvideo", "pipe:1"], capture_output=True, check=True)
            self.assertEqual(len(crop.stdout), 320 * 28)
            mask = [value > 128 for value in crop.stdout]
            self.assertGreater(sum(mask), 150, "Timestamp glyphs must actually be visible")
            self.assertLess(sum(mask), 1000, "The label strip must remain dark around the text")
            strips.append(mask)
            # The source thumbnail below the strip remains unobscured.
            sample = subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", "-i", str(sheet),
                                     "-vf", "crop=16:16:244:100,format=gray", "-frames:v", "1",
                                     "-f", "rawvideo", "pipe:1"], capture_output=True, check=True)
            average = sum(sample.stdout) / len(sample.stdout)
            if kind == "black":
                self.assertLess(average, 10)
            else:
                self.assertGreater(average, 245)
        # JPEG ringing can alter edge pixels; the glyph silhouettes must agree.
        self.assertLess(sum(a != b for a, b in zip(*strips)), 15)

    def test_timestamp_strips_do_not_retain_digits_from_earlier_frames(self):
        film = self.film(["white"] * 30)
        code, report, out = self.review(film, {"cuts": [n / 10 for n in range(1, 29)], "cues": []})
        self.assertEqual(code, 0)
        self.assertEqual(len(report["sheets"]), 3)
        # Compare late-page evidence with independent one-frame static labels.
        # This catches stale glyphs in reused FFmpeg padding buffers without
        # relying on OCR or duplicating the stateful select/pad/tile pipeline.
        for frame_number in (12, 17, 24, 29):
            candidate = next(c for c in report["candidates"] if c["frame"] == frame_number)
            sheet = out / report["sheets"][candidate["page"] - 1]["path"]
            cell = candidate["cell"] - 1
            x, y = 4 + (cell % 4) * 324, 4 + (cell // 4) * 212
            actual = subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", "-i", str(sheet),
                                     "-vf", f"crop=320:28:{x}:{y},format=gray", "-frames:v", "1",
                                     "-f", "rawvideo", "pipe:1"], capture_output=True, check=True)
            expected = subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", "-f", "lavfi",
                                       "-i", "color=black:s=320x28",
                                       "-vf", f"drawtext=text='00\\:00\\:{frame_number / 10:06.3f}':"
                                       "x=6:y=6:fontsize=16:fontcolor=white,format=gray",
                                       "-frames:v", "1", "-f", "rawvideo", "pipe:1"], capture_output=True, check=True)
            self.assertEqual(len(actual.stdout), len(expected.stdout))
            # Allow JPEG edge ringing, but not residual strokes from old digits.
            mismatch = sum((a > 128) != (b > 128) for a, b in zip(actual.stdout, expected.stdout))
            self.assertLess(mismatch / sum(v > 128 for v in expected.stdout), 0.12,
                            f"Timestamp for frame {frame_number} contains missing or extra glyph pixels")

    def test_variable_frame_rate_uses_decoded_timestamps(self):
        original = self.film(["a"] * 12 + ["black"] + ["a"] * 7)
        vfr = self.root / "variable.mp4"
        subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", "-i", str(original),
                        "-vf", "setpts=if(lt(N\\,10)\\,N/(10*TB)\\,(N+10)/(10*TB))",
                        "-fps_mode", "vfr", "-c:v", "libx264", "-threads", "1", "-crf", "0", str(vfr)],
                       check=True, capture_output=True)
        code, report, _ = self.review(vfr)
        self.assertEqual(code, 0)
        self.assertEqual(report["coverage"]["decoded_frames"], 20)
        self.assertTrue(report["coverage"]["variable_frame_intervals"])
        blank = next(f for f in report["findings"] if f["code"] == "black_frames")
        self.assertEqual(blank["first_frame"], 12)
        self.assertAlmostEqual(blank["t"], 2.2)

    def test_timeline_for_different_artifact_fails(self):
        film = self.film(["a"] * 15)
        code, report, _ = self.review(film, {"fps": 10, "durationFrames": 30, "cues": []})
        self.assertNotEqual(code, 0)
        self.assertEqual(report["status"], "failed")
        self.assertIn("expects 30", report["findings"][-1]["evidence"])

    def test_pages_and_evidence_are_bounded_but_scan_covers_every_frame(self):
        film = self.film(["a", "black"] * 130)
        code, report, out = self.review(film)
        self.assertEqual(code, 0)
        self.assertTrue(report["coverage"]["all_frames_decoded"])
        self.assertEqual(report["coverage"]["decoded_frames"], 260)
        self.assertLessEqual(len(report["candidates"]), 96)
        self.assertLessEqual(len(report["sheets"]), 8)
        self.assertGreater(report["omitted"]["findings"], 0)
        self.assertTrue({0, 259}.issubset({c["frame"] for c in report["candidates"]}))
        self.assertEqual(len(list(out.glob("*.jpg"))), len(report["sheets"]))
        code2, repeat, _ = self.review(film)
        self.assertEqual(code2, 0)
        self.assertEqual(report["candidates"], repeat["candidates"])


if __name__ == "__main__":
    unittest.main()
