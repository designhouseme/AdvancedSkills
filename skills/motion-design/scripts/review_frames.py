#!/usr/bin/env python3
# SPDX-License-Identifier: CC-BY-4.0
# © 2026 Design House (https://designhouse.me)
"""Scan every decoded video frame; write bounded contact sheets and review.json.

Python standard library + ffmpeg/ffprobe. See ../references/review.md.
Exit 0: completed, possibly with warnings. Exit 1: failed/incomplete review.
"""
import argparse
from array import array
from collections import Counter, deque
from fractions import Fraction
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import threading


class ReviewError(Exception):
    pass


SETTINGS = {
    "scan_width": 64, "scan_height": 36,
    "black_mean_max": 8.0, "black_pixel_max": 20,
    "uniform_stddev_max": 2.0,
    "flash_delta_min": 20.0, "flash_return_ratio_max": 0.25,
    "flash_return_floor": 6.0,
    "max_findings": 200, "max_candidates": 96, "cells_per_page": 12,
    "cell_width": 320, "cell_height": 180, "label_height": 28,
    "label_method": "static-after-tile-v1",
}


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run(command, timeout):
    try:
        result = subprocess.run(command, capture_output=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ReviewError(f"Tool could not complete: {exc}") from exc
    if result.returncode:
        raise ReviewError(f"{Path(command[0]).name} exited {result.returncode}: "
                          + result.stderr.decode("utf-8", "replace")[-3000:])
    return result


def number(value, label):
    if isinstance(value, bool):
        raise ReviewError(f"{label} must be a finite number")
    try:
        result = float(value)
    except (ValueError, TypeError) as exc:
        raise ReviewError(f"{label} must be a finite number") from exc
    if not math.isfinite(result):
        raise ReviewError(f"{label} must be a finite number")
    return result


def rate(value):
    try:
        result = Fraction(str(value))
    except (ValueError, ZeroDivisionError) as exc:
        raise ReviewError(f"Invalid frame rate: {value}") from exc
    if result <= 0:
        raise ReviewError(f"Invalid frame rate: {value}")
    return result


def metadata(path, timeout):
    result = run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames",
                  "-show_entries", "stream=index,codec_name,width,height,avg_frame_rate,r_frame_rate,time_base,"
                  "duration,nb_frames,nb_read_frames,start_time:format=duration,size", "-of", "json", str(path)], timeout)
    if result.stderr.strip():
        raise ReviewError("ffprobe reported a decoding error: " + result.stderr.decode("utf-8", "replace")[-3000:])
    try:
        data = json.loads(result.stdout)
        stream = data["streams"][0]
        count = int(stream["nb_read_frames"])
    except (ValueError, KeyError, IndexError) as exc:
        raise ReviewError("No countable video stream found") from exc
    if count <= 0:
        raise ReviewError("Video contains no decodable frames")
    fps = rate(stream.get("avg_frame_rate", "0/0"))
    expected = stream.get("nb_frames")
    if expected not in (None, "N/A") and int(expected) != count:
        raise ReviewError(f"Incomplete video: container declares {expected} frames, ffprobe decoded {count}")
    return data, stream, fps, count


def read_contract(path, legacy):
    if path is None:
        return None
    if path.stat().st_size > 2 * 1024 * 1024:
        raise ReviewError("Timeline/cues file exceeds the 2 MiB input limit")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("cues", []), list):
        raise ReviewError("Timeline/cues must be an object containing a cues array")
    cuts = data.get("cuts", [])
    if not isinstance(cuts, list):
        raise ReviewError("cuts must be an array of seconds")
    cuts = [number(t, "cut time") for t in cuts]
    cues, holds = [], []
    for i, cue in enumerate(data.get("cues", [])):
        if not isinstance(cue, dict) or "t" not in cue:
            raise ReviewError(f"Cue {i} must be an object with t in seconds")
        t = number(cue["t"], f"cue {i} time")
        d = number(cue.get("d", 0), f"cue {i} duration")
        if t < 0 or d < 0:
            raise ReviewError("Cue times and durations cannot be negative")
        cues.append({"id": str(cue.get("id", f"cue-{i}")), "t": t, "d": d})
        if legacy and cue.get("type") == "cut":
            cuts.append(t)
        if legacy and cue.get("type") == "hold":
            if d <= 0:
                raise ReviewError("An explicit hold cue requires d > 0")
            holds.append((t, t + d))
    if any(t < 0 for t in cuts):
        raise ReviewError("Cut times cannot be negative")
    return {"path": str(path.resolve()), "sha256": sha256(path), "legacy": legacy,
            "cuts": sorted(set(cuts)), "cues": cues, "holds": holds,
            "durationFrames": data.get("durationFrames"), "fps": data.get("fps")}


