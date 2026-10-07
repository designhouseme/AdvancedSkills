#!/usr/bin/env python3
"""Transcribe a recording with Whisper large-v3 (faster-whisper) and write the edit's text index.

Writes into --out:
  words.json       every word with start/end in seconds and probability, plus segments
  transcript.txt   phrase-packed reading view: one line per phrase, "[start-end] text",
                   a new line after a pause of --gap seconds or at the end of a sentence
  audio.json       loudness per 10 ms window (dBFS), used later to snap cuts into silence

Whisper's own word times start about 150 ms early (FA-Bench, English), so never cut on them
directly: cut.py snaps every cut to the quietest 10 ms window near the word edge.

Usage:
  python transcribe.py --src "input.mp4" --out edit/ [--language pl] [--model large-v3]
"""
import argparse, json, subprocess, sys, time
from pathlib import Path

import numpy as np


def extract_audio(src: Path) -> np.ndarray:
    # Raw float samples straight from ffmpeg: faster-whisper's own decoder breaks on newer PyAV.
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(src), "-map", "0:a:0", "-ac", "1",
                          "-ar", "16000", "-f", "f32le", "-"], check=True, capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32)


def preload_cuda_libs() -> None:
    # CTranslate2 dlopens libcublas.so.12 / libcudnn*.so.9 by name; the pip wheels keep them outside
    # the loader path, so load them by full path first (dlopen then reuses them by soname).
    import ctypes, glob, site
    for sp in site.getsitepackages():
        for pattern in ("nvidia/cublas/lib/libcublasLt.so*", "nvidia/cublas/lib/libcublas.so*",
                        "nvidia/cudnn/lib/libcudnn*.so*"):
            for lib in sorted(glob.glob(f"{sp}/{pattern}")):
                try:
                    ctypes.CDLL(lib, mode=ctypes.RTLD_GLOBAL)
                except OSError:
                    pass


def loudness_envelope(samples: np.ndarray, hop: float = 0.01) -> list:
    n = int(16000 * hop)
    frames = samples[: len(samples) // n * n].reshape(-1, n)
    rms = np.sqrt((frames ** 2).mean(axis=1) + 1e-12)
    return [round(float(v), 1) for v in 20 * np.log10(rms)]


def phrases(words, gap: float):
    out, cur = [], []
    for w in words:
        if cur and (w["start"] - cur[-1]["end"] >= gap or cur[-1]["word"].rstrip().endswith((".", "?", "!"))):
            out.append(cur)
            cur = []
        cur.append(w)
    if cur:
        out.append(cur)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--language", default="pl")
    ap.add_argument("--model", default="large-v3")
    ap.add_argument("--gap", type=float, default=0.6, help="pause (s) that starts a new phrase line")
    ap.add_argument("--device", default="cuda", help="cuda, or cpu (int8, several times slower)")
    a = ap.parse_args()

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    samples = extract_audio(Path(a.src))

    preload_cuda_libs()
    from faster_whisper import WhisperModel
    t0 = time.time()
    model = WhisperModel(a.model, device=a.device, compute_type="float16" if a.device == "cuda" else "int8")
    # No VAD filter: it drops short fillers and breaths, which the editor must see to cut them.
    segs, info = model.transcribe(samples, language=a.language, beam_size=5, word_timestamps=True,
                                  condition_on_previous_text=False, vad_filter=False)
    segments, words = [], []
    for s in segs:
        ws = [{"word": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3),
               "p": round(w.probability, 3)} for w in (s.words or []) if w.word.strip()]
        words.extend(ws)
        segments.append({"start": round(s.start, 3), "end": round(s.end, 3), "text": s.text.strip(),
                         "no_speech": round(s.no_speech_prob, 3), "avg_logprob": round(s.avg_logprob, 3)})
    took = time.time() - t0

    json.dump({"language": info.language, "duration": info.duration, "model": a.model,
               "segments": segments, "words": words}, open(out / "words.json", "w"), ensure_ascii=False, indent=1)
    json.dump({"hop": 0.01, "db": loudness_envelope(samples)}, open(out / "audio.json", "w"))

    lines = []
    for ph in phrases(words, a.gap):
        low = [w["word"] for w in ph if w["p"] < 0.5]
        flag = f"   (unsure: {', '.join(low)})" if low else ""
        lines.append(f"[{ph[0]['start']:7.2f}-{ph[-1]['end']:7.2f}] {' '.join(w['word'] for w in ph)}{flag}")
    (out / "transcript.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{len(words)} words, {len(lines)} phrases, {info.duration:.1f} s of audio, {took:.1f} s on GPU -> {out}")


if __name__ == "__main__":
    sys.exit(main())
