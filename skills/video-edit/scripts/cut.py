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

import numpy as np
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


JOIN_NEXT = {"nie", "się", "ale", "już", "jak", "czy", "bez", "dla", "tak", "ten", "tą", "tę", "też", "pod", "nad",
             "przy", "aby", "żeby", "bo", "to", "co", "na", "do", "od", "po", "za", "ze", "we", "że", "by", "mi",
             "ci", "go", "mu", "ją", "je", "ma", "są", "jest", "cię", "oni", "one", "ona", "on", "my", "wy",
             "mnie", "nas", "was", "ich", "im", "ciebie", "tobie", "sobie", "się"}


def word_pages(cw, cfg):
    """`style: words` — one word on screen at a time, swapped on the word's aligned start and held
    until the next word (the reference edit's captions). Short words lead into the next content word
    and a page holds at most two words: "w szachy", "żeby Ci | to ułatwić", "Bo to | na początku".
    A comma, a sentence end, a cut or an emphasised word (*słowo*) closes a page."""
    join = set(cfg.get("join_next", JOIN_NEXT))
    short = lambda w: (len(w["text"].strip("?")) <= 2 or w["text"].lower().strip("?") in join
                       or any(c.isdigit() for c in w["text"])) and not w.get("emph")
    closes = lambda w: bool(re.search(r"[.,?!…]$", w["raw"]))
    pages, run = [], []

    def flush(words):
        # the content word keeps one function word in front of it; the rest go in pairs before it
        if len(words) <= 2 or (len(words) == 3 and len(" ".join(w["text"] for w in words)) <= 14):
            pages.append(words)               # "w 2026 roku?", "i jak ich" stay together
            return
        if len(words) == 3:                   # "to jest | sprzedaż", never "to | jest sprzedaż"
            pages.append(words[:2])
            pages.append(words[2:])
            return
        head, tail = words[:-2], words[-2:]
        for i in range(0, len(head), 2):
            pages.append(head[i:i + 2])
        pages.append(tail)

    for w in cw:
        if run and run[-1]["seg"] != w["seg"]:
            flush(run)
            run = []
        run.append(w)
        if not short(w) or closes(w) or w.get("emph"):
            flush(run)
            run = []
    if run:
        flush(run)
    return page_times(pages, dict(cfg, _lead=0.04, _linger=0.7))


