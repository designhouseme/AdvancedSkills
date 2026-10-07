---
name: video-edit
description: Edits recorded footage into a short that looks cut by a human editor, chiefly a talking head into a TikTok, Reel or Short, with the best takes chosen from the transcript, cuts placed in the pauses between words, punch-ins that hide jump cuts, phrase captions on pills, full-screen motion inserts over the explanation, loudness for social and an EDL for finishing in Resolve or Premiere. Use when someone gives a recording (a raw take, an export with several takes, a podcast or interview clip) and asks to edit it, cut it down, make a TikTok or reel from it, remove pauses and repeated takes, or add captions. Not for motion graphics or animation made from code (that's motion-design), generating footage, or colour grading.
license: CC-BY-4.0
metadata:
  author: Design House
  version: "0.1"
---

# Editing recorded footage

Goal: a short that a viewer takes for the work of an editor, made from the speaker's own best takes, saying only what they said, with every cut where an editor would put it. The model reads; scripts measure and cut. You can't hear the audio or watch the video, so everything about sound and motion comes from a tool's output, never from impression.

## Rules that always apply

- **The words are the speaker's.** Captions and the edit say what was said, in the speaker's words. You may drop takes, reorder whole sentences when the meaning holds, and add a short on-screen title that summarises what they say. You never add a claim, fix a fact in their mouth or caption a word you can't confirm. A doubtful fact goes in your reply ("he says 134 thousand neurons; the FlyWire connectome has ~139 thousand"), not into the film.
- **Never describe sound you didn't measure.** No "warm voice", "upbeat", "clean audio". Loudness, peaks, silences and pauses come from `check.py` and `audio.json`; say what wasn't checked.
- **Cut in silence, decided from the audio, and cut tight.** Whisper's word times start ~150 ms early and drift by over a second after a pause or a restart. Choose in- and out-points from the speech runs (`cut.py --runs`), in the pause before the first word and after the last one; the script pulls them to 0.04 s before the first voiced frame and 0.06 s after the phrase decays (about 0.12-0.17 s of air per cut). Pads of 0.1/0.2 s read as "cut too late after the phrase" in review. A point inside speech is a micro-cut: allowed only at a stop closure or a comma dip, and only after a re-transcript of the window starting there shows the first word whole.
- **Caption text from the full transcript, read and corrected by you.** The full-file transcript has context and spells better; a window transcribed on its own mishears short clips ("i mywię ich metodę" for "i my wzięliśmy tą formę"). Put the approved sentence in each segment's `text`; the script times it over the speech.
- **Every jump cut changes the framing.** One static camera: alternate the zoom on every cut (1.0 and ~1.12-1.16), with a slow push (≤1.5%/s) on longer segments and one stronger push (to ~1.25) into the punchline. Never the same framing either side of a cut.
- **Outtakes stay out.** Camera setup, a hand in front of the lens, reaching to stop the recording, a phone check: look at the frames around every chosen take's end (`ffmpeg ... tile`) before you settle it. A hand reaching for the camera on the last word cost a take swap.
- **No added sound.** No music or effects unless the user supplies licensed files. Leave the bed for the platform (TikTok sounds are added in the app) and say so.
- **Inserts explain, the face carries the personality.** Full-screen motion inserts go over the explanation (a number, a process, a result), never over the punchline or the reaction. Each starts on a phrase and ends on a phrase or the cut, starts in motion (no empty first frame after a hard cut), keeps moving during a hold (a 1-5% push; `check.py` flags a still stretch) and uses the captions' palette and typeface. Build them with the motion-design skill's renderer.
- **No big title unless asked.** A heavy title over the first seconds was rejected; the spoken hook and its caption do the job.

## Workflow

### 0. Setup (once per machine)

Needs ffmpeg with libass, Python 3, `uv`, and for speed an NVIDIA GPU (CPU works with `--device cpu`, several times slower). About 3.6 GB for the environment and 4.1 GB of models (Whisper large-v3 2.9 GB, the Polish aligner 1.2 GB); check free disk first.

```bash
uv venv --python 3.12 ~/.cache/video-edit/venv
VP=~/.cache/video-edit/venv/bin/python
uv pip install --python $VP faster-whisper nvidia-cublas-cu12 "nvidia-cudnn-cu12==9.*" numpy pillow "opencv-python-headless<5"
uv pip install --python $VP torch --index-url https://download.pytorch.org/whl/cpu   # CPU build: the PyPI one pulls 5+ GB of CUDA
uv pip install --python $VP transformers
PY=$VP; SK=<this skill's folder>/scripts
```

Pillow measures caption widths with the caption's own font file (libass size 100 = Pillow size 83.3). OpenCV 4.x ships the Haar face cascade `faces.py` uses (5.x doesn't). torch + transformers run the forced aligner (`align.py`, `jonatasgrosman/wav2vec2-large-xlsr-53-polish`, Apache-2.0).

