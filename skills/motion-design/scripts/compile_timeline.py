#!/usr/bin/env python3
# SPDX-License-Identifier: CC-BY-4.0
# © 2026 Design House (https://designhouse.me)
"""Compile an optional film manifest to frame-aligned scene and cue metadata.

Python standard library only. Usage:
  python3 compile_timeline.py --src film.json --out timeline.generated.json --speed .75
"""

import argparse
from decimal import Decimal
from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile


class ManifestError(ValueError):
    """Invalid input, with a path to the responsible field."""


ID = re.compile(r"^[a-zA-Z][a-zA-Z0-9_-]*$")
REF = re.compile(r"^[a-zA-Z][a-zA-Z0-9_-]*\.[a-zA-Z][a-zA-Z0-9_-]*$")


def object_fields(value, required, optional, where):
    if not isinstance(value, dict):
        raise ManifestError(f"{where}: expected an object")
    missing = set(required) - value.keys()
    unknown = value.keys() - set(required) - set(optional)
    if missing:
        raise ManifestError(f"{where}: missing {', '.join(sorted(missing))}")
    if unknown:
        raise ManifestError(f"{where}: unknown field(s) {', '.join(sorted(unknown))}")


def number(value, where, *, positive=False, integer=False):
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal, Fraction)):
        raise ManifestError(f"{where}: expected a finite number")
    try:
        result = Fraction(str(value))
    except (ValueError, OverflowError):
        raise ManifestError(f"{where}: expected a finite number") from None
    if result < 0 or (positive and result == 0):
        raise ManifestError(f"{where}: must be {'positive' if positive else 'non-negative'}")
    if integer and result.denominator != 1:
        raise ManifestError(f"{where}: expected an integer; fractional fps is not supported in v1")
    return int(result) if integer else result


def string(value, where, pattern=None):
    if not isinstance(value, str) or not value.strip():
        raise ManifestError(f"{where}: expected a non-empty string")
    if pattern is not None and not pattern.fullmatch(value):
        raise ManifestError(f"{where}: invalid identifier {value!r}")
    return value


def array(value, where, *, nonempty=False):
    if not isinstance(value, list) or (nonempty and not value):
        raise ManifestError(f"{where}: expected {'a non-empty' if nonempty else 'an'} array")
    return value


def read_manifest(path):
    raw = Path(path).read_bytes()

    def invalid_constant(value):
        raise ManifestError(f"non-finite JSON number: {value}")

    def unique_keys(pairs):
        out = {}
        for key, value in pairs:
            if key in out:
                raise ManifestError(f"duplicate JSON field: {key}")
            out[key] = value
        return out

    try:
        manifest = json.loads(raw, parse_float=Decimal, parse_constant=invalid_constant,
                              object_pairs_hook=unique_keys)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ManifestError(f"invalid JSON: {exc}") from None
    return manifest, hashlib.sha256(raw).hexdigest()


