#!/usr/bin/env python3
"""Word times by forced alignment: the approved text against the audio of one window.

Whisper's word times are early (~150 ms) and drift after pauses; a per-word caption highlight needs
the times the words are actually said. This runs a Polish wav2vec2 CTC model
(jonatasgrosman/wav2vec2-large-xlsr-53-polish, Apache-2.0, ~1.3 GB, CPU is enough) over the window
and finds the best path of the text's letters through its frames (one frame = 20 ms).

The model has letters only: numbers are spelled out for the alignment ("134" -> "sto trzydzieści
cztery") and the span maps back to the displayed token. Punctuation is dropped.

  align_words(samples_16k, ["Amerykańscy", "naukowcy", "1", "do", "1"]) -> [(start_s, end_s), ...]

Usage (test): python align.py --src source.mp4 --from 40.4 --to 45.0 --text "Amerykańscy naukowcy ..."
"""
import argparse, re, subprocess
import numpy as np

MODEL = "jonatasgrosman/wav2vec2-large-xlsr-53-polish"
_M = {}

ONES = ["zero", "jeden", "dwa", "trzy", "cztery", "pięć", "sześć", "siedem", "osiem", "dziewięć", "dziesięć",
        "jedenaście", "dwanaście", "trzynaście", "czternaście", "piętnaście", "szesnaście", "siedemnaście",
        "osiemnaście", "dziewiętnaście"]
TENS = ["", "", "dwadzieścia", "trzydzieści", "czterdzieści", "pięćdziesiąt", "sześćdziesiąt", "siedemdziesiąt",
        "osiemdziesiąt", "dziewięćdziesiąt"]
HUND = ["", "sto", "dwieście", "trzysta", "czterysta", "pięćset", "sześćset", "siedemset", "osiemset", "dziewięćset"]


def spell(n):
    """Polish cardinal for 0-999999, the nominative form: enough to align, not to print."""
    if n < 20:
        return ONES[n]
    out = []
    if n >= 1000:
        th, n = divmod(n, 1000)
        if th == 1:
            out.append("tysiąc")
        else:
            last = th % 10
            form = "tysiące" if 2 <= last <= 4 and not 12 <= th % 100 <= 14 else "tysięcy"
            out += [spell(th), form]
        if n == 0:
            return " ".join(out)
    h, r = divmod(n, 100)
    if h:
        out.append(HUND[h])
    if r >= 20:
        out.append(TENS[r // 10])
        if r % 10:
            out.append(ONES[r % 10])
    elif r:
        out.append(ONES[r])
    return " ".join(out)


def spoken(token):
    t = token.lower().strip(".,?!…:;\"'()*_")      # *emphasis* markers are not spoken
    if re.fullmatch(r"\d+", t):
        return spell(int(t)).split()
    t = re.sub(r"[^a-ząćęłńóśźż]", "", t)
    return [t] if t else []


def model():
    if not _M:
        import torch
        from transformers import Wav2Vec2ForCTC, Wav2Vec2FeatureExtractor
        from huggingface_hub import snapshot_download
        path = snapshot_download(MODEL, allow_patterns=["config.json", "preprocessor_config.json", "vocab.json",
                                                        "pytorch_model.bin"])
        import json, os
        _M["fe"] = Wav2Vec2FeatureExtractor.from_pretrained(path)
        _M["net"] = Wav2Vec2ForCTC.from_pretrained(path).eval()
        _M["vocab"] = json.load(open(os.path.join(path, "vocab.json"), encoding="utf-8"))
        _M["torch"] = torch
    return _M


def align_words(samples, tokens, sr=16000):
    """Return (start, end) in seconds from the window start for every display token, or None
    when the path is implausible (times going backwards). CTC letters are single 20 ms spikes, so a
    one-letter word ("i", "z", "w") is 20 ms long: ends are stretched to 60 ms, starts are the signal."""
    m = model()
    torch, vocab = m["torch"], m["vocab"]
    blank, sep = vocab["<pad>"], vocab["|"]
    groups = [spoken(t) for t in tokens]
    ids, owner = [], []                      # letter ids, and which display token each belongs to
    for k, words in enumerate(groups):
        for w in words:
            if ids:
                ids.append(sep); owner.append(None)
            for ch in w:
                if ch in vocab:
                    ids.append(vocab[ch]); owner.append(k)
    if not ids:
        return None
    with torch.inference_mode():
        x = m["fe"](samples, sampling_rate=sr, return_tensors="pt").input_values
        em = torch.log_softmax(m["net"](x).logits[0], dim=-1).numpy()
    T, L = em.shape[0], len(ids)
    if T < L:
        return None
    sec = len(samples) / sr / T
    # CTC trellis: best score of having emitted the first j letters after t frames
    tr = np.full((T + 1, L + 1), -np.inf, dtype=np.float32)
    tr[0, 0] = 0
    tr[1:, 0] = np.cumsum(em[:, blank])
    tok = np.array(ids)
    for t in range(T):
        stay = tr[t, 1:] + em[t, blank]
        move = tr[t, :-1] + em[t, tok]
        tr[t + 1, 1:] = np.maximum(stay, move)
    # backtrack from the end: which frame emitted which letter
    j, frames = L, [None] * L
    for t in range(T, 0, -1):
        if j == 0:
            break
        stay = tr[t - 1, j] + em[t - 1, blank]
        move = tr[t - 1, j - 1] + em[t - 1, tok[j - 1]]
        if move >= stay:
            frames[j - 1] = t - 1
            j -= 1
    if j > 0:
        return None
    spans = [[None, None] for _ in tokens]
    for i, f in enumerate(frames):
        k = owner[i]
        if k is None:
            continue
        s, e = spans[k]
        spans[k] = [f if s is None else min(s, f), f if e is None else max(e, f)]
    out = []
    for s, e in spans:
        if s is None:
            return None
        out.append((round(s * sec, 3), round(max((e + 1) * sec, s * sec + 0.06), 3)))
    if any(b[0] < a[0] for a, b in zip(out, out[1:])):
        return None
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--from", dest="a", type=float, required=True)
    ap.add_argument("--to", dest="b", type=float, required=True)
    ap.add_argument("--text", required=True)
    a = ap.parse_args()
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(a.a), "-to", str(a.b), "-i", a.src, "-map", "0:a:0",
                          "-ac", "1", "-ar", "16000", "-f", "f32le", "-"], capture_output=True, check=True).stdout
    toks = a.text.replace("|", " ").split()
    res = align_words(np.frombuffer(raw, dtype=np.float32), toks)
    for t, r in zip(toks, res or []):
        print(f"{a.a + r[0]:8.3f} {a.a + r[1]:8.3f}  {t}")
    if res is None:
        print("alignment failed")


if __name__ == "__main__":
    main()
