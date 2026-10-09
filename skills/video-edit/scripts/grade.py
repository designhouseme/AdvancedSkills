#!/usr/bin/env python3
"""Grade our footage toward a reference video's look: a 3D LUT from colour statistics.

Samples frames from the reference (a TikTok the user likes) and from our source, measures each in
CIELAB (mean and spread of lightness and of the two colour axes) and builds a 33^3 .cube that moves
our statistics toward the reference's (Reinhard colour transfer), at a chosen strength, separately for
colour and for lightness. cut.py applies it with lut3d to the footage only (not to inserts or text).

What it can't do: the reference's look is also its light and its subject (a dark room, black clothes).
Matching statistics will darken a bright warm scene and can tint skin; that is why the default
strength is 0.5 for colour and 0.35 for lightness, and why the A/B still is part of the output.

Usage:
  python grade.py --ref ref.mp4 --src source.mp4 [--src-range 190-560] --out edit/look.cube \
                  [--color 0.5] [--luma 0.35] [--ab edit/grade_ab.png --at 200]
"""
import argparse, subprocess
from pathlib import Path
import numpy as np
import cv2


def frames(path, n=30, rng=None):
    d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                             capture_output=True, text=True).stdout)
    a, b = rng or (d * 0.05, d * 0.95)
    out = []
    for t in np.linspace(a, b, n):
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", path, "-frames:v", "1",
                              "-vf", "scale=270:480", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                             capture_output=True).stdout
        if len(raw) == 270 * 480 * 3:
            out.append(np.frombuffer(raw, np.uint8).reshape(480, 270, 3))
    return out


def lab_stats(imgs):
    px = np.concatenate([cv2.cvtColor(im.astype(np.float32) / 255, cv2.COLOR_RGB2LAB).reshape(-1, 3) for im in imgs])
    return px.mean(0), px.std(0) + 1e-6


def build_lut(src_stats, ref_stats, color, luma, size=33):
    (ms, ss), (mr, sr) = src_stats, ref_stats
    g = np.linspace(0, 1, size, dtype=np.float32)
    b, gg, r = np.meshgrid(g, g, g, indexing="ij")              # .cube order: red changes fastest
    rgb = np.stack([r, gg, b], -1).reshape(-1, 1, 3)
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB).reshape(-1, 3)
    moved = (lab - ms) / ss * sr + mr
    w = np.array([luma, color, color], dtype=np.float32)
    lab2 = lab + (moved - lab) * w
    out = cv2.cvtColor(lab2.reshape(-1, 1, 3).astype(np.float32), cv2.COLOR_LAB2RGB).reshape(-1, 3)
    return np.clip(out, 0, 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", required=True); ap.add_argument("--src", required=True)
    ap.add_argument("--src-range"); ap.add_argument("--out", required=True)
    ap.add_argument("--color", type=float, default=0.5); ap.add_argument("--luma", type=float, default=0.35)
    ap.add_argument("--ab"); ap.add_argument("--at", type=float, default=None)
    a = ap.parse_args()
    rng = tuple(map(float, a.src_range.split("-"))) if a.src_range else None
    rs, ss = lab_stats(frames(a.ref)), lab_stats(frames(a.src, rng=rng))
    lut = build_lut(ss, rs, a.color, a.luma)
    with open(a.out, "w") as f:
        f.write(f'TITLE "look from {Path(a.ref).name}"\nLUT_3D_SIZE 33\n')
        f.writelines(f"{x:.6f} {y:.6f} {z:.6f}\n" for x, y, z in lut)
    print(f"reference L/a/b mean {np.round(rs[0], 1)} sd {np.round(rs[1], 1)}")
    print(f"source    L/a/b mean {np.round(ss[0], 1)} sd {np.round(ss[1], 1)}")
    print(f"LUT -> {a.out} (colour {a.color}, lightness {a.luma})")
    if a.ab:                                  # before | after at one moment of the source
        t = a.at if a.at is not None else (rng[0] + 5 if rng else 5)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", a.src, "-frames:v", "1", "-filter_complex",
                        f"[0:v]scale=540:-2,split[x][y];[y]lut3d=file='{a.out}':interp=tetrahedral[z];[x][z]hstack",
                        a.ab], check=True)
        print(f"A/B -> {a.ab}")


if __name__ == "__main__":
    main()
