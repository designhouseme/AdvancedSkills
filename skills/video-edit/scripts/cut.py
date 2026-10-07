#!/usr/bin/env python3
"""Render an edit from edit.json: snapped cuts, punch-ins, captions, loudness, plus an EDL for an editor.

The model writes edit.json (which takes, in what order, what framing); this script does the mechanics
the model can't hear or see precisely:
  - every in/out point (chosen by the model in a pause) is pulled tight to the speech: 0.04 s before
    the onset, 0.06 s after the phrase has decayed, then onto a frame boundary;
  - each segment gets 15 ms audio fades so joins don't click;
  - framing per segment: zoom [start, end] around the focus point, cropped from the source;
  - full-screen inserts (motion graphics rendered elsewhere) over the speaker's voice;
  - captions from the approved text, in phrases the model marks with "|", on a pill;
  - two-pass loudnorm to the target, BT.709 tags written with setparams, x264 for TikTok/Reels;
  - a CMX3600 EDL with the source timecode, so the cut opens in Resolve/Premiere for finishing.

Writes into --work: cuts.json, captions.ass, captions.json, edit.edl. The film goes to --out.

Usage:
  python cut.py --edit edit.json --words edit/words.json --audio edit/audio.json --work edit/ --out final.mp4 [--draft]
"""
import argparse, json, math, re, subprocess, sys
from pathlib import Path

PRE, POST = 0.04, 0.06          # kept before the speech onset / after the phrase decays (s); wider pads
                                # read as a late cut (0.2 s after the phrase was called sloppy in review)
FADE = 0.015                    # audio fade at every join (s)


def load(p):
    return json.load(open(p, encoding="utf-8"))


# ---------- snapping ----------

class Env:
    """Loudness per 10 ms and the speech runs in it. Cuts are placed from the audio, because
    Whisper's word times are only a hint: early by ~150 ms, and off by over a second after a pause."""

    def __init__(self, audio):
        self.hop, self.db = audio["hop"], audio["db"]
        s = sorted(self.db)
        self.thr = s[len(s) // 10] + 18          # speech threshold: noise floor (p10) + 18 dB
        self.thr_end = self.thr + 8              # a phrase has ended once it decays below this
        raw, start = [], None
        for k, v in enumerate(self.db + [-120.0]):
            if v > self.thr and start is None:
                start = k
            elif v <= self.thr and start is not None:
                if (k - start) * self.hop >= 0.04:   # drop single-frame blips before bridging
                    raw.append([start, k])
                start = None
        runs = []
        for a, b in raw:
            if runs and (a - runs[-1][1]) * self.hop < 0.08:
                runs[-1][1] = b                      # bridge gaps under 80 ms (stop closures)
            else:
                runs.append([a, b])
        self.runs = [(a * self.hop, b * self.hop) for a, b in runs]

    def loud(self, t):
        k = int(round(t / self.hop))                 # 2 of 3 frames, so a single-frame blip isn't speech
        return sum(self.db[max(0, min(len(self.db) - 1, j))] > self.thr for j in (k - 1, k, k + 1)) >= 2

    def speech_in(self, a, b):
        """Speech intervals inside [a, b], pauses under 0.25 s bridged (words run across them)."""
        out = []
        for ra, rb in self.runs:
            ra, rb = max(ra, a), min(rb, b)
            if rb <= ra:
                continue
            if out and ra - out[-1][1] < 0.25:
                out[-1][1] = rb
            else:
                out.append([ra, rb])
        return out or [[a, b]]


VOWELS = set("aąeęioóuyAĄEĘIOÓUY")


def time_words(env, text, a, b):
    """Spread the approved text over the speech in [a, b], by syllables, skipping pauses."""
    toks = text.split()
    weight = [max(1, 2 * sum(c.isdigit() for c in t)) if any(c.isdigit() for c in t)
              else max(1, sum(c in VOWELS for c in t)) for t in toks]
    spans = env.speech_in(a, b)
    total_t = sum(rb - ra for ra, rb in spans)

    def at(frac):
        left = frac * total_t
        for ra, rb in spans:
            if left <= rb - ra:
                return ra + left
            left -= rb - ra
        return spans[-1][1]
    out, acc, total_w = [], 0, sum(weight)
    for tok, wgt in zip(toks, weight):
        out.append({"word": tok, "start": round(at(acc / total_w), 3), "end": round(at((acc + wgt) / total_w), 3)})
        acc += wgt
    return out


def snap_in(env, t, warn):
    """`t` is the model's in-point, chosen in the silence before the first kept word (from --runs).
    Trim the leading silence to PRE; a point inside speech stays as it is and gets a warning."""
    if env.loud(t):
        warn.append(f"in-point {t:.2f} is inside speech: a micro-cut, check it in the strip and the re-transcript")
        return t
    # The onset is the first voiced stretch (3 frames above the phrase level), not the first frame
    # above the noise: a breath or a click before the word otherwise leaves 0.2-0.5 s of slack.
    # From there, step back at most 120 ms over the quieter attack (a soft "j", "s", "w").
    k0 = k = int(round(t / env.hop))
    n = len(env.db)
    while k < n - 3 and not all(env.db[k + j] > env.thr_end for j in range(3)) and (k - k0) * env.hop < 3.0:
        k += 1
    m = k
    while m > k0 and (k - m) * env.hop < 0.12 and env.db[m - 1] > env.thr:
        m -= 1
    return max(t, m * env.hop - PRE)


def snap_out(env, t, warn):
    if env.loud(t):
        warn.append(f"out-point {t:.2f} is inside speech: a micro-cut, check it in the strip and the re-transcript")
        return t
    k = int(round(t / env.hop))
    while k > 0 and env.db[k] <= env.thr_end and (t - k * env.hop) < 3.0:
        k -= 1                                   # last 10 ms frame before the phrase's decay tail
    return min(t, (k + 1) * env.hop + POST)


def print_runs(env, words, a, b):
    """The edit's map: speech runs from loudness with the words Whisper put near them. Whisper's
    times drift, so a word may sit one run early; read the words as a hint, the runs as the truth."""
    for ra, rb in env.runs:
        if rb < a or ra > b:
            continue
        ws = [w["word"] for w in words if ra - 0.4 <= w["start"] < rb]
        print(f"  speech {ra:7.2f}-{rb:7.2f}  {' '.join(ws)}")


def frame(t, fps, mode):
    f = t * fps
    return (math.floor(f + 1e-6) if mode == "down" else math.ceil(f - 1e-6)) / fps


def kept_words(words, a, b):
    return [w for w in words if a - 0.05 <= (w["start"] + w["end"]) / 2 <= b + 0.05]


def aligned_words(src, a, b, tokens, warn):
    """Word times by forced alignment of the approved text (align.py); None if the aligner isn't
    installed or the path is implausible, and the caller keeps the syllable spread."""
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from align import align_words
        import numpy as np
    except ImportError as e:
        warn.append(f"no aligner ({e.name}): caption word times are a syllable spread")
        return None
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{a}", "-to", f"{b}", "-i", src, "-map", "0:a:0",
                          "-ac", "1", "-ar", "16000", "-f", "f32le", "-"], capture_output=True, check=True).stdout
    res = align_words(np.frombuffer(raw, dtype=np.float32), tokens)
    if res is None:
        warn.append(f"alignment failed for {a:.2f}-{b:.2f}: syllable spread used there")
        return None
    return [{"word": t, "start": a + s, "end": a + e} for t, (s, e) in zip(tokens, res)]


