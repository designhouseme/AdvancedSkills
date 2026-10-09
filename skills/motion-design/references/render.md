# Rendering: requirements, cost, failures

Read when the render is slow, crashes or leaves rubbish behind, and before the first render on a new machine. The scripts in `scripts/` already have the bugs described below fixed: don't write your own renderer.

## Requirements

- **Node 22+** (built-in WebSocket). `render.mjs` drives a local Chromium through the DevTools Protocol on 127.0.0.1 and needs no npm packages and no internet.
- **Chromium or Chrome.** The script looks for `/usr/bin/chromium`, Chrome, Chromium on macOS and `~/.cache/ms-playwright`. Another path: `--chrome /path`. Running as root, it adds `--no-sandbox` itself.
- **ffmpeg** with libx264 (and libwebp for WebP), **ffprobe**, **Python 3** for the checks and optional timeline compiler. Frame review also needs FFmpeg's `drawtext` filter and an available font. Pillow is optional for the older export checks; the new timeline and frame-review tools use Python's standard library.

## Capture contract and preflight

The page exports `__ready` (Promise), `__render(seconds)` (function) and `__DURATION` (positive seconds). Optional `__SIZE: {w, h}` sets positive even pixel dimensions; otherwise the renderer uses 1920×1080. `__SUB` chooses the subframe count. `__CUES: [{t, d?, ...}]` marks review moments and `__CUTS: [seconds]` declares hard cuts strictly inside the film. Both use output seconds after retiming. Keep the capture clock independent of the browser's live preview.

`__ready` resolves after the composition's assets and scene setup finish. The renderer also waits for declared fonts and current images. It awaits a returned Promise from **every** `__render(t)`, then a paint opportunity, before capture. Async work must still yield the same complete state for the same `t`. Set all visible state on each seek; never assume the preceding frame ran.

```bash
node render.mjs --src index.html --preflight
node render.mjs --src index.html --preflight --timeline timeline.generated.json
```

Preflight checks tool versions, encoding/filter support, optional audio, dimensions and one captured frame. It records available memory/disk space, render settings and SHA-256 hashes in `out/environment.json`; availability is diagnostic, not a prediction that a whole film fits. Remote HTTP(S)/WebSocket assets are blocked during capture. Missing assets, rejected promises, console errors and page exceptions fail the run. Put assets in local project files. Early failures also replace the relevant diagnostic report with a failed status when its output path can be determined and written. An ambiguous path or unwritable directory can only produce a terminal error; always check the process exit code.

CLI values are validated: positive **integer fps**, subframes 1–128, workers 1–64, shutter 0–1, finite nonnegative sample times. `--timeout 30000` is a per-operation timeout in milliseconds, not a whole-film deadline. Rational fps such as `30000/1001` is deliberately unsupported in this version. See `node render.mjs --help` for all options.

With `--timeline`, the generated object is injected as `window.__TIMELINE` before page initialization. Dimensions, duration and fps must agree with the composition. Retiming belongs to `compile_timeline.py --speed`, and renderer `--speed` is rejected to prevent a second retime. Without a manifest, the existing HTML contract and query parameters work unchanged. See [project contract](project-contract.md).

## Sampled frame repeatability

```bash
node render.mjs --src index.html --check-frames
node render.mjs --src index.html --check-frames --times 0,1.5,3.6
```

Use the same manifest, dimensions, fps and composition parameters as the final render. Default samples cover an evenly spaced grid and selected cut/cue boundaries, capped at 128; explicit times focus on a suspected problem. The checker compares decoded RGBA pixels from screenshots **before** lossy encoding, across forward/reverse/shuffled seeks, a second Chromium and fresh page loads. It writes `frame-check.json`; mismatches include expected, actual and difference PNGs. A failed run returns a nonzero exit code and replaces the previous report with a failure.

A pass establishes repeatability only for those times and the recorded local toolchain. It does not compare encoded MP4 bytes, all subframes or another operating system. Review the final video separately with [review_frames.py](review.md).

## Cost and measuring

- Measure 2 s of the heaviest part **with the same number of workers** you'll use for the full render: measuring with 4 workers overestimated the time 1.6 times. On a machine busy with other work, the figure includes that load.
- The full render takes roughly ms/frame × number of frames. 47 s at 60 fps with 5 subframes: 5–7 min on 20 cores. The estimate holds on an otherwise idle machine; other renders or builds stretch it.
- By default there are half as many workers as cores, at most 8. Each is a Chromium and an ffmpeg, about 0.5–1 GB of RAM together; with little free memory, lower `--workers`.
- `filter: blur()` on the whole frame and large `box-shadow` slow down every frame. Use them briefly.

## Running in the background

Run the full render as a separate process that survives the end of the session, with a fresh log and an end marker:

```bash
rm -f out/render.log
setsid nohup sh -c 'node render.mjs --src index.html --out film.mp4 > out/render.log 2>&1; echo "exit $?" >> out/render.log' >/dev/null 2>&1 < /dev/null &
until grep -q '^exit' out/render.log 2>/dev/null; do sleep 3; done; tail -3 out/render.log
```

The `rm -f` before the start is needed: an old log with "exit 0" would end the loop at once.

## Motion blur and stepping

