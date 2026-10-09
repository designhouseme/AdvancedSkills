"""Behavioral tests for optional film timeline compilation (stdlib only)."""

import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
COMPILER = ROOT / "skills/motion-design/scripts/compile_timeline.py"
EXAMPLE = ROOT / "skills/motion-design/assets/film.example.json"


def film():
    return {
        "version": 1, "fps": 30, "size": {"width": 1280, "height": 720},
        "scenes": [
            {"id": "intro", "hold": 2, "transition": {"type": "overlap", "duration": .4},
             "cues": [{"id": "title", "t": .2, "d": 1, "text": "Zażółć", "source": "Illustrative"}]},
            {"id": "middle", "hold": 3,
             "cues": [{"id": "title", "t": .5}, {"id": "accent", "ref": "middle.title", "offset": .2}]},
            {"id": "end", "hold": 1, "cues": [{"id": "title", "t": 0}]}
        ]
    }


class TimelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)
        self.src = self.work / "film.json"
        self.out = self.work / "timeline.generated.json"

    def run_compile(self, value=None, *, raw=None, speed=None, ok=True, out=None):
        self.src.write_text(raw if raw is not None else json.dumps(value if value is not None else film()), encoding="utf-8")
        cmd = [sys.executable, str(COMPILER), "--src", str(self.src), "--out", str(out or self.out)]
        if speed is not None:
            cmd += ["--speed", str(speed)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if ok:
            self.assertEqual(result.returncode, 0, result.stderr)
            return json.loads((out or self.out).read_text())
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("ERROR:", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        return result

    def test_example_is_a_compilable_real_input(self):
        output = self.run_compile(raw=EXAMPLE.read_text())
        self.assertEqual(output["durationFrames"], 195)
        self.assertEqual(output["cuts"], [4.5])
        self.assertEqual(output["scenes"][1]["startFrame"], 60)
        self.assertEqual(output["scenes"][0]["endFrame"], 72)

    def test_overlap_does_not_delay_later_scenes_or_cues(self):
        output = self.run_compile()
        self.assertEqual([s["startFrame"] for s in output["scenes"]], [0, 60, 150])
        self.assertEqual([s["endFrame"] for s in output["scenes"]], [72, 150, 180])
        self.assertEqual(output["duration"], 6)
        self.assertEqual(output["cuts"], [5])
        cues = {c["id"]: c for c in output["cues"]}
        self.assertEqual(cues["middle.accent"]["t"], 2.7)
        self.assertEqual(cues["end.title"]["t"], 5)
        self.assertEqual(cues["intro.title"]["text"], "Zażółć")

    def test_middle_duration_change_retimes_every_dependent_output(self):
        before = self.run_compile()
        value = film()
        value["scenes"][1]["hold"] = 4
        after = self.run_compile(value)
        self.assertEqual(after["durationFrames"] - before["durationFrames"], 30)
        self.assertEqual(after["cuts"], [6])
        self.assertEqual(after["scenes"][-1]["startFrame"], 180)
        self.assertEqual(next(c["t"] for c in after["cues"] if c["id"] == "end.title"), 6)

    def test_deleting_middle_scene_retimes_without_stale_cues(self):
        value = film()
        del value["scenes"][1]
        output = self.run_compile(value)
        self.assertEqual(output["durationFrames"], 90)
        self.assertEqual(output["scenes"][-1]["startFrame"], 60)
        self.assertFalse(any(c["scene"] == "middle" for c in output["cues"]))

    def test_deleting_target_scene_exposes_orphaned_reference(self):
        value = film()
        value["scenes"][-1]["cues"][0] = {"id": "title", "ref": "middle.title", "offset": 2.5}
        self.run_compile(value)
        del value["scenes"][1]
        result = self.run_compile(value, ok=False)
        self.assertIn("unknown cue reference", result.stderr)

    def test_speed_retimes_scenes_cuts_cues_and_windows(self):
        output = self.run_compile(speed=".75")
        self.assertEqual(output["durationFrames"], 240)
        self.assertEqual(output["scenes"][-1]["startFrame"], 200)
        self.assertEqual(output["cuts"], [200 / 30])
        cues = {c["id"]: c for c in output["cues"]}
        self.assertEqual(cues["intro.title"]["t"], 8 / 30)
        self.assertEqual(cues["intro.title"]["d"], 40 / 30)
        self.assertEqual(output["speed"], .75)

    def test_absolute_rounding_does_not_accumulate_per_scene_roundoff(self):
        value = film()
        value["scenes"] = [{"id": f"s{i}", "hold": .05} for i in range(10)]
        output = self.run_compile(value)
        self.assertEqual(output["durationFrames"], 15)
        self.assertEqual([s["startFrame"] for s in output["scenes"]], [0, 2, 3, 5, 6, 8, 9, 11, 12, 14])
        self.assertEqual(output["scenes"][0]["endFrame"], output["scenes"][1]["startFrame"])

    def test_window_duration_is_difference_of_rounded_endpoints(self):
        value = film()
        value["scenes"][0]["cues"] = [{"id": "title", "t": .05, "d": .05}]
        output = self.run_compile(value)
        cue = next(c for c in output["cues"] if c["id"] == "intro.title")
        self.assertEqual(cue["t"], 2 / 30)
        self.assertEqual(cue["d"], 1 / 30)

    def test_cue_end_is_exclusive_and_window_can_end_at_scene_end(self):
        value = film()
        value["scenes"] = [{"id": "only", "hold": 1, "cues": [{"id": "title", "t": 0, "d": 1}]}]
        self.run_compile(value)
        value["scenes"][0]["cues"] = [{"id": "title", "t": 1}]
        self.assertIn("outside", self.run_compile(value, ok=False).stderr)
        value["scenes"][0]["cues"] = [{"id": "title", "t": .99}]
        self.assertIn("quantization", self.run_compile(value, ok=False).stderr)

    def test_forward_reference_resolves_and_cycle_fails(self):
        value = film()
        value["scenes"][0]["cues"] = [{"id": "later", "ref": "intro.earlier", "offset": .2},
                                         {"id": "earlier", "t": .5}]
        out = self.run_compile(value)
        self.assertEqual(next(c["t"] for c in out["cues"] if c["id"] == "intro.later"), .7)
        value["scenes"][0]["cues"][1] = {"id": "earlier", "ref": "intro.later"}
        self.assertIn("cyclic", self.run_compile(value, ok=False).stderr)

    def test_invalid_inputs_are_errors_and_preserve_previous_artifact(self):
        cases = []
        for key, bad in [("fps", "30000/1001"), ("fps", 29.97), ("fps", True), ("version", True), ("fps", 0)]:
            item = film(); item[key] = bad; cases.append(item)
        item = film(); item["unknown"] = 1; cases.append(item)
        item = film(); item["size"]["width"] = False; cases.append(item)
        item = film(); item["scenes"][1]["id"] = "intro"; cases.append(item)
        item = film(); item["scenes"][0]["hold"] = -1; cases.append(item)
        item = film(); item["scenes"][0]["hold"] = .001; cases.append(item)
        item = film(); item["scenes"][-1]["transition"] = {"type": "cut", "duration": 0}; cases.append(item)
        item = film(); item["scenes"][0]["transition"]["duration"] = 4; cases.append(item)
        item = film(); item["scenes"][0]["transition"] = {"type": "cut", "duration": .2}; cases.append(item)
        for cue in [
            {"id": "x", "t": True}, {"id": "x", "t": -1}, {"id": "x", "t": 0, "d": -1},
            {"id": "x", "t": 0, "d": .001}, {"id": "x", "t": 0, "offset": 1},
            {"id": "x", "t": 0, "ref": "intro.x"}, {"id": "x", "ref": "absent.x"},
            {"id": "x", "t": 0, "d": 5}, {"id": "x", "t": 0, "text": "  "},
            {"id": "x", "t": 0, "source": False}, {"id": "x", "t": 0, "extra": 1},
        ]:
            item = film(); item["scenes"][0]["cues"] = [cue]; cases.append(item)
        item = film(); item["scenes"][0]["cues"] *= 2; cases.append(item)
        self.run_compile()
        original = self.out.read_bytes()
        for value in cases:
            with self.subTest(value=value):
                self.run_compile(value, ok=False)
                self.assertEqual(self.out.read_bytes(), original)
                self.assertFalse(list(self.work.glob("*.tmp")))

    def test_invalid_json_and_speed_fail_without_traceback(self):
        for raw in ['{"version":1,"version":1}', '{"fps":NaN}', '{"fps":Infinity}', '{']:
            with self.subTest(raw=raw):
                self.run_compile(raw=raw, ok=False)
        for speed in [0, -1, "NaN", "Infinity", "bad"]:
            with self.subTest(speed=speed):
                self.run_compile(speed=speed, ok=False)

    def test_provenance_hash_and_repeatability(self):
        first = self.run_compile()
        payload = self.out.read_bytes()
        self.assertEqual(first["source"]["sha256"], hashlib.sha256(self.src.read_bytes()).hexdigest())
        self.assertEqual(first["source"]["path"], str(self.src.resolve()))
        self.run_compile()
        self.assertEqual(payload, self.out.read_bytes())

    def test_output_cannot_replace_source(self):
        self.run_compile(out=self.src, ok=False)
        self.assertEqual(json.loads(self.src.read_text()), film())


if __name__ == "__main__":
    unittest.main()