def retranscribe(src, a, b, language):
    """Words for one window, transcribed on their own: for takes where the full-file word times
    are wrong (a long pause or a restart confuses Whisper's alignment)."""
    sys.path.insert(0, str(Path(__file__).parent))
    from transcribe import preload_cuda_libs
    import numpy as np
    preload_cuda_libs()
    from faster_whisper import WhisperModel
    global _MODEL
    if "_MODEL" not in globals():
        _MODEL = WhisperModel("large-v3", device="cuda", compute_type="float16")
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{a}", "-to", f"{b}", "-i", src, "-map", "0:a:0",
                          "-ac", "1", "-ar", "16000", "-f", "f32le", "-"], capture_output=True, check=True).stdout
    segs, _ = _MODEL.transcribe(np.frombuffer(raw, dtype=np.float32), language=language, beam_size=5,
                                word_timestamps=True, condition_on_previous_text=False, vad_filter=False)
    return [{"word": w.word.strip(), "start": a + w.start, "end": a + w.end, "p": w.probability}
            for s in segs for w in (s.words or []) if w.word.strip()]


# ---------- captions ----------

def ass_color(hexrgb, alpha=0):
    h = hexrgb.lstrip("#")
    return f"&H{alpha:02X}{h[4:6]}{h[2:4]}{h[0:2]}".upper()


