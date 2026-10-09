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
- **Only recorded sound, never synthesised.** Effects and music come from real recordings with a licence that allows use in a published MP4 (bought packs, CC0, Pixabay, Mixkit). Whooshes, clicks and pops synthesised from noise and sine were tried and sounded bad (review, 9.10.2026); never build a stand-in. No file, no sound: say which moments are silent. Trending TikTok sounds go on in the app.
- **Inserts explain, the face carries the personality.** Full-screen motion inserts go over the explanation (a number, a process, a result), never over the punchline or the reaction. Each starts on a phrase and ends on a phrase or the cut, starts in motion (no empty first frame after a hard cut), keeps moving during a hold (a 1-5% push; `check.py` flags a still stretch) and uses the captions' palette and typeface. Build them with the motion-design skill's renderer.
- **No big title unless asked.** A heavy title over the first seconds was rejected; the spoken hook and its caption do the job.

## Workflow

### 0. Setup (once per machine)

Needs ffmpeg with libass, Python 3, `uv`, and for speed an NVIDIA GPU (CPU works with `--device cpu`, several times slower). About 4 GB for the environment and 4.1 GB of models (Whisper large-v3 2.9 GB, the Polish aligner 1.2 GB, the hand model 8 MB); check free disk first.

```bash
uv venv --python 3.12 ~/.cache/video-edit/venv
VP=~/.cache/video-edit/venv/bin/python
uv pip install --python $VP faster-whisper nvidia-cublas-cu12 "nvidia-cudnn-cu12==9.*" numpy pillow "opencv-python-headless<5"
uv pip install --python $VP torch --index-url https://download.pytorch.org/whl/cpu   # CPU build: the PyPI one pulls 5+ GB of CUDA
uv pip install --python $VP transformers mediapipe svgelements
mkdir -p ~/.cache/video-edit/models && curl -so ~/.cache/video-edit/models/hand_landmarker.task \
  https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task
PY=$VP; SK=<this skill's folder>/scripts
```

