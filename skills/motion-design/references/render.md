# Rendering: requirements, cost, failures

Read when the render is slow, crashes or leaves rubbish behind, and before the first render on a new machine. The scripts in `scripts/` already have the bugs described below fixed: don't write your own renderer.

## Requirements

- **Node 22+** (built-in WebSocket). `render.mjs` drives a local Chromium through the DevTools Protocol on 127.0.0.1 and needs no npm packages and no internet.
- **Chromium or Chrome.** The script looks for `/usr/bin/chromium`, Chrome, Chromium on macOS and `~/.cache/ms-playwright`. Another path: `--chrome /path`. Running as root, it adds `--no-sandbox` itself.
- **ffmpeg** with libx264 (and libwebp for WebP), **ffprobe**, **Python 3** for `check_film.py`. Pillow is optional.

## Cost and measuring

- Measure 2 s of the heaviest part **with the same number of workers** as the full render (the default): measuring with 4 workers overestimated the time 1.6 times.
- The full render takes roughly ms/frame × number of frames. 47 s at 60 fps with 5 subframes: 5–7 min on 20 cores.
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

## Failures and cleaning up

- **`ERROR:` messages** from `render.mjs` say what to fix. Exit code 2 is bad input (missing file, Node, Chromium), 1 is a failure during the render.
- **`[console]` and `[page]` in the log** are errors from the composition (e.g. the font didn't load). Fix them before delivering.
- **"Socket path too long":** Chromium's sockets have a path length limit. With a long `TMPDIR`, `render.mjs` puts the profile in `/tmp`; don't move `TMPDIR` into a deep folder.
- **After an interruption (Ctrl+C, a closed session)** `ffmpeg … image2pipe` processes and Chromium with a `/tmp/motion-chrome-…` profile may remain. Kill them by these patterns, never all of the user's browsers: `pkill -f 'user-data-dir=/tmp/motion-chrome'`, then `rm -rf /tmp/motion-chrome-*`.
- **zsh aborts the whole command** when a glob matches nothing (`rm out/still-*`). Use `find … -delete` or `bash -c`.

## Composition pitfalls that `check_film.py` catches

- `Math.random()`, `Date.now()`, `setInterval()`, CSS animations and transitions: frames stop being repeatable.
- `will-change: transform`: Chrome draws the layer once at the old scale, and zooming makes the picture blurry.
- Resources from the internet (Google Fonts, images from a CDN): the render depends on the network, and a font may not load in time.
- A missing font file: the video comes out in a fallback font with no warning on screen.
- An empty first frame: it's the thumbnail and the start of autoplay.

Not covered by the script, only by eye: a `filter` (e.g. a whip pan's blur) on an element with `preserve-3d` turns off its children's perspective; irrelevant during a whip pan, it matters in a 3D scene.

## Delivery

- **Master:** H.264, crf 17, yuv420p, `+faststart`, 60 fps. 47 s with grain is about 70 MB.
- **To send:** `export.sh mp4 … MB` makes 2 x264 passes to the given size. Give the limit minus about 10% (24 MB for a 25 MB limit). Grain eats bits: with a small file, look at a frame for blotches.
- **README:** an animated WebP (`export.sh webp`), about 5–6 MB for 47 s at 800 px and 15 fps. libwebp writes the file only at the end, so several minutes without change is normal. ffmpeg can't read an animated WebP: check it with `check_film.py --webp`. GitHub doesn't play an MP4 from the repo in a README; WebP or GIF does. The file must be committed.
- **Poster:** `export.sh poster film.mp4 <second> poster.png`, ideally a frame from the end card.