def caption_pages(cw, cfg):
    if cfg.get("style") == "words":
        return word_pages(cw, cfg)
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
    lead, linger = cfg.get("_lead", 0.08), cfg.get("_linger", 0.6)
    for n, p in enumerate(pages):
        start = p[0]["start"] - lead          # a page leads its word slightly, but never across a cut
        if seg_start:
            start = max(start, seg_start[p[0]["seg"]])
        nxt = pages[n + 1][0]["start"] - lead if n + 1 < len(pages) else None
        if nxt is not None and seg_start and pages[n + 1][0]["seg"] != p[0]["seg"]:
            nxt = seg_start[pages[n + 1][0]["seg"]] - 0.01   # libass truncates 24.60 s to 24599 ms
        end = p[-1]["end"] + linger if nxt is None else min(nxt, p[-1]["end"] + linger)
        if nxt is None and cfg.get("_total"):
            end = min(end, cfg["_total"] - 0.2)  # the last frame shows the speaker, not a caption
        out.append({"start": round(max(start, out[-1]["end"] if out else 0), 3), "end": round(end, 3),
                    "words": [x["text"] for x in p], "seg": p[0]["seg"],
                    "emph": [bool(x.get("emph")) for x in p],
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
        if cfg.get("style") == "words":       # one line; an emphasised word is ~2x tall
            return 0.55 * size * (cfg.get("emph_scale", 2.0) if any(p.get("emph", [])) else 1.0)
        rows = 2 if len(" ".join(p["words"])) > cfg.get("wrap_chars", 20) and len(p["words"]) > 1 else 1
        return (rows * 0.98 * size + 0.34 * size) / 2

    def bounds(p):                     # (lowest chin, highest face top) while the page is up
        chin, top = None, None
        t = p["start"]
        while t <= p["end"]:
            s = next((s for s in segs if s["out_start"] <= t < s["out_start"] + s["out"] - s["in"]), None)
            if s and not any(a <= t < b for a, b, _ in s.get("inserts", [])):
                d = s["out"] - s["in"]
                z = zoom_at(s, t - s["out_start"])
                f = face_at(s["in"] + t - s["out_start"])
                if f:
                    sfy = focus_at(s, t - s["out_start"], fx, fy)[1]
                    y0 = min(max(sfy * H * z - H / 2, 0), H * z - H)
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
    pill_pop = r"\fscx92\fscy92\t(0,150,0.6,\fscx100\fscy100)"   # no alpha fade: text and pill share frame 1
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
                     f"\\blur9{pill_pop}\\p1}}{path}")
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


FONTS = Path(__file__).resolve().parent.parent / "assets" / "fonts"


def write_words(pages, cfg, W, H, lines):
    """`style: words`: the page's words, centred, Inter SemiBold; an emphasised word in Inter Black at
    ~2x, shrunk if it would pass the safe width; a light soft drop shadow as its own layer under the
    text (blurring the text layer itself would blur the letters); a 60 ms fade in, no other motion."""
    from PIL import ImageFont
    size = cfg.get("size", 80)
    big = size * cfg.get("emph_scale", 2.0)
    fn, fe = cfg.get("font", "Inter SemiBold"), cfg.get("font_emph", "Inter Black")
    f_reg = str(cfg.get("font_file", FONTS / "Inter-SemiBold.ttf"))
    f_emp = str(cfg.get("font_emph_file", FONTS / "Inter-Black.ttf"))
    maxw = cfg.get("max_width", 900)
    sh = cfg.get("shadow", {})
    dx, dy, blur, alpha = sh.get("dx", 0), sh.get("dy", 4), sh.get("blur", 7), sh.get("alpha", "98")
    for p in pages:
        e_size = big
        while True:                          # measured with the same font files libass will use
            reg, emp = ImageFont.truetype(f_reg, size / 1.2), ImageFont.truetype(f_emp, e_size / 1.2)
            width = sum((emp if e else reg).getlength(w) + len(w) * cfg.get("emph_spacing" if e else "spacing", -1)
                        for w, e in zip(p["words"], p["emph"])) + reg.getlength(" ") * (len(p["words"]) - 1)
            if width <= maxw or e_size <= size:
                break
            e_size -= 4
        p["size_px"] = e_size if any(p["emph"]) else size
        esp, rsp = cfg.get("emph_spacing", -8), cfg.get("spacing", -1)
        parts = [(f"{{\\fn{fe}\\fs{e_size:.0f}\\fsp{esp}}}{w}{{\\fn{fn}\\fs{size}\\fsp{rsp}}}" if e else w)
                 for w, e in zip(p["words"], p["emph"])]
        txt = " ".join(parts)
        y = p.get("y", cfg.get("y", int(H * 0.64)))
        t0, t1 = ass_time(p["start"]), ass_time(p["end"])
        lines.append(f"Dialogue: 0,{t0},{t1},W,,0,0,0,,{{\\an5\\pos({W // 2 + dx},{y + dy})\\1c&H000000&"
                     f"\\1a&H{alpha}&\\blur{blur}\\fad(60,0)}}{txt}")
        lines.append(f"Dialogue: 1,{t0},{t1},W,,0,0,0,,{{\\an5\\pos({W // 2},{y})\\fad(60,0)}}{txt}")


# ---------- fx: icons and list lockups drawn in the caption layer ----------

BUILTIN_ICONS = {
    # a stopwatch: ring (outer clockwise, inner counter-clockwise), crown and a hand
    "timer": "M12 4a9 9 0 1 1 0 18a9 9 0 1 1 0-18zM12 6.4a6.6 6.6 0 1 0 0 13.2a6.6 6.6 0 1 0 0-13.2z"
             "M9.6 0.8h4.8v2.2h-4.8zM11.1 8.2h1.8v5.6h-1.8z",
    # a browser window (frame with a cut-out and a title bar), 24-unit box like Simple Icons
    "web": "M3 3h18a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2zM3 8v11h18V8z",
}


def icon_path(name, work):
    """SVG path data of an icon: built-in, or Simple Icons (CC0) fetched once into work/icons/."""
    if name in BUILTIN_ICONS:
        return BUILTIN_ICONS[name]
    f = Path(work) / "icons" / f"{name}.svg"
    if not f.exists():
        import urllib.request
        f.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(f"https://cdn.jsdelivr.net/npm/simple-icons@latest/icons/{name}.svg", f)
    m = re.search(r'\bd="([^"]+)"', f.read_text(encoding="utf-8"))
    if not m:
        sys.exit(f"icon {name}: no path in {f}")
    return m.group(1)


def svg_to_ass(d, size):
    """SVG path (24-unit viewBox) -> ASS drawing at `size` px, in p3 units (1/4 px), arcs as cubics."""
    from svgelements import Path as SPath, Move, Line, CubicBezier, QuadraticBezier, Close
    path = SPath(d)
    path.approximate_arcs_with_cubics()
    k = size / 24 * 4
    q = lambda pt: f"{pt.x * k:.0f} {pt.y * k:.0f}"
    out = []
    for seg in path:
        if isinstance(seg, Move):
            out.append(f"m {q(seg.end)}")
        elif isinstance(seg, (Line, Close)) and seg.end is not None:
            out.append(f"l {q(seg.end)}")
        elif isinstance(seg, CubicBezier):
            out.append(f"b {q(seg.control1)} {q(seg.control2)} {q(seg.end)}")
        elif isinstance(seg, QuadraticBezier):
            c1 = seg.start + (seg.control - seg.start) * (2 / 3)
            c2 = seg.end + (seg.control - seg.end) * (2 / 3)
            out.append(f"b {q(c1)} {q(c2)} {q(seg.end)}")
    return " ".join(out)


def find_word(cw, word, after=0.0, seg=None):
    w0 = word.lower().strip(".,?!…:;*")
    for w in cw:
        if w["start"] + 1e-3 >= after and (seg is None or w["seg"] == seg) and \
                w["text"].lower().strip(".,?!…:;") == w0:
            return w
    sys.exit(f"fx: word '{word}' not found" + (f" in segment {seg}" if seg is not None else "") + f" after {after:.2f} s")


def hand_fx_lines(E, cw, segs, cap, W, H, fx, fy, work):
    """Effects that come out of the speaker's hands (hands.json from hands.py):
      {"type": "hand_icon", "icon": "facebook", "label": "Facebook", "word": "Facebook", "seg": 6, "dur": 1.3}
        the icon pops above the raised fingers (spring scale with a small turn, a burst of lines),
        follows the hand in 0.25 s steps and shrinks away;
      {"type": "burst", "word": "branding", "seg": 1, "at": "index"}
        a short burst of lines at the fingertip, for a point or a beat.
    Positions go through the same zoom and crop as the picture."""
    hp = Path(E.get("hands", work / "hands.json"))
    if not hp.exists():
        sys.exit("fx with hands: run hands.py first (hands.json not found)")
    samples = load(hp)["samples"]
    ts = [x["t"] for x in samples]
    col = ass_color(cap.get("color", "#F2EFE9"))
    sh = cap.get("shadow", {})
    sdx, sdy, sblur, salpha = sh.get("dx", 0), sh.get("dy", 4), sh.get("blur", 7), sh.get("alpha", "98")
    out = []
    seg_end = lambda i: segs[i]["out_start"] + segs[i]["out"] - segs[i]["in"]

    def to_out(sg, t_out, x, y):
        z = zoom_at(sg, t_out - sg["out_start"])
        sfx, sfy = focus_at(sg, t_out - sg["out_start"], fx, fy)
        x0 = min(max(sfx * W * z - W / 2, 0), W * z - W)
        y0 = min(max(sfy * H * z - H / 2, 0), H * z - H)
        return x * z - x0, y * z - y0

    def hand_at(sg, t_out, key="anchor", side=None):
        import bisect
        src_t = sg["in"] + t_out - sg["out_start"]
        k = bisect.bisect_left(ts, src_t)
        best = min((j for j in (k - 1, k) if 0 <= j < len(ts)), key=lambda j: abs(ts[j] - src_t), default=None)
        if best is None or abs(ts[best] - src_t) > 0.2 or not samples[best]["hands"]:
            return None
        hs = [h for h in samples[best]["hands"] if side is None or h["side"] == side]
        if not hs:
            return None
        lively = [h for h in hs if h["gesture"] in ("point", "count")] or hs
        h = min(lively, key=lambda h: h["anchor"][1])            # the raised hand
        x, y = h["tips"]["index"] if key == "index" else h[key]
        return to_out(sg, t_out, x, y)

    def lines_burst(cx, cy, t0, r0, r1, layer=8, n=8):
        bar = pill_path(7, 30, 3.5)
        a, b = ass_time(t0), ass_time(t0 + 0.32)
        for i in range(n):
            ang = i * 2 * math.pi / n + 0.2
            ux, uy = math.sin(ang), -math.cos(ang)
            x0, y0, x1, y1 = cx + ux * r0, cy + uy * r0, cx + ux * r1, cy + uy * r1
            frz = -math.degrees(ang)
            out.append(f"Dialogue: {layer},{a},{b},W,,0,0,0,,{{\\an5\\move({x0:.0f},{y0:.0f},{x1:.0f},{y1:.0f},0,300)"
                       f"\\frz{frz:.0f}\\1c{col}\\bord0\\shad0\\fscy100\\t(0,300,0.7,\\fscy35\\alpha&HFF&)\\p1}}{bar}")

    for f in E.get("fx", []):
        if f["type"] == "hand_stack":
            # words he lists pop one by one beside the hand that gestures, stacking; the earlier ones dim
            ws = [find_word(cw, it["word"], seg=f.get("seg")) for it in f["items"]]
            sg = segs[ws[0]["seg"]]
            t_end = min(ws[-1]["start"] + f.get("hold", 1.0), seg_end(ws[0]["seg"]) - 0.01)
            pos = hand_at(sg, ws[0]["start"], side=f.get("side")) or (W * 0.75, H * 0.45)
            fs = f.get("size", 112)
            lh = fs * 1.02
            right = pos[0] > W / 2                  # stack on the hand's side, aligned to the frame edge
            x = W - 70 if right else 70
            an = 6 if right else 4
            n = len(ws)
            y_top = min(max(pos[1] - lh * n * 0.55, 260), H * 0.62 - lh * n)
            fn = cap.get("font_emph", "Inter Display Black")
            for i, (it, w) in enumerate(zip(f["items"], ws)):
                a = w["start"] - 0.04
                y = y_top + i * lh
                nxt = ws[i + 1]["start"] - a if i + 1 < n else None
                dim = f"\\t({int(nxt * 1000)},{int(nxt * 1000) + 120},\\alpha&H70&)" if nxt else ""
                dur_ms = int((t_end - a) * 1000)
                pop = (r"\fscx40\fscy40\frz-6\alpha&HFF&\t(0,60,\alpha&H00&)"
                       r"\t(0,130,0.6,\fscx112\fscy112\frz2)\t(130,260,1.3,\fscx100\fscy100\frz0)")
                out_ = f"\\t({max(0, dur_ms - 180)},{dur_ms},1.6,\\fscx60\\fscy60\\alpha&HFF&)"
                ta, tb = ass_time(a), ass_time(t_end)
                out.append(f"Dialogue: 6,{ta},{tb},W,,0,0,0,,{{\\an{an}\\pos({x + sdx:.0f},{y + sdy:.0f})\\fn{fn}\\fs{fs}"
                           f"\\fsp-6\\1c&H000000&\\1a&H{salpha}&\\blur{sblur}{pop}{dim}{out_}}}{it.get('text', it['word'])}")
                out.append(f"Dialogue: 7,{ta},{tb},W,,0,0,0,,{{\\an{an}\\pos({x:.0f},{y:.0f})\\fn{fn}\\fs{fs}"
                           f"\\fsp-6{pop}{dim}{out_}}}{it.get('text', it['word'])}")
            continue
        if f["type"] not in ("hand_icon", "burst"):
            continue
        w = find_word(cw, f["word"], seg=f.get("seg"))
        sg = segs[w["seg"]]
        t0 = w["start"] - 0.06
        if f["type"] == "burst":
            pos = hand_at(sg, t0 + 0.04, key="index" if f.get("at", "index") == "index" else "anchor", side=f.get("side"))
            if pos:
                lines_burst(pos[0], pos[1], t0, 28, 92)
            continue
        px = f.get("size", 190)
        t1 = min(t0 + f.get("dur", 1.3), seg_end(w["seg"]) - 0.01)
        later = [find_word(cw, g["word"], seg=g.get("seg"))["start"] - 0.06 for g in E["fx"]
                 if g["type"] == "hand_icon" and g is not f]
        later = [t for t in later if t > t0 + 0.2]
        if later:                              # the next icon takes the hand: this one leaves first
            t1 = min(t1, min(later) - 0.02)
        # the path: the raised hand every 0.25 s (the first step 0.3 s, it carries the pop)
        steps = [t0, min(t0 + 0.3, t1)]
        while steps[-1] + 0.25 < t1:
            steps.append(steps[-1] + 0.25)
        steps.append(t1)
        pts, last = [], None
        for t in steps:
            p = hand_at(sg, t, side=f.get("side")) or last
            last = p
            pts.append(p)
        if pts[0] is None:
            pts = [q for q in pts if q] or [(W * 0.7, H * 0.4)]
            pts = [pts[0]] * len(steps)
        lab = f.get("label")
        lab_size = f.get("label_size", 64)
        def clamp_xy(p):
            return (min(max(p[0], px / 2 + 40), W - px / 2 - 40), max(p[1] - px * 0.55, 240 + px / 2))
        pts = [clamp_xy(p if p else pts[0]) for p in pts]
        dr = svg_to_ass(icon_path(f["icon"], work), px)
        for i in range(len(steps) - 1):
            a, b = steps[i], steps[i + 1]
            (xa, ya), (xb, yb) = pts[i], pts[i + 1]
            dur_ms = int((b - a) * 1000)
            anim = ""
            if i == 0:
                anim = (r"\fscx35\fscy35\frz-14\alpha&HFF&\t(0,60,\alpha&H00&)"
                        r"\t(0,140,0.6,\fscx116\fscy116\frz5)\t(140,280,1.3,\fscx100\fscy100\frz0)")
            if i == len(steps) - 2:
                anim += f"\\t({max(0, dur_ms - 160)},{dur_ms},1.6,\\fscx55\\fscy55\\alpha&HFF&)"
            mv = f"\\move({xa:.0f},{ya:.0f},{xb:.0f},{yb:.0f})"
            mvs = f"\\move({xa + sdx:.0f},{ya + sdy:.0f},{xb + sdx:.0f},{yb + sdy:.0f})"
            ta, tb = ass_time(a), ass_time(b)
            out.append(f"Dialogue: 6,{ta},{tb},W,,0,0,0,,{{\\an5{mvs}\\1c&H000000&\\1a&H{salpha}&\\blur{sblur}\\bord0\\shad0{anim}\\p3}}{dr}")
            out.append(f"Dialogue: 7,{ta},{tb},W,,0,0,0,,{{\\an5{mv}\\1c{col}\\bord0\\shad0{anim}\\p3}}{dr}")
            if lab:
                ly = px * 0.5 + lab_size * 0.75
                lmv = f"\\move({xa:.0f},{ya + ly:.0f},{xb:.0f},{yb + ly:.0f})"
                lmvs = f"\\move({xa + sdx:.0f},{ya + ly + sdy:.0f},{xb + sdx:.0f},{yb + ly + sdy:.0f})"
                lanim = anim.replace(r"\frz-14", "").replace(r"\frz5", "").replace(r"\frz0", "")
                fn = cap.get("font_emph", "Inter Black")
                out.append(f"Dialogue: 6,{ta},{tb},W,,0,0,0,,{{\\an5{lmvs}\\fn{fn}\\fs{lab_size}\\1c&H000000&\\1a&H{salpha}&\\blur{sblur}{lanim}}}{lab}")
                out.append(f"Dialogue: 7,{ta},{tb},W,,0,0,0,,{{\\an5{lmv}\\fn{fn}\\fs{lab_size}{lanim}}}{lab}")
        lines_burst(pts[0][0], pts[0][1], t0 + 0.06, px * 0.55, px * 0.95)
    return out


def fx_lines(E, cw, segs, pages, cap, W, H, work):
    """ASS events for edit.json "fx", and the caption pages they replace.
      {"type": "icon", "icon": "facebook", "word": "Facebooku", "seg": 15, "size": 110, "dur": 1.2}
      {"type": "list", "header": "Przygotowujemy:", "seg": 6,
       "items": [{"word": "Google", "text": "Google Maps", "icon": "googlemaps"}, ...], "until_seg": 7}
    Icons are white glyphs with the captions' soft shadow, popping in (scale 80->100 %, 140 ms)."""
    col = ass_color(cap.get("color", "#F2EFE9"))
    sh = cap.get("shadow", {})
    dx, dy, blur, alpha = sh.get("dx", 0), sh.get("dy", 4), sh.get("blur", 7), sh.get("alpha", "98")
    size = cap.get("size", 80)
    out, hide = [], []
    seg_end = lambda i: segs[i]["out_start"] + segs[i]["out"] - segs[i]["in"]

    def glyph(name, px, x, y, t0, t1, layer=4):
        dr = svg_to_ass(icon_path(name, work), px)
        pop = r"\fscx80\fscy80\t(0,140,0.5,\fscx100\fscy100)\fad(70,90)"
        a, b = ass_time(t0), ass_time(t1)
        out.append(f"Dialogue: {layer},{a},{b},W,,0,0,0,,{{\\an5\\pos({x + dx:.0f},{y + dy:.0f})\\1c&H000000&"
                   f"\\1a&H{alpha}&\\blur{blur}\\bord0\\shad0{pop}\\p3}}{dr}")
        out.append(f"Dialogue: {layer + 1},{a},{b},W,,0,0,0,,{{\\an5\\pos({x:.0f},{y:.0f})\\1c{col}\\bord0\\shad0{pop}\\p3}}{dr}")

    def text(t, fs, font, x, y, t0, t1, layer=4, extra=""):
        a, b = ass_time(t0), ass_time(t1)
        out.append(f"Dialogue: {layer},{a},{b},W,,0,0,0,,{{\\an5\\pos({x + dx:.0f},{y + dy:.0f})\\fn{font}\\fs{fs}"
                   f"\\1c&H000000&\\1a&H{alpha}&\\blur{blur}{extra}}}{t}")
        out.append(f"Dialogue: {layer + 1},{a},{b},W,,0,0,0,,{{\\an5\\pos({x:.0f},{y:.0f})\\fn{font}\\fs{fs}{extra}}}{t}")

    for f in E.get("fx", []):
        if f["type"] == "icon":
            w = find_word(cw, f["word"], seg=f.get("seg"))
            page = next((p for p in pages if p["start"] - 0.05 <= w["start"] <= p["end"]), None)
            y_cap = page.get("y", cap.get("y", 1250)) if page else cap.get("y", 1250)
            px = f.get("size", int(size * 1.4))
            big = page and any(page.get("emph", []))
            y = f.get("y", y_cap - (size * (cap.get("emph_scale", 2.0) if big else 1.0)) * 0.6 - px * 0.5 - 24)
            t1 = min(w["start"] + f.get("dur", 1.2), seg_end(w["seg"]) - 0.01)
            glyph(f["icon"], px, f.get("x", W / 2), y, w["start"] - 0.04, t1)
        elif f["type"] == "list":
            first = find_word(cw, f.get("from_word", "") or next(x["text"] for x in cw if x["seg"] == f["seg"]), seg=f["seg"])
            t_start = first["start"] - 0.04
            t_end = seg_end(f.get("until_seg", f["seg"])) - 0.01
            y0 = next((p.get("y") for p in pages if p["seg"] == f["seg"] and p.get("y")), cap.get("y", 1250))
            hs = f.get("header_size", int(size * 1.15))
            text(f["header"].upper(), hs, cap.get("font_emph", "Inter Black"), W / 2, y0 - hs * 0.55, t_start, t_end)
            items = f["items"]
            times = []
            after = t_start
            for it in items:
                w = find_word(cw, it["word"], after=after, seg=it.get("seg", f["seg"]))
                times.append(w["start"] - 0.04)
                after = w["start"]
            for i, it in enumerate(items):
                a, b = times[i], (times[i + 1] if i + 1 < len(items) else t_end)
                isz = it.get("size", int(size * 0.9))
                label = it["text"]
                if it.get("icon"):
                    from PIL import ImageFont
                    fnt = ImageFont.truetype(str(cap.get("font_file", FONTS / "Inter-SemiBold.ttf")), isz / 1.2)
                    tw, ip = fnt.getlength(label), isz * 1.05
                    left = W / 2 - (tw + ip + 22) / 2
                    glyph(it["icon"], ip, left + ip / 2, y0 + isz * 0.62, a, b)
                    text(label, isz, cap.get("font", "Inter SemiBold"), left + ip + 22 + tw / 2, y0 + isz * 0.62, a, b,
                         extra=r"\fad(60,0)")
                else:
                    text(label, isz, cap.get("font", "Inter SemiBold"), W / 2, y0 + isz * 0.62, a, b, extra=r"\fad(60,0)")
            hide.append((t_start, t_end))
    return out, hide


def hook_lines(E, cap, W, H):
    """`hook`: a short line at the top that tells the viewer what they get if they stay ("Marketing
    lokalnej firmy / plan na 2026 w minutę"). Not the big title that was rejected: at most two lines
    and ~6 words, 64-72 px, words popping in one after another, gone by ~4 s (slides up and fades)."""
    hk = E["hook"]
    lines_txt = hk["text"].split("\n")[:2]
    fs = hk.get("size", 70)
    fn = hk.get("font", cap.get("font_emph", "Inter Display Black"))
    t0, t1 = hk.get("from", 0.0), hk.get("to", 4.0)
    y0 = hk.get("y", 300)
    sh = cap.get("shadow", {})
    sdy, sblur, salpha = sh.get("dy", 4), sh.get("blur", 7), sh.get("alpha", "98")
    out, k = [], 0
    dur_ms = int((t1 - t0) * 1000)
    # a soft dark band behind it: the top of a phone video is often a bright window or sky
    band_h = y0 + len(lines_txt) * fs * 1.08 + 90
    band = f"m 0 -80 l {W} -80 l {W} {band_h:.0f} l 0 {band_h:.0f}"
    out.append(f"Dialogue: 7,{ass_time(t0)},{ass_time(t1)},W,,0,0,0,,{{\\an7\\pos(0,0)\\1c&H000000&\\1a&H{hk.get('band_alpha', '88')}&"
               f"\\bord0\\shad0\\blur70\\fad(200,300)\\p1}}{band}")
    for li, line in enumerate(lines_txt):
        y = y0 + li * fs * 1.08
        words = line.split()
        anim_parts = []
        for w in words:
            d = 90 * k + 80
            anim_parts.append(f"{{\\alpha&HFF&\\t({d},{d + 90},\\alpha&H00&)}}{w}")
            k += 1
        txt = " ".join(anim_parts)
        leave = f"\\t({dur_ms - 260},{dur_ms},1.5,\\fscx92\\fscy92\\alpha&HFF&)"
        mv = f"\\move({W // 2},{y:.0f},{W // 2},{y - 36:.0f},{dur_ms - 260},{dur_ms})"
        mvs = f"\\move({W // 2},{y + sdy:.0f},{W // 2},{y - 36 + sdy:.0f},{dur_ms - 260},{dur_ms})"
        a, b = ass_time(t0), ass_time(t1)
        out.append(f"Dialogue: 8,{a},{b},W,,0,0,0,,{{\\an5{mvs}\\fn{fn}\\fs{fs}\\fsp-4\\1c&H000000&\\1a&H{salpha}&"
                   f"\\blur{sblur}{leave}}}" + txt.replace("\\alpha&H00&", f"\\alpha&H{salpha}&"))
        out.append(f"Dialogue: 9,{a},{b},W,,0,0,0,,{{\\an5{mv}\\fn{fn}\\fs{fs}\\fsp-4{leave}}}{txt}")
    return out


def write_ass(pages, cfg, title, W, H, path):
    font, size = cfg.get("font", "Fira Sans"), cfg.get("size", 78)
    col, acc = ass_color(cfg.get("color", "#FFFFFF")), ass_color(cfg.get("accent", "#F5B942"))
    accent = set(cfg.get("accent_words", []))
    y = cfg.get("y", int(H * 0.64))
    if cfg.get("style") == "words":
        col = ass_color(cfg.get("color", "#F2EFE9"))
        lines = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}", "WrapStyle: 2",
                 "ScaledBorderAndShadow: yes", "", "[V4+ Styles]",
                 "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, "
                 "Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
                 "Alignment, MarginL, MarginR, MarginV, Encoding",
                 f"Style: W,{cfg.get('font', 'Inter SemiBold')},{cfg.get('size', 80)},{col},{col},&H00000000,"
                 f"&H00000000,0,0,0,0,100,100,{cfg.get('spacing', -1)},0,1,0,0,5,0,0,0,1",
                 "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
        write_words(pages, cfg, W, H, lines)
        Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
        return
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


