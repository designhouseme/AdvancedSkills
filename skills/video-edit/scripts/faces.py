#!/usr/bin/env python3
"""Track the speaker's face in the used parts of the source, for placing captions clear of it.

Samples every --step seconds inside each segment of cuts.json (source time), detects faces with
OpenCV's bundled Haar frontal cascade on a half-size grey frame, keeps the largest, smooths with a
median over 3 samples and writes faces.json: [{"t": src_s, "x", "y", "w", "h"}] in source pixels.
Frames without a detection (a hand in front, a turn away) are skipped, not guessed.

Usage:
  python faces.py --src source.mp4 --cuts edit/cuts.json --out edit/faces.json [--step 0.2]
"""
import argparse, json, subprocess
import numpy as np
import cv2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--cuts", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--step", type=float, default=0.2)
    a = ap.parse_args()

    cuts = json.load(open(a.cuts))
    pr = json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                    "stream=width,height", "-of", "json", a.src], capture_output=True, text=True).stdout)
    W, H = pr["streams"][0]["width"], pr["streams"][0]["height"]
    w2, h2 = W // 2, H // 2
    det = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    raw = []
    for s in cuts["segments"]:
        a0, a1 = s["in"] - 0.2, s["out"] + 0.2
        buf = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{a0:.3f}", "-to", f"{a1:.3f}", "-i", a.src,
                              "-vf", f"fps={1 / a.step},scale={w2}:{h2},format=gray", "-f", "rawvideo", "-"],
                             capture_output=True, check=True).stdout
        n = len(buf) // (w2 * h2)
        frames = np.frombuffer(buf[: n * w2 * h2], dtype=np.uint8).reshape(n, h2, w2)
        for k, f in enumerate(frames):
            found = det.detectMultiScale(f, scaleFactor=1.1, minNeighbors=6, minSize=(60, 60))
            if len(found):
                x, y, w, h = max(found, key=lambda b: b[2] * b[3])
                raw.append({"t": round(a0 + k * a.step, 3), "x": int(x) * 2, "y": int(y) * 2, "w": int(w) * 2, "h": int(h) * 2})
    raw.sort(key=lambda r: r["t"])
    # The cascade sometimes takes a fist or a sweater sleeve for the largest face; one such sample
    # pushes a whole segment's captions above the head. Drop samples whose centre is over 120 px
    # from the median centre of the samples within ±1.2 s.
    cx = lambda r: (r["x"] + r["w"] / 2, r["y"] + r["h"] / 2)
    kept = []
    for r in raw:
        near = [cx(q) for q in raw if abs(q["t"] - r["t"]) <= 1.2]
        mx, my = np.median([c[0] for c in near]), np.median([c[1] for c in near])
        x, y = cx(r)
        if ((x - mx) ** 2 + (y - my) ** 2) ** 0.5 <= 120:
            kept.append(r)
    if len(kept) < len(raw):
        print(f"dropped {len(raw) - len(kept)} outlier detections (hands, sleeves)")
    raw = kept
    out = []
    for i, r in enumerate(raw):                      # median of 3 neighbours, per coordinate
        win = raw[max(0, i - 1): i + 2]
        out.append({"t": r["t"], **{k: int(np.median([q[k] for q in win])) for k in ("x", "y", "w", "h")}})
    json.dump({"width": W, "height": H, "faces": out}, open(a.out, "w"), indent=0)
    ys = [f["y"] + f["h"] for f in out]
    print(f"{len(out)} face samples; chin (box bottom) in source y {min(ys)}-{max(ys)} px")


if __name__ == "__main__":
    main()