def ass_time(t):
    t = max(0, t)
    h, m = int(t // 3600), int(t % 3600 // 60)
    return f"{h}:{m:02d}:{t % 60:05.2f}"


def caption_pages(cw, cfg):
    """cw: words in output time. Pages of 1-3 words that stay on screen at least MIN_PAGE seconds:
    in fast speech a page takes more words (up to max_chars) rather than flashing."""
    maxw, maxc, min_dur = cfg.get("max_words", 3), cfg.get("max_chars", 18), cfg.get("min_page", 0.45)
    keep = [tuple(k.split()) for k in cfg.get("keep_together", [])]
    units, i = [], 0                       # words, with "1500 Elo" style pairs as one unit
    while i < len(cw):
        span = next((len(k) for k in keep if tuple(x["text"] for x in cw[i:i + len(k)]) == k), 1)
        units.append(cw[i:i + span])
        i += span
    text = lambda ws: " ".join(x["text"] for x in ws)
    dur = lambda ws: ws[-1]["end"] - ws[0]["start"]
    if cw and all(w.get("chunk") is not None for w in cw):     # phrases marked by the model with "|"
        pages = []
        for w in cw:
            if pages and pages[-1][-1]["chunk"] == w["chunk"]:
                pages[-1].append(w)
            else:
                pages.append([w])
        return page_times(pages, cfg)
    pages, cur = [], []
    for u in units:
        if cur:
            hard = (u[0]["seg"] != cur[-1]["seg"] or re.search(r"[.?!…]$", cur[-1]["raw"])
                    or u[0]["start"] - cur[-1]["end"] > 0.3 or len(text(cur + u)) > maxc)
            comma = re.search(r",$", cur[-1]["raw"]) and dur(cur) >= min_dur    # a comma breaks a page
            if hard or comma or (len(cur) >= maxw and dur(cur) >= min_dur):     # only once it has stood
                pages.append(cur)
                cur = []
        cur += u
    if cur:
        pages.append(cur)
    # A short function word never ends a page when the sentence goes on ("ode | mnie", "w | szachy"):
    # move it to the next page, as Polish typography moves single-letter words to the next line.
    weak = set(cfg.get("weak_words", ["w", "z", "i", "a", "o", "u", "że", "za", "ze", "we", "do", "na",
                                      "od", "ode", "to", "się", "by", "bo", "po", "ma"]))
    for n in range(len(pages) - 1):
        p, q = pages[n], pages[n + 1]
        if (len(p) > 1 and p[-1]["text"] in weak and not re.search(r"[.,?!…]$", p[-1]["raw"])
                and p[-1]["seg"] == q[0]["seg"] and len(text([p[-1]] + q)) <= maxc):
            q.insert(0, p.pop())
    merged = []                            # a page still under 0.4 s joins the next one (on two lines if
    for p in pages:                        # needed), never across a sentence end or a cut
        prev = merged[-1] if merged else None
        if (prev and dur(prev) < 0.4 and len(text(prev + p)) <= 2 * maxc - 6
                and not re.search(r"[.?!…]$", prev[-1]["raw"]) and prev[-1]["seg"] == p[0]["seg"]):
            merged[-1] = prev + p
        else:
            merged.append(p)
    return page_times(merged, cfg)


def page_times(pages, cfg):
    out = []
    seg_start = cfg.get("_seg_starts", [])
    for n, p in enumerate(pages):
        start = p[0]["start"] - 0.08          # a page leads its word by 80 ms, but never across a cut
        if seg_start:
            start = max(start, seg_start[p[0]["seg"]])
        nxt = pages[n + 1][0]["start"] - 0.08 if n + 1 < len(pages) else None
        if nxt is not None and seg_start and pages[n + 1][0]["seg"] != p[0]["seg"]:
            nxt = seg_start[pages[n + 1][0]["seg"]]
        end = p[-1]["end"] + 0.6 if nxt is None else min(nxt, p[-1]["end"] + 0.6)
        if nxt is None and cfg.get("_total"):
            end = min(end, cfg["_total"] - 0.2)  # the last frame shows the speaker, not a caption
        out.append({"start": round(max(start, out[-1]["end"] if out else 0), 3), "end": round(end, 3),
                    "words": [x["text"] for x in p], "seg": p[0]["seg"],
                    "times": [[round(x["start"], 3), round(x["end"], 3)] for x in p]})
    return out


def place_captions(pages, segs, faces, cfg, W, H, fx, fy, gap=30, limit=1460):
    """Caption height from the face track: the pill's top stays `gap` px under the chin in every frame
    it is on screen (the chin in output pixels, through each segment's zoom and crop). One height for
    the whole film when it fits above the TikTok UI (`limit`), else one per segment, else above the head;
    never per page, because a caption that moves between pages reads as a bug."""
    track = faces["faces"]
    ts = [f["t"] for f in track]
    size = cfg.get("size", 74)
    base = cfg.get("y", int(H * 0.64))

    def face_at(src_t):
        import bisect
        k = bisect.bisect_left(ts, src_t)
        best = min((j for j in (k - 1, k) if 0 <= j < len(ts)), key=lambda j: abs(ts[j] - src_t), default=None)
        return track[best] if best is not None and abs(ts[best] - src_t) <= 0.3 else None

    def half_h(p):
        rows = 2 if len(" ".join(p["words"])) > cfg.get("wrap_chars", 20) and len(p["words"]) > 1 else 1
        return (rows * 0.98 * size + 0.34 * size) / 2

    def bounds(p):                     # (lowest chin, highest face top) while the page is up
        chin, top = None, None
        t = p["start"]
        while t <= p["end"]:
            s = next((s for s in segs if s["out_start"] <= t < s["out_start"] + s["out"] - s["in"]), None)
            if s and not any(a <= t < b for a, b, _ in s.get("inserts", [])):
                d = s["out"] - s["in"]
                z = s["zoom"][0] + (s["zoom"][1] - s["zoom"][0]) * (t - s["out_start"]) / d
                f = face_at(s["in"] + t - s["out_start"])
                if f:
                    y0 = min(max(fy * H * z - H / 2, 0), H * z - H)
                    c = (f["y"] + 1.12 * f["h"]) * z - y0
                    tp = (f["y"] - 0.25 * f["h"]) * z - y0
                    chin = c if chin is None else max(chin, c)
                    top = tp if top is None else min(top, tp)
            t += 0.08
        return chin, top

    info = [(p, half_h(p), *bounds(p)) for p in pages]
    need = [(c + gap + hh) if c is not None else base for p, hh, c, _ in info]
    y_all = max([base] + need)
    if y_all + max(hh for _, hh, _, _ in info) <= limit:
        for p, *_ in info:
            p["y"] = round(y_all)
    else:
        for si in {p["seg"] for p in pages}:
            grp = [(p, hh, c, tp) for p, hh, c, tp in info if p["seg"] == si]
            y_s = max([base] + [(c + gap + hh) if c is not None else base for _, hh, c, _ in grp])
            if y_s + max(hh for _, hh, _, _ in grp) > limit:     # no room under the chin: above the head
                tops = [tp for _, _, _, tp in grp if tp is not None]
                y_s = max(260, min(tops) - gap - max(hh for _, hh, _, _ in grp)) if tops else base
            for p, *_ in grp:
                p["y"] = round(y_s)
    for p, hh, c, tp in info:
        p["clearance"] = None if c is None else round(p["y"] - hh - c)     # pill top minus chin, px
    return pages


def pill_path(w, h, r):
    """A rounded rectangle as an ASS drawing (\\p1), origin top-left; r = h/2 makes a pill."""
    k = 0.5523 * r                                # cubic Bézier handle for a quarter circle
    f = lambda *v: " ".join(str(int(round(x))) for x in v)
    return (f"m {f(r, 0)} l {f(w - r, 0)} b {f(w - r + k, 0, w, r - k, w, r)} l {f(w, h - r)} "
            f"b {f(w, h - r + k, w - r + k, h, w - r, h)} l {f(r, h)} b {f(r - k, h, 0, h - r + k, 0, h - r)} "
            f"l {f(0, r)} b {f(0, r - k, r - k, 0, r, 0)}")


def font_file(family, weight="bold"):
    return subprocess.run(["fc-match", "-f", "%{file}", f"{family}:{weight}"], capture_output=True, text=True).stdout


def write_pills(pages, cfg, W, H, lines):
    """Each page on a pill: the drawing sized from the text measured with the same font file
    (libass font size 100 = Pillow size 83.3 for the same width), text centred on it, one soft
    shadow under it, and the same short pop on all three layers."""
    from PIL import ImageFont
    pc = cfg["pill"]
    size, maxc = cfg.get("size", 74), cfg.get("wrap_chars", 20)
    pil = ImageFont.truetype(font_file(cfg.get("font", "Fira Sans"), cfg.get("weight", "bold")), size / 1.2)
    accent = set(cfg.get("accent_words", []))
    padx, pady, line_h = 0.42 * size, 0.17 * size, 0.98 * size
    hp, bh, br = 0.16 * size, 0.94 * size, 0.24 * size          # the active-word box
    pill_pop = r"\fscx92\fscy92\alpha&HFF&\t(0,60,\alpha&H00&)\t(0,150,0.6,\fscx100\fscy100)"
    text_pop = ""          # the text doesn't scale: the word boxes are placed at its final size
    for p in pages:
        words, times = p["words"], p["times"]
        y = p.get("y", cfg.get("y", int(H * 0.64)))
        if len(" ".join(words)) > maxc and len(words) > 1:          # two balanced lines, never
            keep = {tuple(k.split()) for k in cfg.get("keep_together", [])}   # between "134 | tysiące"
            ok = [j for j in range(1, len(words)) if (words[j - 1], words[j]) not in keep] or list(range(1, len(words)))
            k = min(ok, key=lambda j: abs(len(" ".join(words[:j])) - len(" ".join(words[j:]))))
            rows = [words[:k], words[k:]]
        else:
            rows = [words]
        row_w = [pil.getlength(" ".join(r)) for r in rows]
        w = max(row_w) + 2 * padx
        h = len(rows) * line_h + 2 * pady
        r = h / 2 if len(rows) == 1 else 0.36 * line_h
        is_acc = any(x.strip(".,?!") in accent for x in words)
        fill = ass_color(pc.get("accent_fill", "#F2B544") if is_acc else pc.get("fill", "#F5F0E8"))
        ink = ass_color(pc.get("accent_text", pc.get("text", "#17120E")) if is_acc else pc.get("text", "#17120E"))
        box = ass_color(pc.get("accent_box", pc.get("fill", "#F5F0E8")) if is_acc else pc.get("box", pc.get("accent_fill", "#F2B544")))
        t0, t1 = ass_time(p["start"]), ass_time(p["end"])
        path = pill_path(w, h, r)
        a = pc.get("shadow_alpha", "B8")
        lines.append(f"Dialogue: 0,{t0},{t1},Pill,,0,0,0,,{{\\an5\\pos({W // 2},{y + 9})\\1c&H000000&\\1a&H{a}&"
                     f"\\blur9{pill_pop.replace('alpha&H00&', f'alpha&H{a}&')}\\p1}}{path}")
        lines.append(f"Dialogue: 1,{t0},{t1},Pill,,0,0,0,,{{\\an5\\pos({W // 2},{y})\\1c{fill}{pill_pop}\\p1}}{path}")

        # Where each word sits: rows are centred; a word's x comes from the measured prefix string.
        geo = []
        for ri, rw in enumerate(rows):
            left = W / 2 - row_w[ri] / 2
            cy = y + 2 + (ri - (len(rows) - 1) / 2) * line_h
            for j, word in enumerate(rw):
                pre = pil.getlength(" ".join(rw[:j]) + " ") if j else 0
                ww = pil.getlength(word)
                geo.append((left + pre + ww / 2, cy, ww + 2 * hp))
        # The box under the word being said: one event per word, continuous (each lasts until the
        # next word starts), sliding from the previous word in 90 ms and stretching to the new width.
        for i, (cx, cy, bw) in enumerate(geo):
            hs = p["start"] if i == 0 else max(p["start"], times[i][0])
            he = p["end"] if i == len(geo) - 1 else max(hs + 0.04, min(p["end"], times[i + 1][0]))
            bpath = pill_path(bw, bh, br)
            if i == 0:
                anim = f"\\pos({cx:.0f},{cy:.0f})\\alpha&HFF&\\t(0,60,\\alpha&H00&)"
            else:
                px, py, pw = geo[i - 1]
                anim = f"\\move({px:.0f},{py:.0f},{cx:.0f},{cy:.0f},0,90)\\fscx{pw / bw * 100:.0f}\\t(0,90,0.7,\\fscx100)"
            lines.append(f"Dialogue: 2,{ass_time(hs)},{ass_time(he)},Pill,,0,0,0,,{{\\an5{anim}\\1c{box}\\p1}}{bpath}")
        # Text: words not yet said are dimmed and come up to full ink when they are said.
        parts, wi = [], 0
        for ri, rw in enumerate(rows):
            seg = []
            for word in rw:
                ms = int(max(0, times[wi][0] - p["start"]) * 1000)
                seg.append(word if wi == 0 else f"{{\\alpha&H80&\\t({ms},{ms + 70},\\alpha&H00&)}}{word}")
                wi += 1
            parts.append(" ".join(seg))
        lines.append(f"Dialogue: 3,{t0},{t1},Cap,,0,0,0,,{{\\an5\\pos({W // 2},{y + 2})\\1c{ink}{text_pop}}}" + r"\N".join(parts))


def write_ass(pages, cfg, title, W, H, path):
    font, size = cfg.get("font", "Fira Sans"), cfg.get("size", 78)
    col, acc = ass_color(cfg.get("color", "#FFFFFF")), ass_color(cfg.get("accent", "#F5B942"))
    accent = set(cfg.get("accent_words", []))
    y = cfg.get("y", int(H * 0.64))
    if cfg.get("pill"):
        lines = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}", "WrapStyle: 2",
                 "ScaledBorderAndShadow: yes", "", "[V4+ Styles]",
                 "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, "
                 "Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
                 "Alignment, MarginL, MarginR, MarginV, Encoding",
                 f"Style: Cap,{font},{size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1",
                 "Style: Pill,Arial,20,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1",
                 "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
        write_pills(pages, cfg, W, H, lines)
        Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
        return
    lines = [
        "[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}", "WrapStyle: 2",
        "ScaledBorderAndShadow: yes", "", "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, "
        "Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding",
        # A soft dark halo (outline 3 px, blurred, ~60% opaque) instead of a hard drop shadow: it holds
        # white text on a light sweater or a bright window without looking like a meme caption.
        f"Style: Cap,{font},{size},{col},{col},&H60000000,&H00000000,-1,0,0,0,100,100,0,0,1,3,0,5,60,60,0,1",
    ]
    if title:
        tf = title.get("font", font)
        lines.append(f"Style: Title,{tf},{title.get('size', 76)},{ass_color(title.get('color', '#16110D'))},"
                     f"&H00000000,&H00000000,&H00000000,-1,0,0,0,100,100,-1,0,1,0,0,7,0,0,0,1")
    lines += ["", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    pop = r"{\blur3\fscx94\fscy94\alpha&H40&\t(0,90,\fscx100\fscy100\alpha&H00&)}"
    maxc = cfg.get("max_chars", 18)
    for p in pages:
        words = [r"{\c" + acc + "}" + w + r"{\c" + col + "}" if w.strip(".,?!") in accent else w for w in p["words"]]
        if len(" ".join(p["words"])) > maxc and len(words) > 1:     # two balanced lines
            cut_at = min(range(1, len(words)), key=lambda k: abs(len(" ".join(p["words"][:k])) - len(" ".join(p["words"][k:]))))
            txt = " ".join(words[:cut_at]) + r"\N" + " ".join(words[cut_at:])
        else:
            txt = " ".join(words)
        lines.append(f"Dialogue: 1,{ass_time(p['start'])},{ass_time(p['end'])},Cap,,0,0,0,,"
                     rf"{{\pos({W // 2},{y})}}{pop}{txt}")
    if title:
        x, ty = title.get("x", 72), title.get("y", 250)
        t0, t1 = title.get("from", 0), title.get("to", 2.6)
        text = title["text"].replace("\n", r"\N")
        anim = r"{\fad(0,220)\alpha&H00&}"
        lines.append(f"Dialogue: 2,{ass_time(t0)},{ass_time(t1)},Title,,0,0,0,,{{\\pos({x},{ty})}}{anim}{text}")
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---------- EDL ----------

def tc_to_frames(tc, fps):
    h, m, s, f = map(int, re.split(r"[:;]", tc))
    return ((h * 60 + m) * 60 + s) * fps + f


def frames_to_tc(n, fps):
    f = n % fps; s = n // fps
    return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}:{f:02d}"