def shots_of(s):
    """A segment's framing as shots: [t_rel_start, z_start, z_end, (fx, fy)]. Without angle changes it is
    one shot, the segment's own zoom ramp. fx/fy (crop centre as fractions) come from the face track
    when `framing: face` is on; otherwise the global focus applies."""
    return s.get("shots") or [[0.0, s["zoom"][0], s["zoom"][1]]]


def _shot_k(s, t_rel):
    sh = shots_of(s)
    return max(i for i, x in enumerate(sh) if x[0] <= t_rel + 1e-6)


def zoom_at(s, t_rel):
    sh = shots_of(s)
    d = s["out"] - s["in"]
    k = _shot_k(s, t_rel)
    a, z0, z1 = sh[k][:3]
    b = sh[k + 1][0] if k + 1 < len(sh) else d
    return z0 + (z1 - z0) * (t_rel - a) / max(b - a, 1e-3)


def focus_at(s, t_rel, fx, fy):
    x = shots_of(s)[_shot_k(s, t_rel)]
    return (x[3], x[4]) if len(x) >= 5 else (fx, fy)


def zoom_expr(s, T="t"):
    """ffmpeg expression of the zoom over the segment's own time T: nested if() over the shots."""
    sh = shots_of(s)
    d = s["out"] - s["in"]
    expr = None
    for k in range(len(sh) - 1, -1, -1):
        a, z0, z1 = sh[k][:3]
        b = sh[k + 1][0] if k + 1 < len(sh) else d
        piece = f"({z0}+({z1}-{z0})*({T}-{a:.3f})/{max(b - a, 1e-3):.3f})"
        expr = piece if expr is None else f"if(lt({T},{b:.3f}),{piece},{expr})"   # commas are safe inside the quoted option
    return expr


