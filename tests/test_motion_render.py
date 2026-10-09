"""Browser/encoder regressions. Requires Node 22+, Chromium, ffmpeg and ffprobe.

Run: python3 -m unittest discover -s tests -p 'test_motion_render.py' -v
All renders live in temporary directories; no npm packages or network are used.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import signal
import struct
import subprocess
import tempfile
import time
import unittest
import wave


ROOT = Path(__file__).resolve().parents[1]
RENDER = ROOT / "skills/motion-design/scripts/render.mjs"
COMPILER = ROOT / "skills/motion-design/scripts/compile_timeline.py"


@unittest.skipUnless(all(shutil.which(x) for x in ("node", "ffmpeg", "ffprobe")), "media tools required")
class RenderTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="dh-motion-test-")
        self.work = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def page(self, render, *, duration=.4, extra="", name="film.html"):
        path = self.work / name
        path.write_text(f'''<!doctype html><html><body style="margin:0;background:black">
<script>window.__SIZE={{w:64,h:64}};window.__DURATION={duration};window.__SUB=1;
window.__ready=Promise.resolve();{extra}
window.__render={render};</script></body></html>''')
        return path

    def run_render(self, src, *args, ok=True):
        p = subprocess.run(["node", str(RENDER), "--src", str(src), "--fps", "10", "--workers", "1",
                            "--timeout", "5000", *args], capture_output=True, text=True, timeout=90)
        if ok:
            self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        else:
            self.assertNotEqual(p.returncode, 0, p.stdout + p.stderr)
        return p

    def rgb(self, path):
        p = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                           capture_output=True, check=True, timeout=20)
        return p.stdout

    def probe(self, path):
        return json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-count_frames", "-show_streams",
                                                  "-show_format", "-of", "json", str(path)]))

    def test_invalid_parameters_fail_before_browser(self):
        src = self.page("t => {}")
        for args in (("--fps", "30000/1001"), ("--workers", "0"), ("--sub", "1.5"),
                     ("--shutter", "1.1"), ("--from", "-1"), ("--still", "NaN"), ("--audio",)):
            # No defaults duplicated: validation should not need a working browser.
            p = subprocess.run(["node", str(RENDER), "--src", str(src), "--chrome", "/missing/chrome", *args],
                               capture_output=True, text=True)
            self.assertEqual(p.returncode, 2, p.stderr)
            self.assertNotIn("spawn", p.stderr)

    def test_async_render_finishes_before_capture(self):
        src = self.page("async t => { await new Promise(r=>setTimeout(r,45)); document.body.style.background='rgb(0,255,0)'; }")
        self.run_render(src, "--still", "0.2")
        rgb = self.rgb(next((self.work / "out/stills").glob("*.png")))
        self.assertEqual(rgb[:3], bytes((0, 255, 0)))

    def test_async_ready_can_install_render_before_capture(self):
        src = self.page("undefined", extra="""window.__ready = new Promise(resolve => setTimeout(() => {
            window.__render = t => {document.body.style.background='rgb(0,0,255)'};
            resolve();
        }, 45));""")
        self.run_render(src, "--still", "0.2")
        rgb = self.rgb(next((self.work / "out/stills").glob("*.png")))
        self.assertEqual(rgb[:3], bytes((0, 0, 255)))

    def test_async_failure_does_not_replace_previous_master(self):
        src = self.page("async t => { if(t>.1) throw new Error('failed seek'); }")
        out = self.work / "out"
        out.mkdir()
        master = out / "film.mp4"
        master.write_bytes(b"previous master")
        p = self.run_render(src, ok=False)
        self.assertIn("failed seek", p.stderr)
        self.assertEqual(master.read_bytes(), b"previous master")

    def test_cut_does_not_blend_previous_scene(self):
        src = self.page("t => {document.body.style.background=t<.1?'white':'black'}",
                        duration=.2, extra="window.__CUTS=[.1];")
        self.run_render(src, "--sub", "5")
        rgb = self.rgb(self.work / "out/film.mp4")
        stride = 64 * 64 * 3
        self.assertEqual(len(rgb), stride * 2)
        self.assertGreater(min(rgb[:stride]), 245)
        self.assertLess(max(rgb[stride:]), 8, "hard cut was mixed with outgoing white scene")

    def test_short_audio_and_fragment_keep_video_length(self):
        src = self.page("t => {document.body.style.background='navy'}", duration=.6)
        audio = self.work / "short.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono",
                        "-t", "0.1", str(audio)], check=True)
        self.run_render(src, "--audio", str(audio))
        info = self.probe(self.work / "out/film.mp4")
        video = next(s for s in info["streams"] if s["codec_type"] == "video")
        self.assertEqual(int(video["nb_read_frames"]), 6)
        self.assertAlmostEqual(float(video["duration"]), .6, places=3)
        self.assertTrue(any(s["codec_type"] == "audio" for s in info["streams"]))
        self.run_render(src, "--audio", str(audio), "--from", ".2", "--to", ".5", "--out", "fragment.mp4")
        info = self.probe(self.work / "out/fragment.mp4")
        self.assertEqual(int(next(s for s in info["streams"] if s["codec_type"] == "video")["nb_read_frames"]), 3)
        self.assertTrue(any(s["codec_type"] == "audio" for s in info["streams"]))
        report = json.loads((self.work / "out/fragment.mp4.render.json").read_text())
        self.assertEqual((report["fromFrame"], report["endFrame"]), (2, 5))
        self.assertEqual(report["artifact"]["sha256"], hashlib.sha256((self.work / "out/fragment.mp4").read_bytes()).hexdigest())

    def test_fragment_audio_starts_at_requested_source_offset(self):
        src = self.page("t => {document.body.style.background='navy'}", duration=.6)
        audio = self.work / "two-tones.wav"
        samples = [round(6000 * math.sin(2 * math.pi * (440 if i < 9600 else 880) * i / 48000))
                   for i in range(28800)]
        with wave.open(str(audio), "wb") as handle:
            handle.setnchannels(1)
            handle.setsampwidth(2)
            handle.setframerate(48000)
            handle.writeframes(struct.pack("<" + "h" * len(samples), *samples))
        self.run_render(src, "--audio", str(audio), "--from", ".2", "--to", ".5", "--out", "fragment.mp4")
        raw = subprocess.check_output(["ffmpeg", "-v", "error", "-i", str(self.work / "out/fragment.mp4"),
                                       "-map", "0:a:0", "-ac", "1", "-ar", "48000", "-f", "f32le", "-"], timeout=20)
        decoded = struct.unpack("<" + "f" * (len(raw) // 4), raw)
        # Exclude AAC edge transients. The selected source range contains only 880 Hz;
        # incorrectly starting at source zero would retain the 440 Hz section.
        middle = decoded[2048:-2048]
        self.assertGreater(len(middle), 6000)
        crossings = sum(left <= 0 < right for left, right in zip(middle, middle[1:]))
        measured_hz = crossings * 48000 / (len(middle) - 1)
        self.assertAlmostEqual(measured_hz, 880, delta=20)

    def test_apostrophe_in_output_directory_does_not_break_concat(self):
        src = self.page("t => {document.body.style.background='navy'}")
        outdir = self.work / "director's cut"
        self.run_render(src, "--outdir", str(outdir))
        info = self.probe(outdir / "film.mp4")
        self.assertEqual(int(next(s for s in info["streams"] if s["codec_type"] == "video")["nb_read_frames"]), 4)

    def test_determinism_checks_reordered_and_fresh_seeks(self):
        src = self.page("t => {document.body.style.background=t<.2?'white':'black'}")
        self.run_render(src, "--check-frames", "--times", "0,.2,.3")
        report = json.loads((self.work / "out/frame-check.json").read_text())
        self.assertEqual(report["status"], "passed")
        self.assertEqual({r["pass"] for r in report["comparisons"]}, {"reverse", "shuffled", "second-browser", "fresh-page"})
        self.assertEqual(len(report["comparisons"]), 12)

    def test_stateful_composition_fails_determinism(self):
        src = self.page("t => {document.body.style.background=++window.n%2?'white':'black'}", extra="window.n=0;")
        self.run_render(src, "--check-frames", "--times", "0,.2,.3", ok=False)
        report = json.loads((self.work / "out/frame-check.json").read_text())
        self.assertEqual(report["status"], "failed")
        self.assertTrue(any(r["status"] == "failed" and Path(r["evidence"]["difference"]).is_file() for r in report["comparisons"]))

    def test_preflight_blocks_remote_and_missing_local_assets(self):
        for resource in ('https://example.invalid/missing.png', 'missing.png'):
            src = self.page("t => {}", extra=f"const img=new Image();img.src={json.dumps(resource)};document.body.append(img);")
            self.run_render(src, "--preflight", ok=False)
            report = json.loads((self.work / "out/environment.json").read_text())
            self.assertEqual(report["status"], "failed")

    def test_early_failure_replaces_previous_success_reports(self):
        src = self.page("t => {}")
        outdir = self.work / "out"
        outdir.mkdir()
        for mode, filename in (("--preflight", "environment.json"), ("--check-frames", "frame-check.json")):
            for invalid in (("--chrome", "/missing/chrome"), ("--shutter", "1.1")):
                with self.subTest(mode=mode, invalid=invalid):
                    path = outdir / filename
                    path.write_text(json.dumps({"runId": "previous-run", "status": "passed"}))
                    self.run_render(src, mode, *invalid, ok=False)
                    report = json.loads(path.read_text())
                    self.assertEqual(report["status"], "failed", report)
                    self.assertNotEqual(report.get("runId"), "previous-run")

    def test_malformed_timeline_cue_is_rejected_even_if_html_ignores_it(self):
        src = self.page("t => {}")  # No window.__CUES or copying from __TIMELINE.
        timeline = self.work / "timeline.generated.json"
        for cue in (None, {"id": "bad", "t": "not-a-number"}, {"id": "bad", "t": .2, "d": 1}):
            with self.subTest(cue=cue):
                timeline.write_text(json.dumps({"version": 1, "fps": 10, "size": {"width": 64, "height": 64},
                                                "duration": .4, "durationFrames": 4, "cuts": [], "cues": [cue]}))
                self.run_render(src, "--preflight", "--timeline", str(timeline), ok=False)
                self.assertEqual(json.loads((self.work / "out/environment.json").read_text())["status"], "failed")

    @unittest.skipUnless(Path("/proc").is_dir(), "Process ownership check requires Linux /proc")
    def test_sigterm_stops_owned_browser_and_encoder_without_replacing_master(self):
        src = self.page("async t => {await new Promise(r=>setTimeout(r,2000));document.body.style.background='navy'}",
                        duration=8)
        outdir = self.work / "out"
        outdir.mkdir()
        master = outdir / "film.mp4"
        master.write_bytes(b"previous master")
        owned = {}

        def identity(pid):
            try:
                fields = Path(f"/proc/{pid}/stat").read_text().rpartition(") ")[2].split()
                return fields[19], fields[0]  # start time distinguishes PID reuse; Z is no longer running.
            except (OSError, IndexError):
                return None

        with (self.work / "abort.log").open("w+") as log:
            proc = subprocess.Popen(["node", str(RENDER), "--src", str(src), "--fps", "10", "--workers", "1",
                                     "--timeout", "5000"], stdout=log, stderr=log)
            marker = f"motion-chrome-{proc.pid}-".encode()

            def discover_owned():
                found_encoder = False
                for entry in Path("/proc").iterdir():
                    if not entry.name.isdigit():
                        continue
                    try:
                        cmd = (entry / "cmdline").read_bytes()
                    except OSError:
                        continue
                    is_encoder = b"ffmpeg" in cmd.split(b"\0", 1)[0] and str(outdir / ".render-").encode() in cmd
                    if marker in cmd or is_encoder:
                        state = identity(int(entry.name))
                        if state:
                            owned[int(entry.name)] = state[0]
                        found_encoder |= is_encoder
                return found_encoder

            try:
                deadline = time.monotonic() + 25
                while time.monotonic() < deadline and proc.poll() is None:
                    if discover_owned():
                        break
                    time.sleep(.05)
                else:
                    log.seek(0)
                    self.fail("No active owned encoder before termination: " + log.read())
                self.assertTrue(owned)
                proc.terminate()
                self.assertEqual(proc.wait(timeout=15), 143)
                deadline = time.monotonic() + 5
                alive = []
                while time.monotonic() < deadline:
                    alive = [pid for pid, start in owned.items()
                             if (state := identity(pid)) and state[0] == start and state[1] != "Z"]
                    if not alive:
                        break
                    time.sleep(.05)
                self.assertEqual(alive, [], f"Owned processes survived SIGTERM: {alive}")
                self.assertEqual(master.read_bytes(), b"previous master")
                for directory in {Path(tempfile.gettempdir()), Path("/tmp")}:
                    self.assertEqual(list(directory.glob(f"motion-chrome-{proc.pid}-*")), [])
            finally:
                if proc.poll() is None:
                    proc.kill()
                    proc.wait(timeout=5)
                # Only exact PIDs observed above, with matching start times; never broad pkill.
                for pid, start in owned.items():
                    state = identity(pid)
                    if state and state[0] == start and state[1] != "Z":
                        try:
                            os.kill(pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass

    def test_timeline_example_renders_without_overwriting_compiled_metadata(self):
        manifest = {"version": 1, "fps": 10, "size": {"width": 320, "height": 180}, "scenes": [
            {"id": "intro", "hold": .2, "cues": [{"id": "title", "t": 0, "d": .2, "text": "Żółć"}]},
            {"id": "end", "hold": .2}]}
        source = self.work / "film.json"
        source.write_text(json.dumps(manifest))
        timeline = self.work / "timeline.generated.json"
        subprocess.run(["python3", str(COMPILER), "--src", str(source), "--out", str(timeline)], check=True, capture_output=True)
        before = timeline.read_bytes()
        src = ROOT / "skills/motion-design/assets/timeline-example.html"
        self.run_render(src, "--timeline", str(timeline), "--outdir", str(self.work / "out"))
        self.assertEqual(timeline.read_bytes(), before)
        self.assertFalse((self.work / "out/cues.json").exists())
        info = self.probe(self.work / "out/film.mp4")
        self.assertEqual(int(next(s for s in info["streams"] if s["codec_type"] == "video")["nb_read_frames"]), 4)


if __name__ == "__main__":
    unittest.main()