Polish: Whisper large-v3 (not turbo) had the lowest Polish WER we found (4.74% on FLEURS). Newer models with Polish (Cohere Transcribe 03-2026, VibeVoice-ASR, Nemotron 3.5) don't give verified word-level times, which cutting needs.

### 1. Look and listen with tools

```bash
ffprobe -v error -show_entries stream=codec_type,width,height,r_frame_rate:stream_tags=timecode "$SRC"
ffmpeg -v error -i "$SRC" -vf "fps=1/8,scale=270:-2,drawtext=text='%{pts\:hms}':x=6:y=6:fontsize=20:fontcolor=white:box=1:boxcolor=black@0.6,tile=8x4" -frames:v 1 sheet.png
$PY $SK/transcribe.py --src "$SRC" --out edit/ --language pl
```

Read `edit/transcript.txt` whole. Then check it: a line like "Dzięki za oglądanie!" over a silent stretch is a Whisper hallucination; loud stretches with no words get transcribed on their own before you trust the gap. Note which takes repeat (raw exports often hold 5-9 takes of the CTA), which flubbed ("ma tysiące..." then a restart) and which carry the personality ("tą przepotężną muszką owocówką").

### 2. The story and the brief in one paragraph

Before cutting, write: the reading of the brief in one sentence, the length (TikTok talking head: 30-60 s), the structure (hook in the first 2 s, explanation, a question or turn, the reveal, the CTA), the hook line and whether it is lifted from later (a reorder, say so), and the takes you rejected and why. With "no questions" or "all in", decide and record these in the reply; otherwise show them before rendering.

Pace for talking heads: about 0.33 cuts/s (band 0.19-0.52, Dost & Huang 2026); faster lowered completion in that study. The script leaves 0.04 s before the first voiced frame and 0.06 s after the phrase decays: about 0.12-0.17 s of air per cut, never zero.

### 3. edit.json

```bash
python3 $SK/cut.py --words edit/words.json --audio edit/audio.json --runs 120-180   # speech runs with words
```

```json
{
  "name": "TITLE", "src": "/path/source.mp4", "language": "pl", "focus": [0.52, 0.50],
  "segments": [
    {"in": 40.41, "out": 45.3, "zoom": [1.0, 1.04], "text": "Amerykańscy naukowcy | skopiowali 1 do 1 | mózg muszki owocówki,"},
    {"in": 107.82, "out": 113.5, "zoom": [1.13, 1.16], "text": "czyli 134 tysiące neuronów | zrobione w formie komputerowej."},
    {"in": 195.40, "out": 197.6, "zoom": 1.14, "hold": 0.35, "text": "to link masz w przypiętym komentarzu."}
  ],
  "inserts": [{"src": "inserts/out1/ins1.mp4", "src_at": 107.80, "dur": 3.18}],
  "captions": {"font": "Fira Sans", "weight": "bold", "size": 76, "y": 1250, "case": "as_written", "wrap_chars": 20,
               "accent_words": ["134", "1500"], "keep_together": ["134 tysiące", "1500 Elo"],
               "pill": {"fill": "#F5F0E8", "text": "#17120E", "accent_fill": "#F2B544"}},
  "audio": {"lufs": -14, "tp": -1.5}
}
```

