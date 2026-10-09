---
name: motion-design
description: Makes motion design videos and animations from code, in the brand's colours, fonts and logo, built on a clear idea instead of a template, plus a version small enough to send and an animation for a README. Use when someone asks for a video, an animation, "motion graphics", a showreel, a product or app promo, an intro or animated logo, kinetic typography, an Instagram or TikTok reel, a GIF or animated WebP, including changes to such a video (pace, name, scene, format, file size). Interface animation belongs to ui-motion (website-build owns sites built from a plan); editing recorded footage belongs to video-edit. Not for generating images or authoring Lottie assets.
license: CC-BY-4.0
metadata:
  author: Design House
  version: "1.2"
---

# Motion design from code

Goal: a video with an idea nobody else would have had, in the brand's real colours, that tells only the truth about the product and can be changed with one parameter. The video is an HTML page in which every frame is a function of time; a local Chromium and ffmpeg turn it into pictures through the scripts in `scripts/`.

## Rules that always apply

- **The first idea is the average.** A logo with a glow, a spinning phone and text sliding up from the bottom is what every model makes, and nobody remembers it. Before you write a scene, go through the concept stage (step 2).
- **Truth about the product before effect.** Show features that exist and work the way they do on screen; for every scene, establish who does what. In the ReviewLink showreel the scene "we text your customers" was untrue (the business sends the link itself) and had to be rebuilt. A QR code leads to a working address, you don't invent domains, and you don't draw other companies' logos.
- **No added storyline.** "Change to X, new name" means: show X. Make the story of the change only on explicit request. Write your reading of the brief in one sentence before you build scenes: fixing a storyboard costs a minute, fixing a render costs a dozen.
- **The name is one parameter, and you flag a suspicious spelling straight away.** Use it exactly as in the brief (`NAME`); another case, such as a lowercase wordmark, is a proposal you show, not a silent change. If it looks like a typo ("RewievLink" instead of "ReviewLink"), ask in your first message. A late question cost a full render.
- **The brand comes from the project's files, not from memory.** Colours from the CSS, the font from local files, the logo from the original SVG, app screens rebuilt from the app's CSS (no `iframe`, because a live app has its own timers). When the brand has no logo, build the mark from the name plus one shape from the product's verb; record this as an assumption.
- **Colour and type are decisions, not defaults.** The model's usual look (Inter or its substitutes, a purple gradient, a neon glow, cream with a serif and terracotta, black with an acid accent) makes a video look generated before anything moves. Use the brand's values; without them, choose the palette and typeface with `references/look.md` and write down why. The template's grey palette and Urbanist only let the demo render.
- **Every frame is a pure function of time.** `window.__render(t)` sets the whole state, including on a backward seek; no CSS animation clocks, timers, `Date.now()` or unseeded `Math.random()` drive capture. It may return a Promise for deterministic work; the renderer awaits it. Put asset loading in `__ready`. Verify repeatability with `--check-frames` before a full render.
- **Frames first, then the render.** A still costs a second, a full render several minutes.
- **No sound unless someone asks.** You can't hear the result, so you can't judge it. Sound is best supplied by the user (`--audio`). Say which platform expects it: TikTok and Reels play with sound, while in Facebook and LinkedIn feeds many people watch muted, so every spoken line also has to be on screen.

## Workflow

For a targeted change to an existing film, inspect its source and approved direction, then change and verify the affected scenes. Repeat the concept stage only when the request changes the concept. Existing approval covers that direction; do not ask for it again.

### 1. Brief

Unless told otherwise: 16:9, 1920×1080, 60 fps (other formats: `references/techniques.md`, section 10); showreel 35–50 s, reel 10–20 s, logo intro 4–8 s; copy in the product's language, in the words of its interface; no sound; a master MP4, plus a version under the given size limit and a WebP for a README when they're needed. Collect the material: tokens from the CSS, the font (woff2), the logo (SVG), illustrations, the code or screenshots of the screens you'll show.

### 2. Concept

Read `references/concept.md` and `references/look.md` and write down:

1. the product's verb (what it does for the customer, as a motion),
2. three obvious ideas you reject, each with a replacement,
3. three clearly different directions: idea, world, look, signature, transitions,
4. for the chosen one, the palette as named values and the typeface with the reason, or where they come from in the brand.

Pick the boldest direction that is true to the product and can be built in reasonable time. The swap test: if another model would make almost the same thing from a similar brief, the direction is too safe.

### 3. Storyboard and checkpoint

Read `references/storyboard.md` and write the table: time, what's on screen, motion, how the scene ends, continuity object. Plan a hook in the first 2 s, a surprise every 5–8 s, a climax and a rest.

Show the user the three directions, your choice, the storyboard in a few lines and your one-sentence reading of the brief (plus the spelling question if needed), and wait for approval. Skip this checkpoint when someone wrote "no questions" or isn't at the keyboard; then record your assumptions in the reply.

### 4. Project skeleton