def compile_manifest(manifest, *, source_path, source_sha256, speed=1):
    object_fields(manifest, {"version", "fps", "size", "scenes"}, set(), "film")
    if number(manifest["version"], "version", integer=True) != 1:
        raise ManifestError("version: only manifest version 1 is supported")
    fps = number(manifest["fps"], "fps", positive=True, integer=True)
    speed = number(speed, "speed", positive=True)
    size = manifest["size"]
    object_fields(size, {"width", "height"}, set(), "size")
    size = {k: number(size[k], f"size.{k}", positive=True, integer=True)
            for k in ("width", "height")}
    inputs = array(manifest["scenes"], "scenes", nonempty=True)
    scenes, scene_ids, cue_defs = [], set(), {}
    cursor = Fraction(0)
    for i, scene in enumerate(inputs):
        where = f"scenes[{i}]"
        object_fields(scene, {"id", "hold"}, {"transition", "cues"}, where)
        sid = string(scene["id"], where + ".id", ID)
        if sid in scene_ids:
            raise ManifestError(f"{where}.id: duplicate scene ID {sid!r}")
        scene_ids.add(sid)
        hold = number(scene["hold"], where + ".hold", positive=True)
        transition = {"type": "cut", "duration": Fraction(0)}
        if "transition" in scene:
            if i == len(inputs) - 1:
                raise ManifestError(f"{where}.transition: the last scene cannot have an outgoing transition")
            tr = scene["transition"]
            object_fields(tr, {"type", "duration"}, set(), where + ".transition")
            if tr["type"] not in ("cut", "overlap"):
                raise ManifestError(f"{where}.transition.type: expected cut or overlap")
            duration = number(tr["duration"], where + ".transition.duration")
            if (tr["type"] == "cut" and duration != 0) or (tr["type"] == "overlap" and duration == 0):
                raise ManifestError(f"{where}.transition: cut needs duration 0; overlap needs positive duration")
            transition = {"type": tr["type"], "duration": duration}
        end = cursor + hold + transition["duration"]
        row = {"id": sid, "start": cursor, "holdEnd": cursor + hold,
               "end": end, "transition": transition}
        scenes.append(row)
        for j, cue in enumerate(array(scene.get("cues", []), where + ".cues")):
            cw = f"{where}.cues[{j}]"
            object_fields(cue, {"id"}, {"t", "ref", "offset", "d", "text", "source"}, cw)
            cid = sid + "." + string(cue["id"], cw + ".id", ID)
            if cid in cue_defs:
                raise ManifestError(f"{cw}.id: duplicate cue ID {cid!r}")
            if ("t" in cue) == ("ref" in cue):
                raise ManifestError(f"{cw}: provide exactly one of t or ref")
            data = {"id": cid, "scene": row, "where": cw}
            if "t" in cue:
                if "offset" in cue:
                    raise ManifestError(f"{cw}.offset: only valid with ref")
                data["t"] = cursor + number(cue["t"], cw + ".t")
            else:
                data["ref"] = string(cue["ref"], cw + ".ref", REF)
                data["offset"] = number(cue.get("offset", 0), cw + ".offset")
            if "d" in cue:
                data["d"] = number(cue["d"], cw + ".d", positive=True)
            for key in ("text", "source"):
                if key in cue:
                    data[key] = string(cue[key], cw + "." + key)
            cue_defs[cid] = data
        cursor += hold

    for i, scene in enumerate(scenes[:-1]):
        if scene["end"] > scenes[i + 1]["holdEnd"]:
            raise ManifestError(f"scene {scene['id']!r}: overlap cannot extend past the next scene's hold")

    # Exact rational sums precede one half-up quantization of each absolute boundary.
    def quantize(t):
        frame = t * fps / speed
        return (2 * frame.numerator + frame.denominator) // (2 * frame.denominator)

    def seconds(frame):
        value = frame / fps
        if value == float("inf"):
            raise ManifestError("timeline is too large to represent in JSON seconds")
        return value

    result_scenes, cuts = [], []
    for i, scene in enumerate(scenes):
        start, hold_end, end = (quantize(scene[k]) for k in ("start", "holdEnd", "end"))
        if hold_end <= start:
            raise ManifestError(f"scene {scene['id']!r}: hold collapses below one frame after quantization")
        if scene["transition"]["type"] == "overlap" and end <= hold_end:
            raise ManifestError(f"scene {scene['id']!r}: overlap collapses below one frame after quantization")
        row = {"id": scene["id"], "start": seconds(start), "end": seconds(end),
               "holdEnd": seconds(hold_end), "startFrame": start, "endFrame": end,
               "holdEndFrame": hold_end}
        if i < len(scenes) - 1:
            row["transition"] = {"type": scene["transition"]["type"], "duration": seconds(end - hold_end)}
            if row["transition"]["type"] == "cut":
                cuts.append(seconds(hold_end))
        result_scenes.append(row)

    resolved, visiting = {}, set()

    def cue_time(cid):
        if cid in resolved:
            return resolved[cid]
        if cid not in cue_defs:
            raise ManifestError(f"unknown cue reference: {cid!r}")
        if cid in visiting:
            raise ManifestError(f"cyclic cue reference: {cid!r}")
        visiting.add(cid)
        cue = cue_defs[cid]
        t = cue["t"] if "t" in cue else cue_time(cue["ref"]) + cue["offset"]
        scene = cue["scene"]
        if not scene["start"] <= t < scene["end"]:
            raise ManifestError(f"{cue['where']}: cue {cid!r} is outside its scene [start, end)")
        if t + cue.get("d", 0) > scene["end"]:
            raise ManifestError(f"{cue['where']}.d: cue window extends beyond its scene")
        visiting.remove(cid)
        resolved[cid] = t
        return t

    cues = []
    for cid, data in cue_defs.items():
        t = cue_time(cid)
        frame = quantize(t)
        scene = data["scene"]
        if not quantize(scene["start"]) <= frame < quantize(scene["end"]):
            raise ManifestError(f"{data['where']}: cue falls outside its scene after quantization")
        cue = {"id": cid, "scene": scene["id"], "t": seconds(frame)}
        if "d" in data:
            last = quantize(t + data["d"])
            if last <= frame:
                raise ManifestError(f"{data['where']}.d: cue window collapses below one frame")
            cue["d"] = seconds(last - frame)
        for key in ("text", "source"):
            if key in data:
                cue[key] = data[key]
        cues.append(cue)
    cues.sort(key=lambda c: (c["t"], c["id"]))
    duration_frames = result_scenes[-1]["endFrame"]
    return {"version": 1, "fps": fps, "size": size,
            "duration": seconds(duration_frames), "durationFrames": duration_frames,
            "scenes": result_scenes, "cuts": cuts, "cues": cues,
            "source": {"path": str(source_path), "sha256": source_sha256}, "speed": float(speed)}


def atomic_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix="." + path.name + ".", suffix=".tmp", delete=False) as handle:
            temp = handle.name
            json.dump(data, handle, ensure_ascii=False, indent=2, allow_nan=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
    finally:
        if temp is not None and os.path.exists(temp):
            os.unlink(temp)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--src", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--speed", default="1", help="Positive speed: .75 makes the film 4/3 as long")
    args = parser.parse_args()
    try:
        if args.src.resolve() == args.out.resolve():
            raise ManifestError("--out must not overwrite the source manifest")
        manifest, digest = read_manifest(args.src)
        try:
            speed = Decimal(args.speed)
        except ArithmeticError:
            raise ManifestError("speed: expected a positive finite number") from None
        timeline = compile_manifest(manifest, source_path=args.src.resolve(), source_sha256=digest, speed=speed)
        atomic_json(args.out, timeline)
    except (ManifestError, OSError, OverflowError, RecursionError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(f"{args.out}: {timeline['durationFrames']} frames, {timeline['duration']:.3f}s at {timeline['fps']} fps")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