- `in`/`out`: points you chose in the pauses (source seconds); the script trims them to the pads and lands them on frames. `hold`: picture kept after the last word (a look, a smile); end on the speaker, not on a caption.
- `focus`: the centre of every punch-in as fractions of the frame. Keep y at ~0.5: a punch-in anchored higher (0.4) crops from the top, the chin drops ~250 px at 1.24× and lands in the captions.
- `text`: the approved sentence with its punctuation, and `|` where a new caption page starts. You set the pages by meaning ("Amerykańscy naukowcy | skopiowali 1 do 1 | mózg muszki owocówki"), never by the clock; without `|` the sentence is one page. A page longer than `wrap_chars` breaks into two balanced lines, never inside a `keep_together` pair.
- Captions: a pill under each page (the drawing is sized from the text), one accent fill with one meaning (here: pages with a number), a soft shadow under the pill, inside the TikTok safe area (x 60-920, y 200-1450). Without `pill`, the captions fall back to white text with a soft dark halo.
- The word being said: one box behind it (amber on a cream pill, cream on an amber pill) that slides to the next word in 90 ms and stretches to its width; words not yet said are dimmed and come up as they are said. One mechanism only: no bounce, no colour cycling. Word times come from `align.py` (forced alignment of the approved text, ~20 ms letters); without the aligner they fall back to a syllable spread that was off by ~150 ms on average and up to 0.57 s.
- Caption height comes from the face track (`faces.py`): the pill top stays 30 px under the chin in every frame it is up, through each segment's zoom; one height for the whole film when it fits, else per segment, else above the head. `check.py` reports the smallest clearance.
- `inserts`: full-screen clips over the voice, anchored to the source time of the first word they cover (`src_at`), so re-snapping the cuts keeps them on the same words; one that would run past its segment is shortened. Render them from an HTML composition with `motion-design/scripts/render.mjs` at the edit's frame rate (`--fps 25 --params "scene=1&dur=3.18"`), check stills first.

### 4. Draft, check, look

```bash
$PY $SK/cut.py --edit edit.json --words edit/words.json --audio edit/audio.json --work edit --out draft.mp4 --draft
$PY $SK/faces.py --src "$SRC" --cuts edit/cuts.json --out edit/faces.json        # after the cuts exist; rerun when they change
$PY $SK/cut.py --edit edit.json --words edit/words.json --audio edit/audio.json --work edit --out draft.mp4 --draft
python3 $SK/check.py --film draft.mp4 --work edit --max 60
```

Fix every ERROR. Read every WARNING: "heard … vs caption …" is a signal to look, not proof (the window transcript flips with a 40 ms shift); a micro-cut warning needs the re-transcript of the window starting at the cut. Then look at `edit/strips_*.png` (frames ±0.12 s and the waveform of the second around each cut) and `edit/frames.png`, and at full-size frames of the title, the widest caption page, an accent page and the last frame.

### 5. Final

```bash
$PY $SK/cut.py --edit edit.json --words edit/words.json --audio edit/audio.json --work edit --out final.mp4
python3 $SK/check.py --film final.mp4 --work edit --max 60
```

Deliver the MP4 and `edit/edit.edl` (CMX3600 with the source timecode, so the cut opens in Resolve or Premiere for finishing; zooms are noted as comments, not applied there).

## Pitfalls

- **faster-whisper can't open files with newer PyAV**, and CTranslate2 needs CUDA 12 libraries even on a CUDA 13 system: `transcribe.py` feeds raw samples from ffmpeg and preloads the pip CUDA libraries.
- **A cut chosen from Whisper's times lands in the wrong place.** In the test, "I nauczyliśmy" was timed 1.5 s early (before a pause), and "też" 0.7 s early. Always read the runs.
- **Cutting a word out of continuous speech garbles it.** "elo | i gra lepiej ode mnie" re-transcribed as "No i galepi ode mnie"; the whole take was used instead.
- **A caption page can flash for 0.1 s** when a short word is split off; check.py flags pages under 0.35 s. Mark the pages with `|` instead of trusting the automatic split.
- **CTC letters are 20 ms spikes.** A one-letter word ("i", "z", "w") aligns to 20 ms; checking word length rejected 8 of 10 segments. Use the starts; stretch the ends.
- **The aligner has no digits.** Numbers are spelled for the alignment only ("134" → "sto trzydzieści cztery") and map back to the displayed token.
- **A breath or a click before the first word leaves 0.2-0.5 s of slack** when the onset is "the first frame above the noise". The script waits for three voiced frames and steps back at most 120 ms over the attack.
- **An insert anchored to "segment + offset" drifts onto the next shot** when a cut is re-snapped; anchor it to the source time.
- **The first frame of an insert can be empty** (a counter popping in from alpha 0, a bar still at length 0): after a hard cut it reads as a black flash. Start every element already moving.
- **Clipped source.** Check peaks before the edit (`astats`); the test source peaked at +1.97 dBFS, which loudnorm can't repair. Say so.

## Output

- The film (1080×1920, 25 or source fps, x264 crf 18, AAC 192k, −14 LUFS / −1.5 dBTP, BT.709 tags), the EDL and the insert clips next to the source (the EDL holds the cuts only; the inserts go on a track above in the editor).
- In the reply: the structure and the takes used, the decisions you made for the user (title, reorders, framing, accent), what you couldn't check (anything you'd have to hear), what to do in the app (sound, cover frame, pinned comment), and any fact the speaker states that looks wrong.