def write_edl(segs, src, fps, src_tc, path, title):
    base = tc_to_frames(src_tc, fps)
    rec = tc_to_frames("01:00:00:00", fps)
    out = [f"TITLE: {title}", "FCM: NON-DROP FRAME", ""]
    for n, s in enumerate(segs, 1):
        a, b = round(s["in"] * fps), round(s["out"] * fps)
        out.append(f"{n:03d}  AX       AA/V  C        {frames_to_tc(base + a, fps)} {frames_to_tc(base + b, fps)} "
                   f"{frames_to_tc(rec, fps)} {frames_to_tc(rec + b - a, fps)}")
        out.append(f"* FROM CLIP NAME: {Path(src).name}")
        if s["zoom"] != [1.0, 1.0]:
            out.append(f"* ZOOM {s['zoom'][0]:.2f} -> {s['zoom'][1]:.2f}")
        out.append("")
        rec += b - a
    Path(path).write_text("\n".join(out), encoding="utf-8")


# ---------- render ----------

def probe(src):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height,r_frame_rate:stream_tags=timecode",
                        "-of", "json", src], capture_output=True, text=True, check=True)
    st = json.loads(r.stdout)["streams"]
    v = next(s for s in st if s["codec_type"] == "video")
    tc = next((s.get("tags", {}).get("timecode") for s in st if s.get("tags", {}).get("timecode")), "00:00:00:00")
    num, den = map(int, v["r_frame_rate"].split("/"))
    return v["width"], v["height"], round(num / den), tc