def focus_expr(s, i, default, T="t"):
    """The crop centre (i=3: x, i=4: y) per shot, as a nested if() over the segment's time."""
    sh = shots_of(s)
    expr = None
    for k in range(len(sh) - 1, -1, -1):
        v = sh[k][i] if len(sh[k]) >= 5 else default
        expr = f"{v:.4f}" if expr is None else f"if(lt({T},{sh[k + 1][0]:.3f}),{v:.4f},{expr})"
    return expr


def frame_on_face(segs, faces, W, H, cfg):
    """Every shot framed on the face, the way an operator frames: the face centred across, its centre on
    `face_y` of the frame height (0.40: eyes near the upper third), from the median face position over the
    shot. A crop centred on the frame instead pushed toward the window behind him in review."""
    track = faces["faces"]
    fy_target = cfg.get("face_y", 0.40)
    for s in segs:
        sh = [list(x) for x in shots_of(s)]
        d = s["out"] - s["in"]
        for k, x in enumerate(sh):
            a = x[0]
            b = sh[k + 1][0] if k + 1 < len(sh) else d
            fs = [f for f in track if s["in"] + a - 0.1 <= f["t"] <= s["in"] + b + 0.1]
            if not fs:
                continue
            cx = float(np.median([f["x"] + f["w"] / 2 for f in fs]))
            cy = float(np.median([f["y"] + f["h"] / 2 for f in fs]))
            z = (x[1] + x[2]) / 2
            fxv = cx / W
            fyv = (cy * z - fy_target * H + H / 2) / (H * z)
            sh[k] = x[:3] + [round(fxv, 4), round(fyv, 4)]
        s["shots"] = sh