def delta(left, right):
    return sum(abs(a - b) for a, b in zip(left, right)) / len(left)


def scan(path, work, timeout):
    """Keep three small frames, bounded findings and scalar timestamps, never full images."""
    log_path = work / "decode.log"
    size = SETTINGS["scan_width"] * SETTINGS["scan_height"]
    frames, window, events = 0, deque(maxlen=3), []
    counts = Counter()
    uniform_run = None
    timed_out = threading.Event()

    def event(kind, first, last, **evidence):
        counts[kind] += 1
        if len(events) < SETTINGS["max_findings"]:
            events.append({"kind": kind, "first_frame": first, "last_frame": last, **evidence})

    def finish_run():
        nonlocal uniform_run
        if uniform_run:
            event(uniform_run["kind"], uniform_run["first"], uniform_run["last"])
            uniform_run = None

    command = ["ffmpeg", "-hide_banner", "-nostdin", "-v", "info", "-xerror", "-err_detect", "explode",
               "-threads", "1", "-copyts", "-i", str(path), "-map", "0:v:0", "-an", "-sn", "-dn",
               "-filter_threads", "1", "-vf", f"scale={SETTINGS['scan_width']}:{SETTINGS['scan_height']}:flags=area,format=gray,showinfo",
               "-fps_mode", "passthrough", "-f", "rawvideo", "pipe:1"]
    with log_path.open("wb") as log:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=log)
        def expire():
            timed_out.set()
            process.kill()
        timer = threading.Timer(timeout, expire)
        timer.daemon = True
        timer.start()
        try:
            while True:
                frame = process.stdout.read(size)
                if not frame:
                    break
                if len(frame) != size:
                    raise ReviewError("Incomplete decoded raw frame")
                mean = sum(frame) / size
                variance = sum(v * v for v in frame) / size - mean * mean
                kind = ("black_frames" if mean <= SETTINGS["black_mean_max"] and max(frame) <= SETTINGS["black_pixel_max"]
                        else "uniform_frames" if variance <= SETTINGS["uniform_stddev_max"] ** 2 else None)
                if kind:
                    if uniform_run and uniform_run["kind"] == kind:
                        uniform_run["last"] = frames
                    else:
                        finish_run()
                        uniform_run = {"kind": kind, "first": frames, "last": frames}
                else:
                    finish_run()
                window.append(frame)
                if len(window) == 3:
                    incoming, outgoing = delta(window[0], window[1]), delta(window[1], window[2])
                    if min(incoming, outgoing) >= SETTINGS["flash_delta_min"]:
                        returned = delta(window[0], window[2])
                        if returned <= max(SETTINGS["flash_return_floor"], min(incoming, outgoing) * SETTINGS["flash_return_ratio_max"]):
                            event("isolated_temporal_outlier", frames - 1, frames - 1,
                                  incoming_delta=round(incoming, 4), outgoing_delta=round(outgoing, 4),
                                  neighbor_delta=round(returned, 4))
                frames += 1
            finish_run()
            code = process.wait()
        finally:
            timer.cancel()
            if process.poll() is None:
                process.kill()
                process.wait()
            process.stdout.close()
    if timed_out.is_set():
        raise ReviewError("Full-frame scan timed out; coverage is incomplete")
    if code:
        with log_path.open("rb") as handle:
            handle.seek(max(0, log_path.stat().st_size - 3000))
            detail = handle.read().decode("utf-8", "replace")
        raise ReviewError(f"ffmpeg full-frame decode failed ({code}): {detail}")
    timestamps = array("d")
    pattern = re.compile(r"\bn:\s*(\d+).*?\bpts_time:\s*([-+\d.eE]+)")
    with log_path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            found = pattern.search(line)
            if found:
                index, stamp = int(found[1]), float(found[2])
                if index != len(timestamps) or not math.isfinite(stamp):
                    raise ReviewError("Invalid or discontinuous decoded frame timestamps")
                timestamps.append(stamp)
    if not frames or len(timestamps) != frames:
        raise ReviewError(f"Incomplete timestamp coverage: {len(timestamps)} timestamps for {frames} frames")
    first_pts = timestamps[0]
    for i in range(len(timestamps)):
        timestamps[i] -= first_pts
        if i and timestamps[i] < timestamps[i - 1]:
            raise ReviewError("Decoded presentation timestamps move backwards")
    return frames, timestamps, first_pts, events, counts


