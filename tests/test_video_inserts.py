"""Actual insert placement and segment-ID propagation; no media/model downloads."""

import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("video_cut", ROOT / "skills/video-edit/scripts/cut.py")
cut = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cut)


def segments():
    return [
        {"id": "hook", "in": 10.0, "out": 14.0, "out_start": 0.0},
        {"id": "result", "in": 10.0, "out": 14.0, "out_start": 8.0},
    ]


def insert(**values):
    return dict({"src": "result.mp4", "src_at": 11.0, "dur": 2.0}, **values)


class InsertPlacementTests(unittest.TestCase):
    def place(self, rows, items, fps=25):
        warn = []
        result = cut.place_inserts({"_fps": fps, "inserts": items}, rows, warn)
        return result, warn

    def test_selector_picks_second_occurrence_not_first_source_match(self):
        rows = segments()
        placed, warn = self.place(rows, [insert(segment_id="result")])
        self.assertEqual(placed, [(9.0, 2.0, "result.mp4", 0.0)])
        self.assertNotIn("inserts", rows[0])
        self.assertEqual(rows[1]["inserts"], [[9.0, 11.0, "result.mp4"]])
        self.assertEqual(warn, [])

    def test_selector_stays_with_occurrence_after_reorder(self):
        rows = list(reversed(segments()))
        rows[0]["out_start"], rows[1]["out_start"] = 0.0, 4.0
        placed, _ = self.place(rows, [insert(segment_id="result")])
        self.assertEqual(placed[0][:2], (1.0, 2.0))
        self.assertNotIn("inserts", rows[1])

    def test_ambiguous_anchor_is_actionable_with_or_without_ids(self):
        for use_ids in (True, False):
            rows = segments()
            if not use_ids:
                for row in rows:
                    del row["id"]
            with self.subTest(ids=use_ids), self.assertRaises(SystemExit) as raised:
                self.place(rows, [insert()])
            message = str(raised.exception)
            self.assertIn("ambiguous", message)
            self.assertIn("segment_id", message)
            self.assertIn("0 (id=", message)
            self.assertIn("1 (id=", message)
            self.assertTrue(all("inserts" not in row for row in rows))

    def test_unambiguous_legacy_segment_keeps_rounding_and_tuple_shape(self):
        row = {"in": 10.0, "out": 14.0, "out_start": 5.0}
        with patch.object(cut.subprocess, "run") as probe:
            placed, warn = self.place([row], [insert(src_at=10.13, dur=1.21)])
        self.assertEqual(placed, [(5.12, 1.2, "result.mp4", 0.0)])
        self.assertEqual(row["inserts"], [[5.12, 6.32, "result.mp4"]])
        self.assertEqual(warn, [])
        probe.assert_not_called()

    def test_default_fps_remains_25(self):
        rows = [segments()[0]]
        placed = cut.place_inserts({"inserts": [insert(src_at=10.13)]}, rows, [])
        self.assertEqual(placed[0][0], .12)

    def test_existing_presnap_tolerance_clamps_to_segment_start(self):
        placed, _ = self.place([segments()[1]], [insert(src_at=9.71, segment_id="result")])
        self.assertEqual(placed[0][:2], (8.0, 2.0))

    def test_overlapping_tolerance_windows_are_also_ambiguous(self):
        rows = [{"in": 10.0, "out": 11.0, "out_start": 0.0},
                {"in": 11.0, "out": 12.0, "out_start": 1.0}]
        with self.assertRaisesRegex(SystemExit, "ambiguous"):
            self.place(rows, [insert(src_at=10.8)])

    def test_missing_selector_target_fails_even_when_source_matches(self):
        for rows in (segments(), [{"in": 10.0, "out": 14.0, "out_start": 0.0}]):
            with self.subTest(rows=rows), self.assertRaisesRegex(SystemExit, "unknown segment_id"):
                self.place(rows, [insert(segment_id="missing")])

    def test_selector_must_match_source_anchor_not_just_exist(self):
        rows = segments()
        rows[1].update({"in": 20.0, "out": 24.0})
        with self.assertRaisesRegex(SystemExit, "does not match segment_id 'result'"):
            self.place(rows, [insert(segment_id="result")])

    def test_source_outpoint_is_exclusive(self):
        with self.assertRaisesRegex(SystemExit, "outside every segment"):
            self.place([segments()[0]], [insert(src_at=14.0)])
        with self.assertRaisesRegex(SystemExit, "does not match"):
            self.place([segments()[0]], [insert(src_at=14.0, segment_id="hook")])

    def test_duplicate_ids_fail_before_placement_even_without_inserts(self):
        rows = segments()
        rows[1]["id"] = "hook"
        with self.assertRaisesRegex(SystemExit, "duplicate segment id 'hook'"):
            self.place(rows, [])

    def test_invalid_segment_ids_and_selectors_are_errors(self):
        for invalid in (None, "", " ", " hook", "hook ", 1, True, []):
            with self.subTest(field="id", value=invalid):
                rows = [dict(segments()[0], id=invalid)]
                with self.assertRaisesRegex(SystemExit, "id must be a non-empty string"):
                    self.place(rows, [])
            with self.subTest(field="segment_id", value=invalid):
                with self.assertRaisesRegex(SystemExit, "segment_id must be a non-empty string"):
                    self.place(segments(), [insert(segment_id=invalid)])

    def test_clips_to_selected_segment_end_without_spilling_into_next(self):
        rows = segments()
        placed, warn = self.place(rows, [insert(src_at=13.0, dur=3.0, segment_id="result")])
        self.assertEqual(placed, [(11.0, 1.0, "result.mp4", 0.0)])
        self.assertEqual(rows[1]["inserts"], [[11.0, 12.0, "result.mp4"]])
        self.assertTrue(any("cut to 1.00 s" in message for message in warn))

    def test_nonpositive_or_nonfinite_duration_cannot_be_placed(self):
        for duration in (0, -1, float("nan"), float("inf"), True, "2"):
            with self.subTest(duration=duration), self.assertRaises(SystemExit):
                self.place([segments()[0]], [insert(dur=duration)])

    def test_rounding_cannot_produce_empty_insert(self):
        for item in (insert(dur=.001), insert(src_at=13.999, dur=1)):
            rows = [segments()[0]]
            with self.subTest(insert=item), self.assertRaisesRegex(SystemExit, "no positive duration"):
                self.place(rows, [item])
            self.assertNotIn("inserts", rows[0])

    def test_invalid_anchor_and_skip_are_errors(self):
        for value in (None, float("nan"), float("inf"), "11", True):
            with self.subTest(anchor=value), self.assertRaisesRegex(SystemExit, "src_at must be a finite number"):
                self.place([segments()[0]], [insert(src_at=value)])
        for value in (-1, None, float("nan"), float("inf"), "1", True):
            with self.subTest(skip=value), self.assertRaises(SystemExit):
                self.place([segments()[0]], [insert(skip=value)])

    def test_skip_clips_to_available_complete_frames(self):
        result = subprocess.CompletedProcess([], 0, "1.03\n", "")
        with patch.object(cut.subprocess, "run", return_value=result):
            placed, warn = self.place([segments()[0]], [insert(skip=.5)])
        self.assertEqual(placed, [(1.0, .52, "result.mp4", .5)])
        self.assertTrue(any("cut to 0.52 s" in message for message in warn))

    def test_skip_at_or_beyond_duration_cannot_create_nonpositive_insert(self):
        result = subprocess.CompletedProcess([], 0, "1.0", "")
        for skip in (1, 2, .999):
            with self.subTest(skip=skip), patch.object(cut.subprocess, "run", return_value=result):
                with self.assertRaisesRegex(SystemExit, "no positive duration"):
                    self.place([segments()[0]], [insert(skip=skip)])

    def test_failed_missing_or_unusable_probe_is_actionable(self):
        cases = [subprocess.CompletedProcess([], 1, "", "missing file")]
        cases += [subprocess.CompletedProcess([], 0, value, "") for value in ("", "N/A", "nan", "inf", "0", "-1")]
        for result in cases:
            with self.subTest(result=result), patch.object(cut.subprocess, "run", return_value=result):
                with self.assertRaisesRegex(SystemExit, "ffprobe"):
                    self.place([segments()[0]], [insert(skip=.5)])
        with patch.object(cut.subprocess, "run", side_effect=FileNotFoundError("ffprobe missing")):
            with self.assertRaisesRegex(SystemExit, "cannot probe"):
                self.place([segments()[0]], [insert(skip=.5)])