def punch_in(segs, cw, E):
    """`ending`/`punches`: a cut-in to a close-up on a word (the last word, a payoff), the way an editor
    lands a line; the ending also holds a beat on his face before the film ends."""
    items = list(E.get("punches", []))
    if E.get("ending"):
        items.append(dict(E["ending"], seg=E["ending"].get("seg", len(segs) - 1)))
    for p in items:
        w = find_word(cw, p["word"], seg=p.get("seg"))
        s = segs[w["seg"]]
        t = round(w["start"] - 0.04 - s["out_start"], 3)
        sh = [list(x) for x in shots_of(s)]
        sh = [x for x in sh if x[0] < t - 0.3] or [sh[0]]
        z = p.get("zoom", 1.3)
        if sh[-1][1] >= z - 0.12:              # the shot before has to be wider, or the cut-in doesn't read
            z0, z1 = s["zoom"]
            sh[-1] = [sh[-1][0], z0, z0 + (z1 - z0) * 0.5]
        sh.append([t, z, z + p.get("push", 0.03)])
        s["shots"] = sh


def fx_windows(E, cw):
    """(seg, t0, t1) in output time for the effects that sit on the hands."""
    out = []
    for f in E.get("fx", []):
        if f["type"] in ("hand_icon", "burst"):
            w = find_word(cw, f["word"], seg=f.get("seg"))
            out.append((w["seg"], w["start"] - 0.3, w["start"] + f.get("dur", 1.3 if f["type"] == "hand_icon" else 0.4)))
    return out


