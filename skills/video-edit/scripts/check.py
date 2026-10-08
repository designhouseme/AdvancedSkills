#!/usr/bin/env python3
"""Check a finished edit and build the review images. Prints ERROR / WARNING / OK lines.

Measured (no vision needed):
  duration, size, fps, BT.709 tags; frozen or black stretches (0.3 s, not ffmpeg's 2 s default);
  integrated loudness and true peak against the target; cuts per second against the short-form
  band (0.19-0.52 cuts/s for talking heads, Dost & Huang 2026); caption pages: not flashing
  (under 0.35 s) and not faster than 20 characters per second.

Review images (for the model to look at, each under 2000 px):
  strips_N.png   one row per cut: frames at -0.12, -0.04, +0, +0.04, +0.12 s around the cut and the
                 waveform of the second around it, so a clipped word or a jump that needs a
                 punch-in shows up before anyone watches the film
  frames.png     the first frame (the TikTok cover) and one frame per caption style moment

Usage:
  python check.py --film final.mp4 --work edit/ [--lufs -14] [--tp -1.5] [--max 60]
"""
import argparse, json, re, subprocess
from pathlib import Path


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def ff(*args):
    return run(["ffmpeg", "-hide_banner", "-nostats", *args]).stderr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--film", required=True)
    ap.add_argument("--work", required=True)
    ap.add_argument("--lufs", type=float, default=-14)
    ap.add_argument("--tp", type=float, default=-1.5)
    ap.add_argument("--max", type=float, default=90, help="longest allowed length in seconds")
    a = ap.parse_args()
    work = Path(a.work)
    cuts = json.load(open(work / "cuts.json"))
    pages = json.load(open(work / "captions.json"))
    res = []

    p = json.loads(run(["ffprobe", "-v", "error", "-show_entries",
                        "stream=codec_type,width,height,r_frame_rate,color_primaries,color_transfer,color_space:format=duration",
                        "-of", "json", a.film]).stdout)
    v = next(s for s in p["streams"] if s["codec_type"] == "video")
    dur = float(p["format"]["duration"])
    res.append(("OK" if dur <= a.max else "ERROR", f"length {dur:.2f} s (limit {a.max:.0f} s)"))
    res.append(("OK" if (v["width"], v["height"]) == (1080, 1920) else "WARNING", f"size {v['width']}x{v['height']}"))
    tags = (v.get("color_primaries"), v.get("color_transfer"), v.get("color_space"))
    res.append(("OK" if tags == ("bt709", "bt709", "bt709") else "ERROR", f"colour tags {tags}"))

    e = ff("-i", a.film, "-vf", "freezedetect=n=-60dB:d=0.3,blackdetect=d=0.2:pix_th=0.08", "-an", "-f", "null", "-")
    frozen = re.findall(r"freeze_start: ([\d.]+)", e)
    black = re.findall(r"black_start:([\d.]+)", e)
    res.append(("ERROR" if frozen else "OK", f"frozen stretches over 0.3 s: {frozen or 'none'}"))
    res.append(("ERROR" if black else "OK", f"black stretches over 0.2 s: {black or 'none'}"))

    e = ff("-i", a.film, "-vn", "-af", "ebur128=peak=true", "-f", "null", "-")
    I = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", e)[-1])
    TP = float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", e)[-1])
    res.append(("OK" if abs(I - a.lufs) <= 1 else "ERROR", f"loudness {I:.1f} LUFS (target {a.lufs})"))
    res.append(("OK" if TP <= a.tp + 0.3 else "ERROR", f"true peak {TP:.1f} dBTP (limit {a.tp})"))

    n_cuts = len(cuts["segments"]) - 1
    rate = n_cuts / dur
    res.append(("OK" if 0.19 <= rate <= 0.52 else "WARNING",
                f"{n_cuts} cuts, {rate:.2f} cuts/s (talking-head band 0.19-0.52, median 0.33)"))
    short = [s for s in cuts["segments"] if s["out"] - s["in"] < 0.8]
    if short:
        res.append(("WARNING", f"segments under 0.8 s: {[(s['in'], s['out']) for s in short]}"))
    for w in cuts.get("warnings", []):
        res.append(("WARNING", w))

    words_mode = "Style: W," in (work / "captions.ass").read_text(encoding="utf-8") if (work / "captions.ass").exists() else False
    flash = 0.1 if words_mode else 0.35       # one word at a time follows the speech: 0.2-0.3 s is normal
    for pg in pages:
        d = pg["end"] - pg["start"]
        text = " ".join(pg["words"])
        if d < flash:
            res.append(("WARNING", f"caption '{text}' on screen {d:.2f} s"))
        if not words_mode and len(text) / max(d, 0.01) > 25 and d < 0.5:   # synced pages follow speech pace
            res.append(("WARNING", f"caption '{text}' at {len(text) / d:.0f} chars/s"))
    res.append(("OK", f"{len(pages)} caption pages"))
    clear = [(pg["clearance"], " ".join(pg["words"])) for pg in pages if pg.get("clearance") is not None]
    if clear:
        c, t = min(clear)
        res.append(("ERROR" if c < 0 else "WARNING" if c < 20 else "OK", f"captions clear of the chin by at least {c} px ('{t}')"))
    elif pages:
        res.append(("WARNING", "caption position not checked against the face (no faces.json)"))

    # review images
    strips = work / "strips"
    strips.mkdir(exist_ok=True)
    for f in strips.glob("*.png"):
        f.unlink()
    rows = []
    for k, s in enumerate(cuts["segments"][1:], 1):
        c = s["out_start"]
        tiles = []
        for j, off in enumerate((-0.12, -0.04, 0.0, 0.04, 0.12)):
            out = strips / f"c{k:02d}_{j}.png"
            run(["ffmpeg", "-v", "error", "-y", "-ss", f"{max(0, c + off):.3f}", "-i", a.film, "-frames:v", "1",
                 "-vf", f"scale=200:-2,drawtext=text='{off:+.2f}':x=6:y=6:fontsize=22:fontcolor=white:box=1:boxcolor=black@0.6",
                 str(out)])
            tiles.append(out)
        wave = strips / f"c{k:02d}_w.png"
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{max(0, c - 0.5):.3f}", "-t", "1", "-i", a.film,
             "-filter_complex", "showwavespic=s=1000x90:colors=white,drawbox=x=499:y=0:w=2:h=90:color=red@0.9:t=fill",
             "-frames:v", "1", str(wave)])
        row = strips / f"row{k:02d}.png"
        inputs = sum((["-i", str(t)] for t in tiles + [wave]), [])
        run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex",
             "[0][1][2][3][4]hstack=5[top];[top][5]vstack,"
             f"drawtext=text='cut {k} at {c:.2f}s (src {s['in']:.2f})':x=8:y=h-120:fontsize=24:fontcolor=yellow:box=1:boxcolor=black@0.7",
             str(row)])
        rows.append(row)
    for n in range(0, len(rows), 4):
        group = rows[n:n + 4]
        inputs = sum((["-i", str(r)] for r in group), [])
        out = work / f"strips_{n // 4 + 1}.png"
        if len(group) > 1:
            run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", f"vstack=inputs={len(group)}", str(out)])
        else:
            run(["ffmpeg", "-v", "error", "-y", *inputs, str(out)])
    for f in strips.glob("c*.png"):
        f.unlink()

    times = [0.0] + [round((pg["start"] + pg["end"]) / 2, 2) for pg in pages[:: max(1, len(pages) // 5)]][:5]
    frames = []
    for j, t in enumerate(times):
        out = strips / f"f{j}.png"
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", a.film, "-frames:v", "1", "-vf",
             f"scale=320:-2,drawtext=text='{t:.2f}s':x=6:y=6:fontsize=22:fontcolor=white:box=1:boxcolor=black@0.6", str(out)])
        frames.append(out)
    inputs = sum((["-i", str(f)] for f in frames), [])
    run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", f"hstack=inputs={len(frames)}", str(work / "frames.png")])

    for level, msg in res:
        print(f"{level:7s} {msg}")
    print(f"review: {', '.join(str(p) for p in sorted(work.glob('strips_*.png')))}, {work / 'frames.png'}")
    return 1 if any(l == "ERROR" for l, _ in res) else 0


if __name__ == "__main__":
    raise SystemExit(main())