```bash
SK=<this skill's folder>; F=<the film's folder, e.g. design/film in the project's repository>
mkdir -p $F && cp $SK/assets/template.html $F/index.html && cp -r $SK/assets/fonts $F/ \
  && cp $SK/scripts/render.mjs $SK/scripts/export.sh $SK/scripts/check_film.py \
    $SK/scripts/compile_timeline.py $SK/scripts/review_frames.py $F/
```

Requirements: Node 22+, ffmpeg, Python 3 and Chromium or Chrome; no npm packages. In `index.html` set for good: `W` and `H` (format), `TIMELINE` (length in seconds), `NAME`, the `:root` block with the brand's tokens, `@font-face` and `FAMILY`. Set `WT` (weights by role) to the weights your `@font-face` declares. The grey palette, Urbanist, the demo's copy and `NAME` are placeholders; `check_film.py` warns while they're still there. With the brand's font or the face you chose, put its files and licence in `fonts/` and delete `urbanist-*.woff2` and the demo's `OFL.txt`. The demo scenes show moves from the concept file; delete them or rework them. In a repository, check `.gitignore`: if the film folder is ignored, the sources won't reach the repo, so tell the user.

For films with linked cues, repeated retiming or multiple scenes, use the optional [project timeline](references/project-contract.md): `film.json` → `compile_timeline.py` → `timeline.generated.json`. Start from `assets/timeline-example.html` instead of the legacy template, and pass `--timeline timeline.generated.json` to every render/still/check command. The generated file owns scene times, cuts, cues and integer fps. Keep simple existing HTML films working without migration. Compiled metadata is never replaced with the renderer's legacy `cues.json`.

### 5. Scenes