def plan_angles(segs, cw, cfg, keep_wide=()):
    """Multicam feel from one camera: inside a long segment, switch framing at a phrase start so no shot
    runs much past `max_shot`, alternating the segment's own framing with a close-up. The audio isn't
    cut; only the picture changes, the way a cut to another camera does."""
    max_shot, min_shot = cfg.get("max_shot", 2.6), cfg.get("min_shot", 1.1)
    close = cfg.get("close", 1.25)
    for si, s in enumerate(segs):
        d = s["out"] - s["in"]
        if d <= max_shot or s.get("shots"):
            continue
        # candidate switch points: starts of phrase chunks ("|") and sentence starts, in segment time
        starts, prev = [], None
        for w in cw:
            if w["seg"] != si:
                continue
            t = w["start"] - s["out_start"]
            if prev is None:
                prev = w
                continue
            if w.get("chunk") != prev.get("chunk") or re.search(r"[.,?!…]$", prev["raw"]):
                starts.append(max(0.0, t - 0.04))
            prev = w
        cuts, last = [], 0.0
        for t in starts:
            if t - last >= min_shot and d - t >= min_shot and (t - last >= max_shot * 0.75 or not cuts and t > max_shot * 0.6):
                cuts.append(t)
                last = t
        if not cuts:
            continue
        z0, z1 = s["zoom"]
        base = (z0 + z1) / 2
        wide_first = base < close - 0.05
        shots, bounds = [], [0.0] + cuts + [d]
        for k in range(len(bounds) - 1):
            a, b = bounds[k], bounds[k + 1]
            if k == 0:
                za, zb = z0, z0 + (z1 - z0) * b / d
            elif (k % 2 == 1) == wide_first:
                za, zb = close, close + 0.02          # the close-up, with a slow push
            else:
                za, zb = z0 + (z1 - z0) * a / d, z0 + (z1 - z0) * b / d
            shots.append([round(a, 3), round(za, 3), round(zb, 3)])
        for sh_i, (a, za, zb) in enumerate(shots):   # a close-up over a hand effect would crop the hand away
            b = shots[sh_i + 1][0] if sh_i + 1 < len(shots) else d
            if za >= close - 1e-6 and any(k == si and s["out_start"] + a < w1 and w0 < s["out_start"] + b
                                          for k, w0, w1 in keep_wide):
                shots[sh_i] = [a, z0 + (z1 - z0) * a / d, z0 + (z1 - z0) * b / d]
        s["shots"] = shots