def graph(segs, W, H, fx, fy, with_video=True):
    parts, labels = [], []
    for n, s in enumerate(segs):
        d = s["out"] - s["in"]
        a = (f"[0:a]atrim=start={s['in']:.3f}:end={s['out']:.3f},asetpts=PTS-STARTPTS,"
             f"afade=t=in:d={FADE},afade=t=out:st={d - FADE:.3f}:d={FADE}[a{n}]")
        if with_video:
            z0, z1 = s["zoom"]
            z = f"({z0}+({z1}-{z0})*t/{d:.3f})"
            v = (f"[0:v]trim=start={s['in']:.3f}:end={s['out']:.3f},setpts=PTS-STARTPTS,"
                 f"scale=w='trunc({W}*{z}/2)*2':h='trunc({H}*{z}/2)*2':eval=frame:flags=lanczos,"
                 f"crop={W}:{H}:x='clip({fx}*iw-{W / 2},0,iw-{W})':y='clip({fy}*ih-{H / 2},0,ih-{H})',setsar=1[v{n}]")
            parts.append(v)
            labels.append(f"[v{n}][a{n}]")
        else:
            labels.append(f"[a{n}]")
        parts.append(a)
    parts.append("".join(labels) + f"concat=n={len(segs)}:v={1 if with_video else 0}:a=1" +
                 ("[vc][ac]" if with_video else "[ac]"))
    return ";".join(parts)