def frame_near(times, target):
    import bisect
    pos = bisect.bisect_left(times, target)
    if pos == len(times):
        return pos - 1
    if pos and target - times[pos - 1] < times[pos] - target:
        return pos - 1
    return pos


def classify(events, counts, times, fps, contract):
    cuts = set()
    if contract:
        cuts = {frame_near(times, t) for t in contract["cuts"] if 0 <= t <= times[-1] + 0.5 / float(fps)}
    findings, candidates = [], {}
    def candidate(index, reason, priority):
        if 0 <= index < len(times):
            item = candidates.setdefault(index, {"frame": index, "t": round(times[index], 9), "reasons": [], "priority": priority})
            item["priority"] = min(item["priority"], priority)
            if reason not in item["reasons"]:
                item["reasons"].append(reason)
    candidate(0, "first_frame", 0)
    candidate(len(times) - 1, "last_frame", 0)
    for entry in events:
        first, last = entry["first_frame"], entry["last_frame"]
        declared_cut = entry["kind"] == "isolated_temporal_outlier" and (first in cuts or first + 1 in cuts)
        finding = {"status": "passed" if declared_cut else "warning", "code": "declared_cut_transition" if declared_cut else entry["kind"],
                   "first_frame": first, "last_frame": last, "t": round(times[first], 9), "end_t": round(times[last], 9),
                   "frame_count": last - first + 1,
                   "evidence": {k: v for k, v in entry.items() if k not in ("kind", "first_frame", "last_frame")}}
        if contract and any(start <= times[first] and times[last] < end for start, end in contract["holds"]):
            finding["declared_hold"] = True
        findings.append(finding)
        for index in sorted({first - 1, first, last, last + 1}):
            candidate(index, finding["code"], 2 if declared_cut else 1)
    if contract:
        boundaries = [("cut", t) for t in contract["cuts"]]
        for cue in contract["cues"]:
            boundaries.append((f"cue:{cue['id']}", cue["t"]))
            if cue["d"]:
                boundaries.append((f"cue-end:{cue['id']}", cue["t"] + cue["d"]))
        for label, moment in boundaries:
            if moment > times[-1] + 1 / float(fps):
                continue
            center = frame_near(times, moment)
            for index in (center - 1, center, center + 1):
                candidate(index, label, 2)
    ordered = sorted(candidates.values(), key=lambda c: (c["priority"], c["frame"]))
    selected = sorted(ordered[:SETTINGS["max_candidates"]], key=lambda c: c["frame"])
    for i, item in enumerate(selected):
        item.pop("priority")
        item["page"] = i // SETTINGS["cells_per_page"] + 1
        item["cell"] = i % SETTINGS["cells_per_page"] + 1
    return findings, selected, {"findings": sum(counts.values()) - len(events), "candidates": len(candidates) - len(selected)}