class SegmentIdPropagationTests(unittest.TestCase):
    def test_main_preserves_optional_ids_in_processed_cuts(self):
        class StopBeforeRender(Exception):
            pass

        with tempfile.TemporaryDirectory() as temp:
            work = Path(temp)
            edit = {"src": "source.mp4", "segments": [
                {"id": "hook", "in": 10, "out": 12, "exact": True},
                {"in": 20, "out": 22, "exact": True},
                {"id": "result", "in": 10, "out": 12, "exact": True},
            ]}
            (work / "edit.json").write_text(json.dumps(edit))
            (work / "words.json").write_text('{"words": []}')
            (work / "audio.json").write_text('{}')
            argv = ["cut.py", "--edit", str(work / "edit.json"), "--words", str(work / "words.json"),
                    "--audio", str(work / "audio.json"), "--work", str(work), "--out", str(work / "final.mp4")]
            heard = lambda src, start, end, language: [{"word": "Hello", "start": start, "end": end}]
            with patch.object(sys, "argv", argv), patch.object(cut, "Env", return_value=SimpleNamespace(runs=[])), \
                    patch.object(cut, "probe", return_value=(1920, 1080, 25, "00:00:00:00")), \
                    patch.object(cut, "retranscribe", side_effect=heard), \
                    patch.object(cut, "place_inserts", side_effect=StopBeforeRender) as place:
                with self.assertRaises(StopBeforeRender):
                    cut.main()
            rows = json.loads((work / "cuts.json").read_text())["segments"]
            self.assertEqual([row.get("id") for row in rows], ["hook", None, "result"])
            self.assertNotIn("id", rows[1])
            self.assertEqual([row["out_start"] for row in rows], [0, 2, 4])
            self.assertEqual(place.call_args.args[1], rows)
            actual = copy.deepcopy(rows)
            placed = cut.place_inserts({"inserts": [insert(segment_id="result", dur=.5)]}, actual, [])
            self.assertEqual(placed, [(5.0, .48, "result.mp4", 0.0)])


if __name__ == "__main__":
    unittest.main()