def place_inserts(E, segs, warn):
    """Inserts: full-screen motion graphics over the speaker's voice, anchored to the SOURCE time of
    the words they cover ("src_at"), so re-snapping a cut keeps them on the same words; an insert
    never runs past its segment into the next shot."""
    placed = []
    for ins in E.get("inserts", []):
        k = next((j for j, s in enumerate(segs) if s["in"] - 0.3 <= ins["src_at"] < s["out"]), None)
        if k is None:
            sys.exit(f"insert at source {ins['src_at']} is outside every segment")
        sg = segs[k]
        src_at = max(ins["src_at"], sg["in"])
        t0 = sg["out_start"] + src_at - sg["in"]
        d = min(ins["dur"], sg["out_start"] + sg["out"] - sg["in"] - t0)
        if d < ins["dur"] - 0.02:
            warn.append(f"insert {Path(ins['src']).name} cut to {d:.2f} s to end with its segment")
        sg.setdefault("inserts", []).append([round(t0, 3), round(t0 + d, 3), ins["src"]])
        placed.append((t0, d, ins["src"]))
    return placed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--edit")
    ap.add_argument("--words", required=True)
    ap.add_argument("--audio", required=True)
    ap.add_argument("--work")
    ap.add_argument("--out")
    ap.add_argument("--draft", action="store_true", help="fast encode for review")
    ap.add_argument("--runs", help="print speech runs with words for a range, e.g. 120-180, and exit")
    a = ap.parse_args()

    words, env = load(a.words)["words"], Env(load(a.audio))
    if a.runs:
        lo, hi = map(float, a.runs.split("-"))
        print(f"speech threshold {env.thr:.1f} dB")
        print_runs(env, words, lo, hi)
        return
    E = load(a.edit)
    work = Path(a.work); work.mkdir(parents=True, exist_ok=True)
    src = E["src"]
    W, H, fps, src_tc = probe(src)
    fx, fy = E.get("focus", [0.5, 0.4])

    # 1. snap
    segs, cw, t_out, warn, n_chunk, shifts = [], [], 0.0, [], 0, []
    cap_cfg = E.get("captions", {})
    fixes = cap_cfg.get("replace", {})
    for s in E["segments"]:
        if s.get("exact"):
            i0, o0 = frame(s["in"], fps, "down"), frame(s["out"], fps, "up")
        else:
            i0 = frame(snap_in(env, s["in"], warn), fps, "down")
            # "hold": seconds of picture kept after the speech (a reaction, the last look at camera)
            o0 = frame(min(s["out"], snap_out(env, s["out"], warn) + s.get("hold", 0)), fps, "up")
        if o0 - i0 < 0.2:
            sys.exit(f"segment {s['in']}-{s['out']} shorter than 0.2 s after snapping")
        for (ra, rb), (rc, rd) in zip(env.runs, env.runs[1:]):
            if i0 < rb and rc < o0 and rc - rb > 0.7:
                warn.append(f"pause {rc - rb:.2f} s inside segment {i0:.2f}-{o0:.2f} at {rb:.2f}: split it or keep it on purpose")
        # Caption text: the approved "text" of the segment (read from the full transcript, which has
        # context and spells better), timed over the speech in the window. The window transcribed on
        # its own is only a signal: it mishears short clips, so a mismatch is a thing to check, not proof.
        heard = retranscribe(src, i0, o0, E.get("language", "pl"))
        if s.get("text"):
            # "|" marks where the model wants a new caption page: phrases by meaning, not by the clock
            chunks = [c.split() for c in s["text"].split("|") if c.strip()]
            spread = time_words(env, " ".join(" ".join(c) for c in chunks), i0, o0)
            ws = aligned_words(src, i0, o0, [w["word"] for w in spread], warn) if E.get("align", True) else None
            if ws:
                shifts += [abs(a["start"] - b["start"]) for a, b in zip(ws, spread)]
            else:
                ws = spread
            ids = [n_chunk + k for k, c in enumerate(chunks) for _ in c]   # no "|": the sentence is one page
            for w, cid in zip(ws, ids):
                w["chunk"] = cid
            n_chunk += len(chunks)
        else:
            ws = heard
            warn.append(f"segment {i0:.2f}-{o0:.2f} has no approved text: captions from the re-transcript")
        if not ws:
            sys.exit(f"no words in {i0:.2f}-{o0:.2f}")
        norm = lambda x: x.lower().strip(".,?!… ")
        want = [norm(w["word"]) for w in ws]
        got = [norm(w["word"]) for w in heard] or [""]
        if want[0][:3] != got[0][:3] or want[-1][:3] != got[-1][:3]:
            warn.append(f"segment {i0:.2f}-{o0:.2f}: heard '{' '.join(got)}', caption '{' '.join(want)}': "
                        "check the first and last word in the strip")
        z = s.get("zoom", 1.0)
        z = [float(z), float(z)] if not isinstance(z, list) else [float(z[0]), float(z[1])]
        segs.append({"in": round(i0, 3), "out": round(o0, 3), "zoom": z, "note": s.get("note", ""),
                     "out_start": round(t_out, 3)})
        for w in ws:
            raw = w["word"]
            bare = raw.strip(".,?!…")
            if cap_cfg.get("case", "lower") == "lower" and not any(c.isdigit() for c in bare):
                bare = bare.lower()
            text = fixes.get(bare, bare) + ("?" if raw.endswith("?") else "")
            cw.append({"text": text, "raw": raw, "seg": len(segs) - 1, "chunk": w.get("chunk"),
                       "start": t_out + max(0, w["start"] - i0),
                       "end": t_out + min(o0, w["end"]) - i0})
        t_out += o0 - i0
    json.dump({"fps": fps, "duration": round(t_out, 3), "segments": segs, "warnings": warn},
              open(work / "cuts.json", "w"), ensure_ascii=False, indent=1)
    for w in warn:
        print("WARNING", w)

    # 2. captions
    cap = dict(E.get("captions", {}), _seg_starts=[s["out_start"] for s in segs], _total=t_out)
    if shifts:
        print(f"word times aligned: mean shift from the syllable spread {1000 * sum(shifts) / len(shifts):.0f} ms, "
              f"max {1000 * max(shifts):.0f} ms over {len(shifts)} words")
    placed = place_inserts(E, segs, warn)
    pages = caption_pages(cw, cap) if cap.get("enabled", True) else []
    faces_path = Path(E.get("faces", work / "faces.json"))
    if pages and cap.get("pill") and faces_path.exists():
        place_captions(pages, segs, load(faces_path), cap, W, H, fx, fy)
        clear = [p["clearance"] for p in pages if p.get("clearance") is not None]
        if clear:
            print(f"captions at y {sorted({p['y'] for p in pages})}, closest to the chin {min(clear)} px")
    elif pages and cap.get("pill"):
        warn.append("no faces.json: captions at a fixed height, run faces.py to keep them off the face")
    json.dump(pages, open(work / "captions.json", "w"), ensure_ascii=False, indent=1)
    write_ass(pages, cap, E.get("title"), W, H, work / "captions.ass")

    # 3. EDL
    write_edl(segs, src, fps, src_tc, work / "edit.edl", E.get("name", "EDIT"))

    # 4. loudness pass 1
    target = E.get("audio", {})
    I, TP = target.get("lufs", -14), target.get("tp", -1.5)
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", src, "-filter_complex",
                        graph(segs, W, H, fx, fy, with_video=False) + f";[ac]loudnorm=I={I}:TP={TP}:LRA=11:print_format=json[x]",
                        "-map", "[x]", "-f", "null", "-"], capture_output=True, text=True)
    m = json.loads(r.stderr[r.stderr.rindex("{"):r.stderr.rindex("}") + 1])

    # 5. render
    ln = (f"loudnorm=I={I}:TP={TP}:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    ass = str(work / "captions.ass").replace(":", r"\:").replace("'", r"\'")
    ins_in, vlab, chain = [], "vc", []
    for n, (t0, d, src_file) in enumerate(placed):
        ins_in += ["-i", src_file]
        chain.append(f"[{n + 1}:v]trim=duration={d:.3f},setpts=PTS-STARTPTS+{t0:.3f}/TB,"
                     f"scale={W}:{H},setsar=1[ins{n}];[{vlab}][ins{n}]overlay=enable='between(t,{t0:.3f},"
                     f"{t0 + d - 0.001:.3f})':eof_action=pass[vi{n}]")
        vlab = f"vi{n}"
    fg = (graph(segs, W, H, fx, fy) + "".join(";" + c for c in chain) + f";[{vlab}]subtitles='{ass}',format=yuv420p,"
          "setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv[vo];"
          f"[ac]{ln},aresample=48000[ao]")
    json.dump({"fps": fps, "duration": round(t_out, 3), "segments": segs, "warnings": warn},
              open(work / "cuts.json", "w"), ensure_ascii=False, indent=1)
    enc = (["-preset", "veryfast", "-crf", "24"] if a.draft else ["-preset", "slow", "-crf", "18", "-profile:v", "high"])
    cmd = ["ffmpeg", "-hide_banner", "-v", "error", "-stats", "-y", "-i", src, *ins_in, "-filter_complex", fg,
           "-map", "[vo]", "-map", "[ao]", "-r", str(fps), "-c:v", "libx264", *enc, "-pix_fmt", "yuv420p",
           "-x264-params", "colorprim=bt709:transfer=bt709:colormatrix=bt709",
           "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", a.out]
    subprocess.run(cmd, check=True)
    print(f"{len(segs)} segments, {t_out:.2f} s, {len(pages)} caption pages -> {a.out}")


if __name__ == "__main__":
    main()