- Stills (`--still`) have no motion blur. Blur only shows in the video, so look at 1–2 frames of the measuring fragment (`ffmpeg -ss 1 -i out/part-….mp4 -frames:v 1 frame.png`): they're free.
- 5 subframes smooth motion up to about 60 px per frame. Faster edges (a whip pan, an iris growing 100+ px per frame) step: blur them directionally (`whipBlur`) or soften the edge (`iris(…, { feather })` with feather ≈ 0.6 · |vel|).
- A large object turning fast (a 180° flip on `io4`) moves its far edge 100+ px per frame, and directional blur doesn't fit a rotation: set `SUB` in the composition to 8–10 (the time grows in proportion) or use a gentler curve. Check the fastest passage, not only the most expensive one.
- A thin detail steps sooner than a large edge: it shows as separate copies when its speed × shutter / (subframes − 1) is more than its width. A 5 px line at 51 px per frame with 5 subframes: 51 × 0.5 / 4 ≈ 6.4 px > 5 px, so five lines instead of one.
- `SUB` in the composition is the default for `render.mjs`; `--sub` overrides it for one run, e.g. a test passage.
- The shutter samples preceding times. At a declared hard cut, samples clamp to that cut so the first incoming frame cannot blend the outgoing scene. Declare real cuts only; an overlap should retain its continuous motion blur.

## Supplied audio and fragments

```bash
node render.mjs --src index.html --audio narration.wav --out film.mp4
node render.mjs --src index.html --audio narration.wav --from 4 --to 6 --out excerpt.mp4
```

Video frame count owns the output length. Audio is padded with silence if short and trimmed if long; it cannot shorten the film. A fragment takes audio from the same output-time interval as its video and resets timestamps to zero. Range endpoints are rounded to frame boundaries; the end frame is exclusive. `--speed` changes the legacy composition's visuals, **not** the supplied track's tempo. Obtain a separately retimed track when speech or music must follow that change. This interface supports one supplied track; it is not a multi-track mixer.

## Artifact publication and evidence

Workers write into a unique `out/.render-*` directory. After encoding, ffprobe checks decoded frame count, dimensions and duration. The renderer rechecks hashes of the HTML, compiled timeline, supplied audio and observed local resources before publishing. A changed input fails the render. Successful publication replaces the MP4 atomically, including when `--out` is on another filesystem; failed rendering leaves a previous master intact.

`film.mp4.render.json` records the exact final artifact hash, source/resource hashes, tool versions, render settings, frame range and audio policy. `environment.json` describes that run's environment. For legacy films only, the probe writes `out/cues.json` once; compiled timeline files are never overwritten. Keep evidence beside the output and check its artifact hash after moving or re-encoding a film. Separate concurrent renders should have separate output directories and filenames, since diagnostic reports use fixed names.

## Failures and cleaning up

- **`ERROR:` messages** from `render.mjs` say what to fix. Exit code 2 is bad input (missing file, Node, Chromium), 1 is a failure during the render.
- **`[console]` and `[page]` in the error** identify composition failures (e.g. a font didn't load). They stop capture. `[console.log]` lines are the composition's own messages, at most 50 per browser.
- **"Socket path too long":** Chromium's sockets have a path length limit. With a long `TMPDIR`, `render.mjs` puts the profile in `/tmp`; don't move `TMPDIR` into a deep folder.
- **After a forced kill or host failure**, ffmpeg or Chromium processes may remain. Normal failure, Ctrl+C and SIGTERM trigger cleanup. At the start, `render.mjs` prints a cleanup line for that run alone (its PID is in the profile names, its segments are in a unique `out/.render-*` directory): use that line. A broad pattern such as `motion-chrome` also kills renders in other folders and sessions, and never touch the user's browsers.
- **zsh aborts the whole command** when a glob matches nothing (`rm out/still-*`). Use `find … -delete` or `bash -c`. zsh also doesn't split an unquoted `$var` into words (`for f in $files`): write such loops in bash.

## Composition pitfalls that `check_film.py` catches

- `Math.random()`, `Date.now()`, `setInterval()`, CSS animations and transitions: frames stop being repeatable.
- `will-change: transform`: Chrome draws the layer once at the old scale, and zooming makes the picture blurry.
- Resources from the internet (Google Fonts, images from a CDN): the render depends on the network, and a font may not load in time.
- A missing font file: the video comes out in a fallback font with no warning on screen.
- An empty first frame: it's the thumbnail and the start of autoplay.

Not covered by the script, only by eye: stepping in the fastest passage after a change of palette (grey hides it; the first contrasting palette showed rings in a fast zoom), and a `filter` (e.g. a whip pan's blur) on an element with `preserve-3d` turns off its children's perspective; irrelevant during a whip pan, it matters in a 3D scene.

## Delivery

- **Master:** H.264, crf 17, yuv420p, `+faststart`, 60 fps by default or the chosen integer fps. 47 s with grain is about 70 MB.
- **To send:** `export.sh mp4 … MB` makes 2 x264 passes to the given size. Give the limit itself: the script keeps 5% headroom for the container and the encoder's error, and a master that already fits is copied instead of encoded again (a second encode at the same size only costs quality). Check the result with `check_film.py --small … --max-mb`. Grain eats bits: with a small file, look at a frame for blotches.
- **README:** an animated WebP (`export.sh webp`), about 5–6 MB for 47 s at 800 px and 15 fps. libwebp writes the file only at the end, so several minutes without change is normal. ffmpeg can't read an animated WebP: check it with `check_film.py --webp`. GitHub doesn't play an MP4 from the repo in a README; WebP or GIF does. The file must be committed.
- **Poster:** `export.sh poster film.mp4 <second> poster.png`, ideally a frame from the end card.