def graph(segs, W, H, fx, fy, with_video=True, lut=None):
    parts, labels = [], []
    look = f"lut3d=file='{lut}':interp=tetrahedral," if lut else ""   # the footage only, before framing
    for n, s in enumerate(segs):
        d = s["out"] - s["in"]
        a = (f"[0:a]atrim=start={s['in']:.3f}:end={s['out']:.3f},asetpts=PTS-STARTPTS,"
             f"afade=t=in:d={FADE},afade=t=out:st={d - FADE:.3f}:d={FADE}[a{n}]")
        if with_video:
            # Zoom and framing with `perspective`: it takes a source rectangle per frame and fills the
            # constant output frame. scale(eval=frame)+crop does not work: crop keeps the input size of
            # its first frame and clamps every later crop to the top-left (the "zoom into the window").
            fps = s.get("_fps", 25)
            T = f"(in/{fps})"
            Z = zoom_expr(s, T)
            if all(abs(x[1] - 1) < 1e-6 and abs(x[2] - 1) < 1e-6 for x in shots_of(s)):
                frame = ""
            else:
                FX, FY = focus_expr(s, 3, fx, T), focus_expr(s, 4, fy, T)
                L = f"clip({FX}*W-W/(2*{Z}),0,W-W/{Z})"
                TOP = f"clip({FY}*H-H/(2*{Z}),0,H-H/{Z})"
                R, B = f"({L}+W/{Z})", f"({TOP}+H/{Z})"
                frame = (f"perspective=x0='{L}':y0='{TOP}':x1='{R}':y1='{TOP}':x2='{L}':y2='{B}':x3='{R}':y3='{B}'"
                         f":interpolation=cubic:eval=frame,")
            v = (f"[0:v]trim=start={s['in']:.3f}:end={s['out']:.3f},setpts=PTS-STARTPTS,{look}{frame}setsar=1[v{n}]")
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
        fps = E.get("_fps", 25)
        t0 = round((sg["out_start"] + src_at - sg["in"]) * fps) / fps     # on the frame grid, or the frame
        end = min(t0 + ins["dur"], sg["out_start"] + sg["out"] - sg["in"])  # before the cut shows the face
        d = round((end - t0) * fps) / fps
        if ins.get("skip"):                    # skipping the head leaves less clip: say so in cuts.json
            r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                ins["src"]], capture_output=True, text=True)
            d = min(d, math.floor((float(r.stdout) - ins["skip"]) * fps) / fps)
        if d < ins["dur"] - 0.02:
            warn.append(f"insert {Path(ins['src']).name} cut to {d:.2f} s to end with its segment")
        sg.setdefault("inserts", []).append([round(t0, 3), round(t0 + d, 3), ins["src"]])
        placed.append((t0, d, ins["src"], ins.get("skip", 0.0)))
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
    E["_fps"] = fps
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
        norm = lambda x: x.lower().replace("*", "").strip(".,?!… ")
        want = [norm(w["word"]) for w in ws]
        got = [norm(w["word"]) for w in heard] or [""]
        if want[0][:3] != got[0][:3] or want[-1][:3] != got[-1][:3]:
            warn.append(f"segment {i0:.2f}-{o0:.2f}: heard '{' '.join(got)}', caption '{' '.join(want)}': "
                        "check the first and last word in the strip")
        z = s.get("zoom", 1.0)
        z = [float(z), float(z)] if not isinstance(z, list) else [float(z[0]), float(z[1])]
        segs.append({"in": round(i0, 3), "out": round(o0, 3), "zoom": z, "note": s.get("note", ""), "_fps": fps,
                     "out_start": round(t_out, 3)})
        for w in ws:
            raw = w["word"]
            emph = "*" in raw                        # *słowo*: the model's emphasis mark
            raw = raw.replace("*", "")
            bare = raw.strip(".,?!…:;")
            if cap_cfg.get("case", "lower") == "lower" and not any(c.isdigit() for c in bare):
                bare = bare.lower()
            text = fixes.get(bare, bare) + ("?" if raw.endswith("?") else "")
            cw.append({"text": text, "raw": raw, "seg": len(segs) - 1, "chunk": w.get("chunk"), "emph": emph,
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
    if E.get("angles"):
        plan_angles(segs, cw, E["angles"] if isinstance(E["angles"], dict) else {}, fx_windows(E, cw))
        n_sw = sum(len(s.get("shots", [])) - 1 for s in segs if s.get("shots"))
        print(f"angle changes inside segments: {n_sw}")
    if E.get("ending") or E.get("punches"):
        punch_in(segs, cw, E)
    if E.get("framing", {}).get("mode") == "face":
        fp = Path(E.get("faces", work / "faces.json"))
        if fp.exists():
            frame_on_face(segs, load(fp), W, H, E["framing"])
        else:
            warn.append("framing: face needs faces.json (run faces.py), framed on the focus point instead")
    placed = place_inserts(E, segs, warn)
    pages = caption_pages(cw, cap) if cap.get("enabled", True) else []
    faces_path = Path(E.get("faces", work / "faces.json"))
    styled = cap.get("pill") or cap.get("style") == "words"
    if pages and styled and faces_path.exists():
        place_captions(pages, segs, load(faces_path), cap, W, H, fx, fy)
        clear = [p["clearance"] for p in pages if p.get("clearance") is not None]
        if clear:
            print(f"captions at y {sorted({p['y'] for p in pages})}, closest to the chin {min(clear)} px")
    elif pages and styled:
        warn.append("no faces.json: captions at a fixed height, run faces.py to keep them off the face")
    extra, hide = fx_lines(E, cw, segs, pages, cap, W, H, work) if E.get("fx") else ([], [])
    if any(f["type"] in ("hand_icon", "burst", "hand_stack") for f in E.get("fx", [])):
        extra += hand_fx_lines(E, cw, segs, cap, W, H, fx, fy, work)
        for f in E["fx"]:
            if f["type"] == "hand_stack":       # the stacked words replace their caption pages
                said = {find_word(cw, it["word"], seg=f.get("seg"))["start"] for it in f["items"]}
                kept = []
                for p in pages:                 # drop the stacked word, keep the rest of its page
                    keep = [i for i, t in enumerate(p["times"]) if not any(abs(t[0] - x) < 0.02 for x in said)]
                    if keep:
                        kept.append(dict(p, words=[p["words"][i] for i in keep], times=[p["times"][i] for i in keep],
                                         emph=[p["emph"][i] for i in keep]))
                pages = kept
    if E.get("hook"):
        extra += hook_lines(E, cap, W, H)
    if hide:                                   # a list lockup replaces the word captions while it is up
        pages = [p for p in pages if not any(a - 0.02 <= p["start"] < b for a, b in hide)]
    json.dump(pages, open(work / "captions.json", "w"), ensure_ascii=False, indent=1)
    write_ass(pages, cap, E.get("title"), W, H, work / "captions.ass")
    if extra:
        with open(work / "captions.ass", "a", encoding="utf-8") as fh:
            fh.write("\n".join(extra) + "\n")

    # 3. EDL
    write_edl(segs, src, fps, src_tc, work / "edit.edl", E.get("name", "EDIT"))

    # 4. transitions, sound effects, music: where they fall in the film
    FXH = Path.home() / ".cache/video-edit"
    trans_t = []
    for tr in E.get("transitions", []):
        if "cut" in tr:
            t = segs[tr["cut"]]["out_start"]
        else:
            t0i, di = placed[tr["insert"]][:2]
            t = t0i if tr.get("edge", "in") == "in" else t0i + di
        trans_t.append(round(t * fps) / fps)
    burn = FXH / "fx" / f"burn_{W}x{H}_{fps}.mp4"
    sfx_dir = Path(E.get("audio", {}).get("sfx_dir", FXH / "sfx"))
    if trans_t and not burn.exists():
        subprocess.run([sys.executable, str(Path(__file__).parent / "fxassets.py"), "--size", f"{W}x{H}",
                        "--fps", str(fps)], check=True, capture_output=True)
    aud = E.get("audio", {})
    missing = set()

    def sound(name):
        """A recorded sound from the library by name (shutter.wav, whoosh.mp3...) or a path; None if absent."""
        if "/" in name:
            return Path(name) if Path(name).exists() else missing.add(name)
        hits = [p for p in sorted(sfx_dir.glob(f"{name}.*")) if p.suffix.lower() in (".wav", ".flac", ".mp3", ".ogg", ".aif", ".aiff")]
        return hits[0] if hits else missing.add(name)

    sfx = []                                  # (file, time the sound starts, gain dB)
    for t in trans_t:                         # the whoosh peaks (whoosh_peak s in) on the cut, the shutter clicks on it
        if aud.get("transition_sfx", True):
            sfx.append((sound("whoosh"), t - aud.get("whoosh_peak", 0.30), aud.get("whoosh_db", -4)))
            sfx.append((sound("shutter"), t - 0.004, aud.get("shutter_db", -3)))
    if aud.get("icon_pop", True):
        for f in E.get("fx", []):
            if f["type"] in ("hand_icon", "icon"):
                w = find_word(cw, f["word"], seg=f.get("seg"))
                sfx.append((sound("pop"), w["start"] - 0.02, aud.get("pop_db", -6)))
    for e_ in aud.get("sfx", []):             # explicit: {"file": "whoosh"|path, "word"/"cut"/"at", "gain"}
        if "word" in e_:
            t = find_word(cw, e_["word"], seg=e_.get("seg"))["start"]
        elif "cut" in e_:
            t = segs[e_["cut"]]["out_start"]
        else:
            t = e_["at"]
        sfx.append((sound(e_["file"]), t + e_.get("offset", 0.0), e_.get("gain", -6)))
    sfx = [s for s in sfx if s[0]]            # no recorded file, no sound: never a synthesised stand-in
    for name in sorted(missing):
        warn.append(f"no sound '{name}' in {sfx_dir}: those moments are silent (add a recorded file, see SKILL.md)")
    music = aud.get("music")

    def audio_graph(first_input):
        """Voice [ac] + music ducked under it + sound effects -> [mix]. Inputs start at first_input."""
        ins, parts, labels, k = [], [], ["[vox]"], first_input
        parts.append("[ac]aformat=sample_rates=48000:channel_layouts=stereo,asplit=2[vox][vsc]")
        if music:
            ins += ["-stream_loop", "-1", "-ss", str(music.get("offset", 0)), "-i", music["file"]]
            fo = music.get("fade_out", 1.0)
            parts.append(f"[{k}:a]aformat=sample_rates=48000:channel_layouts=stereo,atrim=duration={t_out:.3f},"
                         f"asetpts=PTS-STARTPTS,afade=t=in:d={music.get('fade_in', 0.5)},"
                         f"afade=t=out:st={t_out - fo:.3f}:d={fo},"
                         f"loudnorm=I={music.get('bed_lufs', -22)}:TP=-3:LRA=11,"     # every track sits at the same level
                         f"aresample=48000,volume={music.get('gain', 0)}dB[mus]")
            parts.append("[mus][vsc]sidechaincompress=threshold=0.03:ratio=12:attack=15:release=350[mduck]")
            labels.append("[mduck]")
            k += 1
        else:
            parts.append("[vsc]anullsink")
        for j, (f_, t, g) in enumerate(sfx):
            ins += ["-i", str(f_)]
            ms = max(0, int(round(t * 1000)))
            parts.append(f"[{k}:a]aformat=sample_rates=48000:channel_layouts=stereo,adelay={ms}|{ms},volume={g}dB[s{j}]")
            labels.append(f"[s{j}]")
            k += 1
        parts.append("".join(labels) + f"amix=inputs={len(labels)}:normalize=0:duration=first[mix]")
        return ins, ";".join(parts)

    # 5. loudness pass 1, on the whole mix
    target = E.get("audio", {})
    I, TP = target.get("lufs", -14), target.get("tp", -1.5) - 0.5   # AAC overshoots the limiter
    a_ins, a_fg = audio_graph(1)
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", src, *a_ins, "-filter_complex",
                        graph(segs, W, H, fx, fy, with_video=False) + ";" + a_fg +
                        f";[mix]loudnorm=I={I}:TP={TP}:LRA=11:print_format=json[x]",
                        "-map", "[x]", "-f", "null", "-"], capture_output=True, text=True)
    m = json.loads(r.stderr[r.stderr.rindex("{"):r.stderr.rindex("}") + 1])

    # 6. render
    ln = (f"loudnorm=I={I}:TP={TP}:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    ass = str(work / "captions.ass").replace(":", r"\:").replace("'", r"\'")
    ins_in, vlab, chain = [], "vc", []
    for n, (t0, d, src_file, skip) in enumerate(placed):
        ins_in += ["-i", src_file]
        chain.append(f"[{n + 1}:v]trim=start={skip:.3f}:duration={d:.3f},setpts=PTS-STARTPTS+{t0:.3f}/TB,"
                     f"scale={W}:{H},setsar=1[ins{n}];[{vlab}][ins{n}]overlay=enable='between(t,{t0:.3f},"
                     f"{t0 + d - 0.001:.3f})':eof_action=pass[vi{n}]")
        vlab = f"vi{n}"
    if trans_t:                               # film burn + shutter: a black track with the burns, screen-blended
        base = 1 + len(placed)
        chain.append(f"color=c=black:s={W}x{H}:r={fps}:d={t_out:.3f}[fxb0]")
        for j, t in enumerate(trans_t):
            ins_in += ["-i", str(burn)]
            chain.append(f"[{base + j}:v]setpts=PTS-STARTPTS+{max(0, t - 8 / fps):.3f}/TB[bn{j}];"
                         f"[fxb{j}][bn{j}]overlay=eof_action=pass:repeatlast=0[fxb{j + 1}]")
        chain.append(f"[{vlab}]format=gbrp[vmg];[fxb{len(trans_t)}]format=gbrp[vfg];"
                     f"[vmg][vfg]blend=all_mode=screen,format=yuv420p[vtr]")
        vlab = "vtr"
    a_ins, a_fg = audio_graph(1 + len(ins_in) // 2)
    # grading is opt-in: applied only with "enabled": true, never because a LUT is listed
    lut = E.get("grade", {}).get("lut") if E.get("grade", {}).get("enabled") is True else None
    fg = (graph(segs, W, H, fx, fy, lut=lut) + "".join(";" + c for c in chain) + ";" + a_fg +
          f";[{vlab}]subtitles='{ass}':fontsdir='{cap.get('fontsdir', FONTS)}',format=yuv420p,"
          "setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv[vo];"
          f"[mix]{ln},aresample=48000[ao]")
    ins_in += a_ins
    firsts = [t0 for t0, *_ in placed] + trans_t
    if E.get("hook"):                         # its first word pops in 80 ms after it starts
        firsts.append(E["hook"].get("from", 0.0) + 0.08)
    for f in E.get("fx", []):
        if "word" in f:
            firsts.append(find_word(cw, f["word"], seg=f.get("seg"))["start"])
        elif f.get("items"):
            firsts.append(find_word(cw, f["items"][0]["word"], seg=f.get("seg"))["start"])
        elif f.get("seg") is not None and f["type"] == "list":
            firsts.append(segs[f["seg"]]["out_start"])
    firsts += [pg["start"] for pg in pages if any(pg.get("emph", []))]
    first_motion = round(min(firsts), 2) if firsts else None
    json.dump({"fps": fps, "duration": round(t_out, 3), "segments": segs, "warnings": warn,
               "first_motion": first_motion, "transitions": trans_t,
               "sfx": [[str(f_), round(t, 3), g] for f_, t, g in sfx], "music": music},
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
