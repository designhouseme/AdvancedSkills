# Techniques: a catalog with code

The snippets come from a working showreel (ReviewLink, Design House) and from the template `assets/template.html`. The functions `E`, `tw`, `prog`, `spring`, `zoom`, `T`, `el`, `svgEl`, `measure`, `letters`, `wordRow`, `animRow`, `camera`, `iris`, `whipBlur`, `vel`, `typewriter`, `counter`, `pop`, `letterWindow`, `shapeWipe`, `SHAPE`, `morphPath` already live in the template and have been checked on a render. Which move to reach for and when is in `references/concept.md`, section 4. Read only the section you need.

## Contents

1. [Motion curves](#1-motion-curves)
2. [Camera and zooming into an object](#2-camera-and-zooming-into-an-object)
3. [Transitions](#3-transitions)
4. [Typography in motion](#4-typography-in-motion)
5. [Pops and order](#5-pops-and-order)
6. [3D in CSS](#6-3d-in-css)
7. [Lines, data, codes](#7-lines-data-codes)
8. [Texture and accents](#8-texture-and-accents)
9. [Rhythm and sound](#9-rhythm-and-sound)
10. [Formats](#10-formats)

---

## 1. Motion curves

| Curve | Use for | Avoid for |
|---|---|---|
| `E.outExpo`, `E.out4` | entrances of text and objects: fast start, soft landing | exits (the object "hangs" before it disappears) |
| `E.in3`, `E.inExpo` | exits, zooming into an object before a cut | entrances |
| `E.io3`, `E.io4` | camera moves, moving a lockup, morphs | short pops |
| `E.ioExpo` | whip pans: almost all the motion happens in the middle, where the blur is anyway | calm moves |
| `spring(s, f, z)` | small objects: a dot, a star, a chip, an icon | large text blocks and whole scenes |
| `E.outBack`, `E.inBack` | letters that "jump in" with overshoot, anticipation before being sucked in | backgrounds and the camera |
| linear | constant camera drift, marquee, progress bar | anything that should start or finish |

`tw(t, a, b, from, to, curve)` is the basic interpolation. `zoom()` interpolates the scale on a log scale, because a linear move from 1 to 100 looks like a sudden acceleration at the end.

Spring: `f` is the oscillation frequency (2–3 Hz for UI), `z` the damping (0.33 gives a clear bounce, 0.6 a barely visible one). Position: `y = target + (start - target) * (1 - spring(t - t0, f, z))`.

## 2. Camera and zooming into an object

Every scene has a `cam` container. The camera moves world point F to screen point C at scale s:

```js
camera(cam, { fx, fy, s }); // transform: translate(C) scale(s) translate(-F)
```

**Zoom into an object (cut on a shape).** First move F onto the object (io3), a moment later the scale grows (in3, geometrically). When an object of colour X covers the whole screen, the next scene starts on an X background and the cut is invisible.

```js
const f = E.io3(prog(t, 2.55, 3.25));
camera(cam, {
  fx: lerp(CX, dotX, f), fy: lerp(CY, dotY, f),
  s: zoom(t, 2.7, 3.55, 1, 140, E.in3) * (1 + t * 0.008 + punch), // + slow drift and a punch
});
// the scene in the dot's colour starts exactly at 3.55
```

Coverage condition: object radius × final scale > half the screen diagonal (1101 px at 1920×1080). Check the frame just before the cut.

**Infinite zoom.** Every scene sits in a small object of the previous one: a star on the phone screen contains the next scene, which holds another object. Technically it's a chain of zooms into objects: in the last frame of each zoom the object has the next scene's background colour and covers the screen. Two or three links are enough; a longer chain gets tiring.

**Drift.** `s = 1 + t * 0.006` keeps the frame alive without visible motion. More than 1% per second starts pulling attention away from the content.

## 3. Transitions

Every transition needs a reason: a shared shape, colour, direction, or an object that carries over into the next scene. A dissolve without a reason is the last resort.

**Continuity object.** One element carries the viewer through several cuts. In the ReviewLink showreel the dot over the "i" became an orange world, which shrank into a touch point on a phone, and the touch point tapped a star. Plan it in the storyboard, not after the fact.

**Iris and shrinking into a point.** A circle covers the frame when its radius reaches the farthest corner; `iris()` in the template computes this, also for a circle growing from outside the centre, and `feather` softens the edge during fast growth:

```js
iris(shut, E.io4(prog(t, 9.1, 9.7)), { cx: beanX, cy: beanY, color: "var(--bg)", feather: 40 });
```

Shrinking to a target: the centre moves from the middle of the screen to the target and the diameter shrinks to the target's size.

```js
const m = E.io4(prog(t, 12.32, 12.86));
const d = lerp(Math.hypot(W, H) * 1.06, 58, m);       // down to the touch point's diameter
morph.style.cssText = `position:absolute;background:var(--accent);border-radius:50%;
  left:${lerp(CX, tx, m) - d / 2}px;top:${lerp(CY, ty, m) - d / 2}px;width:${d}px;height:${d}px`;
// when m = 1, swap in an identical element inside the target scene (e.g. inside the phone screen)
```

A rectangle turning into a circle (growing `border-radius`) looks cheap and flat. A circle from the first frame looks like a deliberate move.

**Whip pan.** The old scene leaves and the new one enters on the same `ioExpo` curve in 0.6–0.7 s, with directional blur proportional to speed:

```js
const out = (t) => -W * E.ioExpo(prog(t, 6.0, 6.7));
T(oldScene, { x: out(t) });
whipBlur(oldScene, vel(out, t) * 0.15, 0); // vel = px per frame; capped at 48 px in the template
```

Move **the whole scene together with its background**. In the showreel the new scene's background stood still and covered the leaving scene: the middle of the transition was an empty frame. A vertical whip works the same way with `y` and `whipBlur(e, 0, vy)`. `whipBlur` uses one SVG filter: two elements moving at different speeds in the same frame need two filters (copy the `<filter>` with another `id`).

**Reveal with `clip-path`.** The new scene lies on top and is revealed by a circle growing from the centre (or from an object):

```js
const p = E.io4(prog(t, 30.4, 30.95));
root.style.clipPath = p < 1 ? `circle(${p * farthest(CX, CY)}px at ${CX}px ${CY}px)` : ""; // radius to the farthest corner
```

**A transition shaped like the mark.** The logo's shapes pop up in their places (spring), then grow until they cover the frame. The next scene starts on a background in their colour. It's a transition only this brand has:

```js
const wipe = shapeWipe(root, [
  { x: CX - m * 0.16, y: CY + m * 0.1, size: m * 0.3 },   // m = Math.min(W, H)
  { x: CX + m * 0.03, y: CY - m * 0.17, size: m * 0.13 },
  { x: CX + m * 0.2, y: CY + m * 0.05, size: m * 0.19 },
], "var(--ink)");
// in update(t): wipe(t, 7.7); the frame is covered about 0.8 s later
```

**Split screen.** Two scenes in two halves of the frame (`clip-path: inset(0 50% 0 0)` and `inset(0 0 0 50%)`) play at once, e.g. the 4–5★ path and the 1–3★ path. The dividing line can move (`inset(0 ${100 - p}% 0 0)`), and at the end one side pushes the other out or both merge into a card.

**The world changes colour.** At the climax the whole frame takes on the accent colour (a zoom into an object of that colour, an iris or a transition shaped like the mark), and the typography flips to white. Once, at most twice per video, otherwise it stops being an event.

**Wedge.** A skewed panel in the accent colour crosses the screen; swap the scenes at the moment the panel covers everything:

```js
const p = prog(t, 22.25, 22.85);
wedge.style.cssText = `position:absolute;top:-260px;width:2900px;height:1600px;background:var(--accent);
  display:${p > 0 && p < 1 ? "block" : "none"};transform:translateX(${lerp(-3100, 2200, E.io3(p))}px) skewX(-18deg)`;
// old scene visible until 22.55, new one from 22.55
```

**Scale-through.** The old scene grows to 1.5 and disappears (in3, 0.3 s), the new one enters from scale 0.82 (outExpo, 0.6 s). Set `transform-origin` on the element that should "pull" the eye.

**Digit roll (slot).** A column of digits in a mask, scrolled with deceleration to the target digit:

```js
col.innerHTML = Array.from({ length: 30 }, (_, i) => `<div style="height:${h}px">${(29 - i) % 10}</div>`).join("");
col.style.transform = `translateY(${-E.outExpo(prog(t, 28.5, 29.25)) * 29 * h}px)`; // lands on 0
```

## 4. Typography in motion

**Letters with kerning.** Splitting a word into spans destroys kerning. `measure()` measures the position of every letter in the unsplit string (a Range per character), and `letters()` places the spans exactly there. Letter entrance: `outExpo` 0.75 s, 45 ms stagger, starting 1.15 heights lower, 9° rotation, the container has `overflow:hidden` only during the entrance.

**Words from masks.** `wordRow()` gives every word a mask 1.24 em tall plus 12% headroom (descenders and accents). `animRow()` enters from below and exits upwards by 1.5 heights. A shorter travel with rotation leaves the corner of a long rotated word inside the mask, and a sliver of a letter stays on screen.

**The dot over the "i".** Write the word with "ı" (U+0131, dotless i) and draw the dot as your own element. `tittle()` finds its position and radius from the pixel difference between "i" and "ı" on a canvas, measured from the baseline (measuring from the top of the canvas put the dot 0.13 em too high). This gives you a dot that drops in with a spring as the logo's last accent, a zoom into the dot as a cut, a dot in the accent colour. The font needs "ı": check `unicode-range`; the template returns `null` when it's missing.

**Words and colours in a lockup.** Different weights within one name (e.g. "Review" at 300 + "Link" at 600 in the accent colour): measure them separately and place the second part at `x = width of the first + 0.02 em`.

**Typewriter.** `typewriter(text, t, from, to)` returns HTML with a caret that blinks from time. 25–40 characters per second reads naturally.

**Counter.** `counter(n, t, from, to)` with `outExpo`; digits with `font-variant-numeric: tabular-nums`, otherwise the number jumps sideways. Large, thin digits (weight 200–300) look premium.

**Letters as windows.** The next scene is visible only through the letters of a short, heavy word (weight 700–900), and then a zoom into the middle of a letter opens the window onto the whole frame. Both scenes run at once: the lower one is the background colour, the upper one is clipped by the letters.

```js
const win = letterWindow(nextScene, "MOVE", { size: Math.min(W, H) * 0.42, weight: 800 });
// in update(t): win(prog(t, 3.62, 4.2), prog(t, 5.15, 5.95)); letters come in, then a zoom to 60×
```

`letterWindow` finds the zoom point on a canvas, in the middle of a letter's stroke, otherwise the zoom would fall into a gap, and zooms far enough for the stroke to cover the frame before the clipping goes away. Give the next scene motion (a running counter, a moving grid), so the windows show life, not a flat patch.

Chrome caps text at 10,000 px on screen. Above that, SVG text scaled with a `transform` jumps instead of growing, so the template gives the clipping text `text-rendering: geometricPrecision`, which scales the letter shapes instead of the font size. Do the same for any SVG text you zoom into.

**Huge numerals in the background.** Under short lines (a manifesto), one numeral per line, 1000+ px, weight 200, white at 0.17 opacity, in a mask on the right. Each enters from below (`outExpo` 0.8 s) and exits upwards (`in3` 0.3 s) just before the next line. It gives rhythm and scale without extra content.

**Strike-through.** A pill with a border and a 3 px line across its middle, `transform-origin: 0 50%`, `sx` from 0 to 1 (`io3`, 0.18 s), the next pills every 0.12 s. A readable way to say "no sign-up, no password, no subscription".

**Caret, selection, editing.** An "editor" animation (the caret returns to the start, a selection grows, letters disappear) shows a change of text very well, but only when the change is the topic. When someone asks for a new name, show the new name, not the story of the change.

## 5. Pops and order

```js
sq.forEach((d, k) => {
  const p = pop(t, 4.55 + k * 0.08);        // spring from the start moment
  T(d, { s: p, r: (1 - clamp(p)) * -40 });  // a slight rotation that straightens out
});
```

- Stagger 60–80 ms for UI elements, 40–50 ms for letters, 50–70 ms for words.
- Stars filled one by one (1→5) with `pop` is the most readable "5 stars" on screen.
- A chip on a line (e.g. "4–5 ★ review on Google") pops when the line reaches halfway.
- A "notification" toast slides down 60 px from the top with a spring at z = 0.5.

**An interface from blocks.** The product screen comes together in front of the viewer: first plain rectangles in the line colour (card, buttons, rows), each flying in with a spring from a different direction every 50–70 ms, then the content flows into them (text from masks, icons with `pop`). Reading order: top to bottom, left first.

**Kinetic grid.** Tiles in a grid turn in a wave (`rotateY` 0 → 180° with a delay of `(column + row) * 0.05 s`), and each back holds a fragment of a word or image. A parent with `perspective`, a tile with two faces and `backface-visibility: hidden`, like the cube faces in section 6.

**Touch point.** A circle in the accent colour with a white rim (`box-shadow: 0 0 0 5px rgb(255 255 255 / .85)`) and a soft shadow. Travel to the target on `io3`; a press is scale 1 → 0.78 → 1 on a sine over 0.22 s, and a ring grows from the tap (scale 0.3 → 1.7, opacity 1 → 0). When the point acts inside a phone rotated in 3D, put it inside the screen element, not over the scene.

**Typing indicator.** Three dots in a bubble: `y = -max(0, sin((t - t0) * 12 - i * 0.9)) * 8`. It shows "someone is typing" before a message appears.

## 6. 3D in CSS

**Cubes assembling into a logo.** Each cube is a `div` with `transform-style:preserve-3d` and six faces with `backface-visibility:hidden`. You compute the lighting yourself, because CSS has no light:

```js
const FACES = [
  { n: [0, 0, 1], tf: (h) => `translateZ(${h}px)` },
  { n: [0, 0, -1], tf: (h) => `rotateY(180deg) translateZ(${h}px)` },
  { n: [1, 0, 0], tf: (h) => `rotateY(90deg) translateZ(${h}px)` },
  { n: [-1, 0, 0], tf: (h) => `rotateY(-90deg) translateZ(${h}px)` },
  { n: [0, -1, 0], tf: (h) => `rotateX(90deg) translateZ(${h}px)` },
  { n: [0, 1, 0], tf: (h) => `rotateX(-90deg) translateZ(${h}px)` },
];
// CSS "rotateX(a) rotateY(b) rotateZ(c)" rotates a point first around Z, then Y, then X:
const rot = (n, rx, ry, rz) => {
  const [a, b, c] = [rx, ry, rz].map((d) => (d * Math.PI) / 180);
  let [x, y, z] = n;
  [x, y] = [x * Math.cos(c) - y * Math.sin(c), x * Math.sin(c) + y * Math.cos(c)];
  [x, z] = [x * Math.cos(b) + z * Math.sin(b), -x * Math.sin(b) + z * Math.cos(b)];
  [y, z] = [y * Math.cos(a) - z * Math.sin(a), y * Math.sin(a) + z * Math.cos(a)];
  return [x, y, z];
};
const L = [-0.45, -0.75, 0.55].map((v, _, a) => v / Math.hypot(...a)); // light from the left, above, front
// in update: face brightness = 0.18 + 0.82 * max(0, n'·L), colour = mix(dark, light, brightness)
```

Flight: position and rotations go from their start values to zero through `spring(t - start, 0.95, 0.62)`, the cubes launch 0.25 s apart, with an impact sound on landing. **Flattening:** at the end use `scale3d(1, 1, depth → 0.002)`, the face colours fade to the logo's flat colour and the front face gets the logo's corner radius. In the frame where the cubes are flat, swap them for the flat SVG logo in the same place. Build the cubes without rounded corners (rounded faces in 3D leave gaps at the edges).

**Taking it apart in layers.** An interface card (a parent with `preserve-3d`, rotated by about `rotateX(55deg) rotateZ(-30deg)`) separates into layers: background `translateZ(0)`, text `translateZ(60px)`, buttons `translateZ(120px)`, icons `translateZ(180px)`, each layer on a spring every 80 ms. Labels with lines next to the layers (section 7). Then the layers return to zero and the card straightens to a front view.

**Camera over a floor.** The interface tilted like a floor (`rotateX(60deg)`, a parent with `perspective: 1400px`); the camera moves it with `translateY` towards the viewer, and headings stand upright above it (a separate layer without the rotation). Camera motion on `io3`, with no acceleration in the middle.

**A phone in perspective.** A parent with `perspective: 2200px`, a phone (frame 428×894, screen 400×866, radius 72/58 px) rotated `rotateY(-20deg) rotateX(7deg) rotateZ(3deg)`. The shadow is a separate blurred rectangle under the phone that moves with the scale but doesn't rotate. Rebuild the app screen statically from its CSS (colours, radii, spacing); don't embed an `iframe` with the running app, because its timers don't follow `t` and the frames stop being repeatable.

## 7. Lines, data, codes

**Drawing a path.** `pathLength="1"` normalises the length, so drawing is a single number:

```js
const path = svgEl("path", { d: "M560 560 C 770 560, 790 300, 1036 300", fill: "none", stroke: "var(--accent)", "stroke-width": 5, "stroke-linecap": "round", pathLength: 1 }, svg);
path.setAttribute("stroke-dasharray", `${E.io3(prog(t, 16.1, 16.7))} 1`);
```

A dashed line that also draws itself: mask the dashed path with a solid path inside a `<mask>` and animate the mask.

**Shape morph.** Shapes that are star-shaped around their centre (circle, star, rounded square) are described by a radius as a function of angle, and morphing is blending the radii:

```js
const circle = SHAPE.circle(), star = SHAPE.star(5, 0.48), sq = SHAPE.squircle(5, 0.84);
const a = E.io3(prog(t, 8.7, 9.2)), b = E.io3(prog(t, 9.55, 10.05));
const [fa, fb, p] = b > 0 ? [star, sq, b] : [circle, star, a];
// rotate by 72° (the star's symmetry), then on to 90° (the square's): both shapes land straight
const rot = a * ((2 * Math.PI) / 5) + b * (Math.PI / 2 - (2 * Math.PI) / 5);
path.setAttribute("d", morphPath(cx, cy, R, fa, fb, p, rot));
```

Morph shapes that aren't star-shaped (letters, logos with holes) another way: by breaking them into simple shapes, or by dissolving at the moment both have the same outline.

**Freeze frame with a note.** You stop the scene's time (the scene's `t` stays constant for 0.8–1.2 s), and on top a line draws from the detail to a label (`stroke-dasharray`, `pathLength="1"`) and the label slides in from a mask. Then the scene's time resumes. Slightly darkening the rest of the frame (a black layer at 0.3 opacity) leads the eye.

**Particles along a path.** Call `path.getTotalLength()` once, then `path.getPointAtLength(f * len)` for 5 dots offset by 1/5 of a cycle; radius `6 * sin(f * π) + 1`, so they grow and fade at the ends.

**Bar chart.** Bars with `transform-origin: 50% 100%` and `sy = spring(t - (start + i * 0.06), 2.2, 0.42)`. One bar in the accent colour (the tallest or "today"), the rest in the text colour.

**Carousel on an arc.** Position `x = base - scroll`, and the distance from the centre `dx` drives the rest: `y = |dx| * 0.05`, `r = dx / spacing * 3°`, `s = 1.06 - 0.12 * min(1, |dx| / spacing)`. Accelerating on the way out with directional blur turns the carousel into a transition.

**A QR code assembled from modules.** Compute the matrix in advance with a library (e.g. qrcode-generator) and paste it into the file as an array of strings. On a canvas: modules appear in a wave from the centre (delay = distance × 0.028 s + a little `hash`), the three corner markers come in with a 90° rotation and a spring, and a scan line with a glow runs at the end. The code must lead to a real, working address, because someone will scan it.

## 8. Texture and accents

- **Grain:** a 512×512 canvas filled from `hash()`, shifted every 1/24 s of output time, opacity 0.04–0.05. Grain raises the bitrate: for a small file to send, check that it doesn't turn into blotches.
- **Vignette:** a radial gradient to a colour about 15% darker than the background at the edges.
- **Punch:** `1 + sin((t - hit) * 26) * exp(-(t - hit) * 7) * 0.025` multiplied into the camera scale when an important element lands.
- **Shockwave:** a ring with an accent-colour border, scale 0.9 → 4.5 (`outExpo`), border 5 → 0.6 px, opacity 0.55 → 0.
- **Background glow:** a radial gradient in the brand colour whose centre slowly circles (`sin(t * 0.35)`). The background is alive, but nothing jumps.
- **Camera focus:** the end card's background with `filter: blur()` from 18 to 0 px over 0.8–1 s (`out3`), then without the filter, because blur costs render time.
- **Push-in on the background:** a background image (e.g. a 3D render of the brand) scales 1.18 → 1 and straightens from -3° over the whole scene (`out3`). The motion is barely visible, and the frame never stands still.
- **Illustrations:** enter from 300 px below with a -10° rotation (`outExpo` 0.75 s), then only float `sin(t * 2) * 6` px. An illustration that moves all the time pulls attention away from the text.

## 9. Rhythm and sound

- **Beat grid:** plan the times on a grid, e.g. 120 BPM = every 0.5 s. Cuts and key accents on the beats, even in a video without sound: you feel the rhythm in the picture.
- **Cues:** `cue(t, "impact")` at every event that should be heard. The template scales them by `SPEED`, and `render.mjs` writes `out/cues.json`. That's one source of timing for sound or subtitles.
- **A perfect loop:** the last frame should be the first one. Simplest: all motion is periodic (`sin`, scrolling by the full width of a pattern), and the video's length is a multiple of the period. For a loop with a story: the last scene ends exactly in the opening frame (same colour, shape, position).
- **Broken rhythm:** after a run of fast cuts on the beats, give a second of stillness or a freeze frame. Silence in the picture works as an accent.
- **Sound:** the model can't hear it. By default the video is silent. If the user wants sound, ideally they provide the track (licensed music) and you use `render.mjs --audio track.wav`. Make synthesised effects (clicks, noise, hits from `cues.json`) only on explicit request, at about -16 dBFS RMS with peaks at -1 dBFS, and always deliver a silent version too.

## 10. Formats

| Format | Size | Notes |
|---|---|---|
| 16:9 | 1920×1080 | showreel, YouTube, presentations, README |
| 9:16 | 1080×1920 | Reels, TikTok, Shorts. The app UI covers the top (about 250 px), the bottom (about 400 px) and a strip on the right (about 120 px): keep text and the logo in the middle |
| 1:1 | 1080×1080 | feed posts |
| 4:5 | 1080×1350 | Instagram feed, more vertical room than 1:1 |

Set the format for good in `W` and `H` in `index.html`; the `?w=…&h=…` parameter (`render.mjs --params "w=1080&h=1920"`) is only for a try-out, because if you forget it at render time you silently get a 16:9 video. Lay things out from `W`, `H`, `CX`, `CY` and `Math.min(W, H)`, not fixed pixels: then one composition yields several formats, and only the scenes that really need it get a separate layout.

60 fps is the default for UI motion and typography. 30 fps gives a smaller file, but fast moves lose smoothness. Motion blur: 5 subframes, shutter 0.5 (180°).
