#!/usr/bin/env python3
"""Build the reusable transition clip, once per machine.

  ~/.cache/video-edit/fx/burn_<W>x<H>_<fps>.mp4   film burn + shutter flash on black, 16 frames,
                                                   the cut on frame 8; laid over the film with a
                                                   screen blend (black changes nothing)

Sounds are not made here. Synthesised whooshes and clicks were tried and sounded bad (review,
9.10.2026); every sound comes from recorded files in ~/.cache/video-edit/sfx/ (see SKILL.md).

Usage: python fxassets.py [--size 1080x1920] [--fps 25]
"""
import argparse, subprocess
from pathlib import Path
import numpy as np

HOME = Path.home() / ".cache/video-edit"


def burn_clip(W, H, fps, out):
    """Warm light leaks sweeping across, peaking on the cut, with a 3-frame shutter flash."""
    n, w, h = 16, 270, 480
    rng = np.random.default_rng(7)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    cols = np.array([[1.0, 0.48, 0.10], [0.91, 0.21, 0.12], [1.0, 0.76, 0.29]], dtype=np.float32)
    blobs = [(-0.3, 0.30, 0.55, 0), (-0.6, 0.65, 0.45, 1), (-0.1, 0.85, 0.35, 2)]
    frames = []
    for k in range(n):
        p = k / (n - 1)
        env = np.exp(-((k - 8) / 3.2) ** 2)                      # peaks on the cut frame
        img = np.zeros((h, w, 3), np.float32)
        for x0, yc, r, ci in blobs:
            cx = (x0 + 1.6 * p) * w
            cy = yc * h + 0.05 * h * np.sin(6 * p + ci)
            g = np.exp(-(((xx - cx) / (r * w)) ** 2 + ((yy - cy) / (r * 1.6 * w)) ** 2))
            img += g[..., None] * cols[ci]
        img *= 0.95 * env
        flash = {7: 0.35, 8: 0.85, 9: 0.3}.get(k, 0.0)          # the shutter
        img = 1 - (1 - img) * (1 - flash)
        img += rng.normal(0, 0.02 * env, img.shape).astype(np.float32)   # a little grain in the burn
        frames.append((np.clip(img, 0, 1) * 255).astype(np.uint8))
    raw = b"".join(f.tobytes() for f in frames)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}",
                    "-r", str(fps), "-i", "-", "-vf", f"scale={W}:{H}:flags=bicubic,gblur=sigma=6",
                    "-c:v", "libx264", "-crf", "12", "-pix_fmt", "yuv420p", str(out)], input=raw, check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", default="1080x1920")
    ap.add_argument("--fps", type=int, default=25)
    a = ap.parse_args()
    W, H = map(int, a.size.split("x"))
    (HOME / "fx").mkdir(parents=True, exist_ok=True)
    burn = HOME / "fx" / f"burn_{W}x{H}_{a.fps}.mp4"
    if not burn.exists():
        burn_clip(W, H, a.fps, burn)
    print(burn)


if __name__ == "__main__":
    main()