Before building, read `references/craft.md` (starting values and rules of motion). The code for the moves lives in the template and in `references/techniques.md`; read only the section you need. A scene is `scene(name, from, to, build)`: `build(root)` creates the DOM after the font has loaded and returns `update(t)`; scenes may overlap, and a later one sits on top. For hundreds or thousands of objects (grains, particles of the brand's material), draw on a canvas: `references/techniques.md`, section 11.

After each scene, make stills, including the middle of transitions, and look at them in one image:

```bash
node render.mjs --src index.html --still 0,1.5,3.6,5.2     # out/stills/, cleared every round
./export.sh stills out/stills out/stills.png
```

Offer a live preview: `index.html` opened in a browser plays the video (space, arrow keys, `?t=`). It's the cheapest round of feedback.

### 6. Review and render

Run these before the first full render and after a change to assets or frame logic. Add the same `--timeline`, parameters, fps and subframe settings as the intended render. Read [rendering](references/render.md) for the capture contract, diagnostic artifacts and scope of these checks.

```bash
node render.mjs --src index.html --preflight
node render.mjs --src index.html --check-frames
```

Preflight rejects failed local assets, remote requests and page errors. The frame check compares raw captured pixels across reordered seeks, a second browser and fresh pages. It checks sampled times, not every frame or another machine. Declare hard cuts in `window.__CUTS` (output seconds); generated timelines provide them. Motion blur must not sample the scene before a cut. Overlaps remain continuous transitions.

Go through "Review before the render" (`references/storyboard.md`, section 3) on the stills. Then render two short passages with the default number of workers and look at 1–2 frames of each, because motion blur and stepping only show in the video:

- the most expensive passage (the most elements, blur, shadows): its ms/frame gives the render time;
- the fastest motion, often somewhere else: find it with `vel()` (px per frame). Above about 60 px per frame, and when a large object turns, edges step at 5 subframes: set `SUB` in `index.html` to 8–10 (the render takes proportionally longer) or use a gentler curve. `render.mjs` reads `SUB`, so the full render and every later one keep it. A thin detail steps sooner: when its speed × 0.5 / (`SUB` − 1) is more than its width.

```bash
node render.mjs --src index.html --from 4 --to 6               # at the end: ms/frame overall
node render.mjs --src index.html --from 7 --to 8 --sub 10      # the fastest motion, if it stepped at --sub 5
rm -f out/render.log
setsid nohup sh -c 'node render.mjs --src index.html --out film.mp4 > out/render.log 2>&1; echo "exit $?" >> out/render.log' >/dev/null 2>&1 < /dev/null &
until grep -q '^exit' out/render.log 2>/dev/null; do sleep 3; done; tail -3 out/render.log
```

The full render runs as a separate process because it survives the end of the session. When the render is slow, crashes or leaves processes behind: `references/render.md`.

### 7. Checks

```bash
python3 check_film.py --composition index.html --film out/film.mp4 --length 30 --format 1920x1080 --audio no
python3 review_frames.py --film out/film.mp4 --cues out/cues.json --outdir out/review
```

Use `--timeline timeline.generated.json` instead of `--cues` for a compiled project. For a fragment, omit the full-film contract. The [frame review](references/review.md) decodes every final frame, flags candidate blanks and temporal outliers, and builds timestamped sheets. Its heuristics require judgement: exit 0 can include warnings, and OCR, audio listening and visual approval remain unchecked. Open the sheets listed in `review.json`; inspect suspicious frames at full resolution. Fix every `ERROR`. Fix every `WARNING` or explain it in the reply. Then copy this into the reply and tick it off:

```md
- [ ] concept: verb, three rejected obvious ideas, the chosen direction passes the swap test
- [ ] look: the brand's colours and font, or a palette and typeface chosen with a written reason; no look warning left unexplained
- [ ] sheets of the finished MP4 from review.json viewed in full, flagged frames and 2–3 key frames at full resolution
- [ ] the brand font visible on a frame with accented letters; no clipped letters, overlaps or empty frames
- [ ] every piece of text stays on screen for at least words × 0.3 s + 1 s
- [ ] every sentence and number on screen is backed by the product or clearly marked as an example
- [ ] the name in the spelling the user confirmed
- [ ] check_film.py without errors
- [ ] preflight and sampled frame repeatability passed with the final settings; frame review complete, warnings resolved or explained
```

### 8. Derived versions

```bash
./export.sh mp4  out/film.mp4 out/film-to-send.mp4 25          # the limit itself: 5% headroom; a master that fits is copied
./export.sh webp out/film.mp4 ../../docs/film.webp 800 15 55   # for a README; the file must be committed
python3 check_film.py --film out/film.mp4 --small out/film-to-send.mp4 --max-mb 25 --webp ../../docs/film.webp
```

## Changes after feedback

If the film folder has no scripts (someone else's film, an older project), copy them from the skill first: the last `cp` of step 4.

| Request | Change |
|---|---|
| "25% slower" | compile the source manifest with `--speed 0.75`, or use renderer `--speed 0.75` for a legacy HTML film; never both. State that the video gets a third longer. Supplied audio keeps its original tempo and needs a separate retiming decision |
| "cut that thread" | remove the scene from `film.json` and recompile; for a legacy film, delete the scene and set `shift` before later scenes |
| "change the name" | `NAME` (or `--name` for a one-off); the letters measure themselves, look at a still with the logo |
| "not creative enough" | go back to the concept: a different verb or a different world, not more effects in the same scene |
| "looks generic", "the colours and fonts are slop" | go back to `references/look.md`: three rejected looks, then a palette and typeface with a reason; change the tokens and the font first, then the demo's own motifs (the star and rounded-square mark, the grid, the square wipe) for ones from the brand; keep the copy unless you have the product's lines |
| "different format" | `W` and `H` in `index.html`; layout computed from `W`, `H`, `CX`, `CY` |
| "smaller file", "for the README" | `export.sh mp4 … MB`, `export.sh webp …` and commit the file |
| "for a newsletter", "in an email" | `export.sh poster` as the image, linked to the MP4: Gmail and most email apps don't play video |
| "that's not how it works" | fix the scene and recheck every claim on screen |

## Pitfalls

- **An empty frame in the middle of a transition.** The opaque background of the incoming scene stood still and covered the outgoing scene. Move the whole scene together with its background, or show the background only after the transition.
- **A sliver of a letter at the edge of a mask.** A long rotated word catches the mask with a corner on its way out; the exit must travel at least 1.5 heights (as `animRow` does).
- **A fallback font without a warning.** The template logs an error in the console and `check_film.py` catches a missing file, but still look at a frame with accented letters. Characters the font doesn't have (arrows, stars) should be drawn as SVG.
- **The dot over the "i" too high.** Compute it with `tittle()` from the template; measuring from the top of the canvas instead of the baseline gave a 0.13 em error you don't see without comparing to a real "i".
- **Stepping on fast edges.** 5 subframes smooth motion up to about 60 px per frame; soften a faster iris (`feather`), blur a whip pan directionally, and for a large object turning fast raise `SUB` to 8–10. In a test, the most expensive passage wasn't the one that stepped, and that cost a second full render.
- **Elements outside the camera stay in shot.** A caption attached to the scene rather than the camera stayed on screen while the camera zoomed into the dot.
- **The demo's copy and timing aren't the product's.** "Frame by frame", "MOVE" and the counter are placeholders: replace them with the product's lines, and when you don't have them, keep them, say so and ask. Never invent facts to fill them. On a change of look alone, list what the demo itself doesn't meet (text times, the first frame) instead of ticking it off.
- **Three costly mistakes from the ReviewLink showreel:** an added rebranding storyline, a typo in the name and a feature the product doesn't have. Each needed a full render; the rules at the top are there to catch them before the first one.

## Output

- The film folder (e.g. `design/film/`): `index.html`, which also plays in a browser, `fonts/` and the scripts.
- `out/film.mp4` (master, integer fps; default 60 without a manifest, crf 17), the requested derived versions and the current review sheets.
- Reproduction evidence: the optional source/compiled timeline, `environment.json`, `frame-check.json`, `film.mp4.render.json` and `review/review.json`. Their hashes identify the inputs and artifact actually checked; re-run relevant checks after edits.
- In the reply: the chosen direction and why; the palette and typeface and where they come from; the list of scenes, one sentence each; the readings you assumed (storyline, pace, spelling of the name); length and file sizes; what wasn't checked (e.g. nobody listened to the sound); one command to render again; what needs committing.