Pillow measures caption widths with the caption's own font file (libass size 100 = Pillow size 83.3). OpenCV 4.x ships the Haar face cascade `faces.py` uses (5.x doesn't). torch + transformers run the forced aligner (`align.py`, `jonatasgrosman/wav2vec2-large-xlsr-53-polish`, Apache-2.0). MediaPipe's hand landmarker (Apache-2.0) tracks the fingers for `hands.py`; svgelements turns icon SVGs into caption-layer drawings. Inter Display Bold and Black (OFL) are in `assets/fonts/` (plus Inter SemiBold/Black).

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
  "captions": {"style": "words", "font": "Inter Display Bold", "font_emph": "Inter Display Black", "size": 96,
               "spacing": -4, "emph_spacing": -8, "emph_scale": 1.9, "color": "#F2EFE9", "case": "as_written",
               "y": 1250, "shadow": {"dy": 4, "blur": 7, "alpha": "98"},
               "font_file": "<skill>/assets/fonts/InterDisplay-Bold.ttf", "font_emph_file": "<skill>/assets/fonts/InterDisplay-Black.ttf"},
  "angles": {"max_shot": 2.6, "min_shot": 1.1, "close": 1.3},
  "framing": {"mode": "face", "face_y": 0.40},
  "ending": {"word": "pracowników", "zoom": 1.32},
  "fx": [
    {"type": "hand_icon", "icon": "googlemaps", "label": "Google Maps", "word": "Google", "seg": 6},
    {"type": "burst", "word": "branding", "seg": 1},
    {"type": "icon", "icon": "facebook", "word": "Facebooku", "seg": 15},
    {"type": "list", "header": "Przygotowujemy:", "seg": 6, "until_seg": 7,
     "items": [{"word": "wizytówkę", "text": "Wizytówka Google", "icon": "googlemaps"}]}],
  "audio": {"lufs": -14, "tp": -1.5}
}
```

- `in`/`out`: points you chose in the pauses (source seconds); the script trims them to the pads and lands them on frames. `hold`: picture kept after the last word (a look, a smile); end on the speaker, not on a caption.
- `focus`: the centre of every punch-in as fractions of the frame. Keep y at ~0.5: a punch-in anchored higher (0.4) crops from the top, the chin drops ~250 px at 1.24× and lands in the captions.
- `text`: the approved sentence with its punctuation, and `|` where a new caption page starts. You set the pages by meaning ("Amerykańscy naukowcy | skopiowali 1 do 1 | mózg muszki owocówki"), never by the clock; without `|` the sentence is one page. A page longer than `wrap_chars` breaks into two balanced lines, never inside a `keep_together` pair.
- Captions, `style: words` (the house style since 8.10.2026, from a reference edit the user chose): one word on screen at a time, swapped on its aligned start and held until the next; short words lead into the next content word, at most two words a page (three if ≤14 characters): "w 2026 roku?", "żeby Ci | to ułatwić", "Bo to | na początku". A comma, a sentence end, a cut or an emphasised word closes a page. Inter Display ExtraBold 96 px at -4 px tracking in off-white with a light soft drop shadow (Bold matched the reference's ink, but read as "too thin" in review on a phone; SemiBold 80 px was 30% too small and half as heavy); `*słowo*` in `text` marks an emphasised word: Inter Display Black at ~1.65x. One emphasised word per phrase (12-16 per minute): four in a minute read as "the thick one was used twice". No box, no highlight, no pop: the hierarchy and the swap rhythm are the motion. (Inter is on the generic-look list in ui-without-slop and motion-design; here it is the user's explicit choice, not a default.)
- Captions, `pill` (the earlier style, still supported): a pill under each phrase page (`|` in `text`), one accent fill for pages with a number, and a box under the word being said that slides to the next word. It read as too fast and too busy in review.
- Word times come from `align.py` (forced alignment of the approved text, ~20 ms letters); without the aligner they fall back to a syllable spread that was off by ~150 ms on average and up to 0.9 s.
- `framing: face`: every shot is framed on the face the way an operator frames: centred across, the face centre at `face_y` (0.40) of the height, from the median face position over the shot. Rendered with ffmpeg `perspective` (a source rectangle per frame into a constant frame). Never scale(eval=frame)+crop: crop keeps its first frame's size and pins every zoom to the top-left corner; in review that read as "the zoom flies into the window".
- `ending` (and `punches`): a cut-in to a close-up on a word, the payoff or the CTA verb, with the shot before forced wide so the cut reads; give the last segment a `hold` of ~0.5 s on his face (check the frames: the hold must end before he resets for the next take). An ending that just stops on the last word read as weak.
- `hook`: what the viewer gets if they stay, at the top for the first ~4 s ("Marketing lokalnej firmy / plan na 2026 w minutę"): two lines at most, ~6 words, Inter Display Black ~76 px, words popping in one by one over a soft dark band (the top of the frame is often a bright window), sliding up and out. In the speaker's words, never a promise the film doesn't keep. A big static title was rejected; this is not that.
- Something moves within the first 5 s (the hook, an icon on the first emphasised word, a transition on the first cut); `check.py` warns otherwise.
- `transitions`: a film burn with a shutter flash on chosen cuts (`{"cut": k}`) or insert edges (`{"insert": i, "edge": "in"}`), about one every 10-15 s, not on every cut: warm light leaks peaking on the cut frame with a 3-frame white flash, screen-blended from a black clip (`fxassets.py` builds it once). Each brings a whoosh that peaks on the cut (`whoosh_peak`: where its loudest moment is, 0.30 s by default; measure it for each new file) and a shutter click on the cut frame, if those sounds are in the library.
- `audio`: the mix is voice + music bed + sound effects, loudness-normalised as a whole (-14 LUFS, true peak under -1.5 dBTP). `icon_pop` adds a pop to every icon; `sfx` places any sound on a word, a cut or a time. `music: {"file", "offset", "bed_lufs": -22}`: the track is normalised to the bed level, faded in and out, and ducked ~9 dB under his voice (measured). Use only licensed music: trending TikTok sounds are licensed for use inside the app, not baked into an MP4, so the trending sound goes on in the app. Sounds live in `~/.cache/video-edit/sfx/` as recorded files named `shutter`, `whoosh`, `pop` (wav, flac, mp3 or ogg) plus any you name in `sfx`, with their licence in `LICENSES.md`; a missing one leaves its moments silent and puts a warning in `cuts.json`. You can't hear the mix: report levels and timings, never how it sounds.
- `grade` (optional tool, off by default; use it only when the user asks for a look): a look from a reference video the user likes. `grade.py --ref their.mp4 --src source.mp4 --out look.cube --ab ab.png` matches colour statistics (CIELAB means and spreads, colour 0.5 / lightness 0.35 of the way) into a 3D LUT for the footage only. `cut.py` applies it only with `"grade": {"lut": ..., "enabled": true}`; a listed LUT without that flag does nothing. Show the A/B still first: the reference's look is also its light and subject.
- `angles`: one camera, the feel of several. A segment longer than `max_shot` switches framing at a phrase start (its own framing ↔ a `close` close-up) without cutting the audio, so shots run ~2 s (the reference edit's median was 2.1 s with three cameras). Cap the close-up at ~1.3x on a 1080p source.
- `fx`, effects on the picture, in the caption layer, anchored to a word (`word`, optionally `seg`), never to a second:
  - `hand_icon`: when he counts on his fingers or points while naming something, the icon (and a short `label`) pops above the raised fingers with a burst of lines, follows the hand and leaves when the next one comes. Positions come from `hands.json` through each segment's zoom; no close-up angle starts while one is up, because the crop could cut the hand away and leave the icon floating. `side` restricts it to one hand, but MediaPipe names hands as if the picture were a mirrored selfie: on a normal recording "Left" is his right hand.
  - `burst`: a short burst of lines at the index fingertip, for a point or a beat.
  - `icon`: a glyph above the caption word that names it.
  - `hand_stack`: words he lists ("kwaśna, ciepła, gorzka") pop one by one beside the gesturing hand in Inter Display Black and stack, the earlier ones dimmed; those words leave the bottom captions meanwhile.
  - `list`: a header in Inter Black with items swapping under it ("THE LESS: scripting / hooks"), captions hidden while it is up.
  Icons are Simple Icons (CC0 data; brands' marks belong to their owners: show one only when he names the platform) or built-ins (`web`). White glyphs with the caption shadow, never coloured badges.
- Where his hands do something, put something there. `hands.py --summary` prints the gesture timeline next to the words ("320.88-321.78 point … na Google Maps", "321.88-322.88 count 2 … Facebook i Instagram"); read it before writing `fx`. Effects that sit at the bottom like a second row of captions read as boring in review.
- Caption height comes from the face track (`faces.py`): the pill top stays 30 px under the chin in every frame it is up, through each segment's zoom; one height for the whole film when it fits, else per segment, else above the head. `check.py` reports the smallest clearance.
- `inserts`: full-screen clips over the voice, anchored to the source time of the first word they cover (`src_at`), so re-snapping the cuts keeps them on the same words; one that would run past its segment is shortened. Render them from an HTML composition with `motion-design/scripts/render.mjs` at the edit's frame rate (`--fps 25 --params "scene=1&dur=3.18"`), check stills first. `skip` drops seconds from the clip's head (when its first frames are nearly empty); it shortens the insert, so move `src_at` later by the same amount if the insert has to end on the cut.

### 4. Draft, check, look

```bash
$PY $SK/cut.py --edit edit.json --words edit/words.json --audio edit/audio.json --work edit --out draft.mp4 --draft
$PY $SK/faces.py --src "$SRC" --cuts edit/cuts.json --out edit/faces.json        # after the cuts exist; rerun when they change
$PY $SK/hands.py --src "$SRC" --cuts edit/cuts.json --out edit/hands.json
$PY $SK/hands.py --hands edit/hands.json --words edit/words.json --summary          # gestures next to the words: plan fx here
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
