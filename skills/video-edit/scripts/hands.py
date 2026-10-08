#!/usr/bin/env python3
"""Track the speaker's hands in the used parts of the source: where the fingers are and what they say.

Samples every --step seconds inside each segment of cuts.json (source time), runs MediaPipe's hand
landmarker (21 points per hand) and writes hands.json:
  {"t": src_s, "hands": [{"side", "wrist": [x, y], "tips": {"thumb"...}, "up": n_fingers_extended,
                          "gesture": "point" | "count" | "open" | "fist", "anchor": [x, y], "box": [...]}]}
in source pixels. `anchor` is where an element belongs: just above the highest extended fingertip
(the index tip for a point). With --summary it prints the gesture timeline next to the words, so the
editor can see "18.9-19.6 count 2 (right hand) 'Facebook'" and anchor an effect there.

Needs: pip mediapipe; the model ~/.cache/video-edit/models/hand_landmarker.task (MediaPipe, Apache-2.0).

Usage:
  python hands.py --src source.mp4 --cuts edit/cuts.json --out edit/hands.json [--step 0.1]
  python hands.py --hands edit/hands.json --words edit/words.json --summary
"""
import argparse, json, subprocess
from pathlib import Path
import numpy as np

MODEL = Path.home() / ".cache/video-edit/models/hand_landmarker.task"
TIPS = {"thumb": 4, "index": 8, "middle": 12, "ring": 16, "pinky": 20}
PIPS = {"index": 6, "middle": 10, "ring": 14, "pinky": 18}


def describe(lm, W, H):
    p = lambda i: np.array([lm[i].x * W, lm[i].y * H])
    wrist = p(0)
    size = np.linalg.norm(p(9) - wrist) + 1e-6           # palm length, the hand's own scale
    ext = {f: np.linalg.norm(p(TIPS[f]) - wrist) > np.linalg.norm(p(PIPS[f]) - wrist) * 1.12
           and np.linalg.norm(p(TIPS[f]) - p(PIPS[f])) > 0.35 * size for f in PIPS}
    ext = {f: bool(v) for f, v in ext.items()}
    up = int(sum(ext.values()))
    if ext["index"] and not (ext["middle"] or ext["ring"] or ext["pinky"]):
        gesture = "point"
    elif up >= 4:
        gesture = "open"
    elif up == 0:
        gesture = "fist"
    else:
        gesture = "count"
    tips = {f: p(i).round().tolist() for f, i in TIPS.items()}
    ext_tips = [p(TIPS[f]) for f in PIPS if ext[f]] or [p(9)]
    top = min(ext_tips, key=lambda v: v[1])
    anchor = (top + np.array([0, -0.45 * size])).round().tolist()
    xs = [lm[i].x * W for i in range(21)]
    ys = [lm[i].y * H for i in range(21)]
    direction = (p(8) - p(5)) / (np.linalg.norm(p(8) - p(5)) + 1e-6)
    return {"wrist": wrist.round().tolist(), "tips": tips, "up": up, "gesture": gesture,
            "anchor": anchor, "dir": direction.round(3).tolist(), "size": round(float(size)),
            "box": [round(min(xs)), round(min(ys)), round(max(xs)), round(max(ys))]}


def track(a):
    import mediapipe as mp
    from mediapipe.tasks.python import vision, BaseOptions
    cuts = json.load(open(a.cuts))
    pr = json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                    "stream=width,height", "-of", "json", a.src], capture_output=True, text=True).stdout)
    W, H = pr["streams"][0]["width"], pr["streams"][0]["height"]
    w2, h2 = W // 2, H // 2
    opts = vision.HandLandmarkerOptions(base_options=BaseOptions(model_asset_path=str(MODEL)),
                                        running_mode=vision.RunningMode.VIDEO, num_hands=2,
                                        min_hand_detection_confidence=0.5, min_tracking_confidence=0.5)
    out, ts_ms = [], 0
    with vision.HandLandmarker.create_from_options(opts) as det:
        for s in cuts["segments"]:
            a0, a1 = s["in"], s["out"]
            buf = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{a0:.3f}", "-to", f"{a1:.3f}", "-i", a.src,
                                  "-vf", f"fps={1 / a.step},scale={w2}:{h2},format=rgb24", "-f", "rawvideo", "-"],
                                 capture_output=True, check=True).stdout
            n = len(buf) // (w2 * h2 * 3)
            frames = np.frombuffer(buf[: n * w2 * h2 * 3], dtype=np.uint8).reshape(n, h2, w2, 3)
            ts_ms += 5000                              # a gap between segments resets the tracker's smoothing
            for k, f in enumerate(frames):
                ts_ms += int(a.step * 1000)
                r = det.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(f)), ts_ms)
                hands = []
                for lm, hd in zip(r.hand_landmarks, r.handedness):
                    d = describe(lm, W, H)
                    d["side"] = hd[0].category_name
                    hands.append(d)
                out.append({"t": round(a0 + k * a.step, 3), "hands": hands})
    json.dump({"width": W, "height": H, "step": a.step, "samples": out}, open(a.out, "w"))
    print(f"{len(out)} samples, {sum(len(x['hands']) > 0 for x in out)} with a hand")


def summary(a):
    """Gesture runs (same hand, same gesture and finger count, >= 0.3 s) with the words said then."""
    data = json.load(open(a.hands))["samples"]
    words = json.load(open(a.words))["words"] if a.words else []
    runs = []
    for smp in data:
        for h in smp["hands"]:
            key = (h["side"], h["gesture"], h["up"] if h["gesture"] == "count" else 0)
            if h["gesture"] == "fist":
                continue
            r = next((r for r in runs if r["key"] == key and smp["t"] - r["t1"] <= 0.25), None)
            if r:
                r["t1"] = smp["t"]; r["pts"].append(h["anchor"])
            else:
                runs.append({"key": key, "t0": smp["t"], "t1": smp["t"], "pts": [h["anchor"]]})
    for r in sorted(runs, key=lambda r: r["t0"]):
        if r["t1"] - r["t0"] < 0.3:
            continue
        side, g, n = r["key"]
        ax, ay = np.median(np.array(r["pts"]), axis=0)
        said = " ".join(w["word"] for w in words if r["t0"] - 0.3 <= w["start"] <= r["t1"] + 0.2)
        label = f"count {n}" if g == "count" else g
        print(f"  {r['t0']:7.2f}-{r['t1']:7.2f}  {label:8s} {side:5s} at ({ax:.0f},{ay:.0f})  {said}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src"); ap.add_argument("--cuts"); ap.add_argument("--out")
    ap.add_argument("--step", type=float, default=0.1)
    ap.add_argument("--hands"); ap.add_argument("--words"); ap.add_argument("--summary", action="store_true")
    a = ap.parse_args()
    summary(a) if a.summary else track(a)


if __name__ == "__main__":
    main()