def sheets(path, work, candidates, timeout, prefix, first_pts):
    selection = "+".join(f"eq(n\\,{item['frame']})" for item in candidates)
    # Label the finished sheets with fixed text, outside the source thumbnails.
    # Dynamic drawtext over reused frame/padding buffers can retain or clip old
    # glyphs in some FFmpeg builds. Each bounded label has its own filter here.
    width, height, label_height = (SETTINGS[k] for k in ("cell_width", "cell_height", "label_height"))
    vf = (f"select='{selection}',setpts=PTS-({first_pts:.12f})/TB,"
          f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
          f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1,"
          f"pad={width}:{height + label_height}:0:{label_height}:color=black,"
          "tile=4x3:nb_frames=12:padding=4:margin=4:color=black")
    for index, candidate in enumerate(candidates):
        page, cell = divmod(index, SETTINGS["cells_per_page"])
        x, y = 4 + (cell % 4) * (width + 4), 4 + (cell // 4) * (height + label_height + 4)
        # Candidate times come from the decoded PTS, relative to its first frame.
        whole, millis = divmod(math.floor(candidate["t"] * 1000 + 0.5), 1000)
        hours, rest = divmod(whole, 3600)
        minutes, seconds = divmod(rest, 60)
        stamp = f"{hours:02d}\\:{minutes:02d}\\:{seconds:02d}.{millis:03d}"
        vf += (f",drawbox=x={x}:y={y}:w={width}:h={label_height}:color=black:t=fill:enable='eq(n,{page})'"
               f",drawtext=text='{stamp}':x={x + 6}:y={y + 6}:fontsize=16:fontcolor=white:enable='eq(n,{page})'")
    pages = math.ceil(len(candidates) / SETTINGS["cells_per_page"])
    result = run(["ffmpeg", "-hide_banner", "-nostdin", "-v", "error", "-xerror", "-err_detect", "explode",
                  "-threads", "1", "-copyts", "-i", str(path), "-map", "0:v:0", "-an", "-sn", "-dn",
                  "-filter_threads", "1", "-vf", vf, "-fps_mode", "passthrough", "-frames:v", str(pages),
                  "-q:v", "3", "-start_number", "1", str(work / f"{prefix}-%02d.jpg")], timeout)
    if result.stderr.strip():
        raise ReviewError("Contact sheet generation reported an error: " + result.stderr.decode("utf-8", "replace")[-2000:])
    output = sorted(work.glob(f"{prefix}-*.jpg"))
    if len(output) != pages or any(p.stat().st_size == 0 for p in output):
        raise ReviewError(f"Contact sheet coverage incomplete: expected {pages}, found {len(output)}")
    return output


def atomic_report(path, data):
    fd, name = tempfile.mkstemp(prefix=".review-", suffix=".json", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2, allow_nan=False)
            handle.write("\n")
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def review(args):
    outdir = Path(args.outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    film = Path(args.film).resolve()
    report = {"schemaVersion": 1, "status": "failed", "artifact": {"path": str(film), "sha256": None},
              "settings": dict(SETTINGS), "coverage": {"all_frames_decoded": False}, "findings": [], "sheets": [],
              "checks": {"visual_inspection": "not_checked", "text_ocr": "not_checked", "audio_listening": "not_checked",
                         "audio_measurement": "not_checked", "semantic_text_visibility": "not_checked",
                         "alpha_integrity": "not_checked", "colour_only_changes": "not_checked",
                         "accessibility_flash_safety": "not_checked", "render_determinism": "not_checked"}}
    report["settings"]["command_timeout_seconds"] = args.timeout
    try:
        for executable in ("ffmpeg", "ffprobe"):
            if not shutil.which(executable):
                raise ReviewError(f"Missing required tool: {executable}")
        if not film.is_file():
            raise ReviewError(f"Film not found: {film}")
        report["artifact"].update({"sha256": sha256(film), "size_bytes": film.stat().st_size})
        contract_path = Path(args.timeline or args.cues) if (args.timeline or args.cues) else None
        contract = read_contract(contract_path, bool(args.cues))
        report["timeline"] = contract
        probe, stream, fps, count = metadata(film, args.timeout)
        report["probe"] = probe
        report["fps"] = {"rational": str(fps), "value": float(fps)}
        report["coverage"]["probe_decoded_frames"] = count
        if contract and contract["durationFrames"] is not None:
            expected = number(contract["durationFrames"], "durationFrames")
            if expected != count:
                raise ReviewError(f"Timeline expects {expected:g} frames but artifact contains {count}; use a full-film timeline, not one for a fragment")
        if contract and contract["fps"] is not None and rate(contract["fps"]) != fps:
            raise ReviewError(f"Timeline fps {contract['fps']} differs from artifact fps {fps}")
        with tempfile.TemporaryDirectory(prefix="motion-review-") as directory:
            work = Path(directory)
            frames, times, first_pts, events, counts = scan(film, work, args.timeout)
            report["coverage"].update({"decoded_frames": frames, "timestamped_frames": len(times), "first_source_pts": first_pts,
                                       "first_t": times[0], "last_t": times[-1], "all_frames_decoded": frames == count})
            if frames != count:
                raise ReviewError(f"Incomplete decode: ffprobe counted {count}, scanner decoded {frames}")
            expected_step = 1 / float(fps)
            variable = any(abs((times[i] - times[i - 1]) - expected_step) > max(0.001, expected_step * 0.05) for i in range(1, len(times)))
            report["coverage"]["variable_frame_intervals"] = variable
            findings, candidates, omitted = classify(events, counts, times, fps, contract)
            report.update({"findings": findings, "candidates": candidates, "omitted": omitted,
                           "detected_event_counts": dict(sorted(counts.items()))})
            if variable:
                findings.append({"status": "warning", "code": "variable_frame_intervals", "evidence": "Candidate times use decoded PTS, not index/fps."})
            if omitted["findings"] or omitted["candidates"]:
                findings.append({"status": "warning", "code": "bounded_evidence", "evidence": omitted})
            settings_hash = hashlib.sha256(json.dumps({"settings": report["settings"], "timeline": contract}, sort_keys=True).encode()).hexdigest()[:8]
            prefix = f"review-{report['artifact']['sha256'][:12]}-{settings_hash}"
            pictures = sheets(film, work, candidates, args.timeout, prefix, first_pts)
            if sha256(film) != report["artifact"]["sha256"]:
                raise ReviewError("Film changed during review; the report cannot certify this artifact")
            if contract_path and sha256(contract_path) != contract["sha256"]:
                raise ReviewError("Timeline/cues changed during review")
            for picture in pictures:
                target = outdir / picture.name
                fd, staged = tempfile.mkstemp(prefix=".sheet-", suffix=".jpg", dir=outdir)
                os.close(fd)
                try:
                    shutil.copyfile(picture, staged)
                    os.replace(staged, target)
                finally:
                    if os.path.exists(staged):
                        os.unlink(staged)
                report["sheets"].append({"path": picture.name, "sha256": sha256(target)})
            report["checks"]["decode_coverage"] = "passed"
            report["checks"]["temporal_scan"] = "warning" if any(f["status"] == "warning" for f in findings) else "passed"
            report["checks"]["contact_sheet_generation"] = "passed"
            report["status"] = report["checks"]["temporal_scan"]
    except (ReviewError, OSError, ValueError, TypeError) as exc:
        report["status"] = "failed"
        report["findings"].append({"status": "failed", "code": "review_incomplete", "evidence": str(exc)})
        report["checks"]["review_completion"] = "failed"
    atomic_report(outdir / "review.json", report)
    print(f"{report['status'].upper()}: {outdir / 'review.json'}")
    return 1 if report["status"] == "failed" else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--film", required=True)
    inputs = parser.add_mutually_exclusive_group()
    inputs.add_argument("--timeline", help="Generated full-film timeline JSON")
    inputs.add_argument("--cues", help="Legacy {duration,cues} JSON; explicit type:cut/hold supported")
    parser.add_argument("--outdir", default="out/review")
    parser.add_argument("--timeout", type=float, default=300, help="Maximum seconds per external command (default 300)")
    args = parser.parse_args()
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error("--timeout must be positive and finite")
    return review(args)


if __name__ == "__main__":
    sys.exit(main())
