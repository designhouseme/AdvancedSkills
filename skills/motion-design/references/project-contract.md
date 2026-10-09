# Optional project timeline

Use a manifest when several scenes share cues or retiming would otherwise require editing multiple files. A simple standalone HTML composition still works without it. This v1 compiles timing metadata; it does not generate scene code, mix audio or migrate an existing composition.

## Source and generated files

Copy `assets/film.example.json` and, for a minimal demonstration, `assets/timeline-example.html` plus `assets/fonts/`. Keep your source manifest separate from generated output:

```bash
python3 scripts/compile_timeline.py --src film.json --out timeline.generated.json
python3 scripts/compile_timeline.py --src film.json --out timeline.generated.json --speed .75
```

When using scripts copied into the film folder, omit `scripts/`. Compile once for the intended speed, then use that exact file throughout:

```bash
node render.mjs --src index.html --timeline timeline.generated.json --preflight
node render.mjs --src index.html --timeline timeline.generated.json --check-frames
node render.mjs --src index.html --timeline timeline.generated.json --out film.mp4
python3 review_frames.py --film out/film.mp4 --timeline timeline.generated.json --outdir out/review
```

The source has exactly `version`, `fps`, `size` and `scenes`. Version 1 accepts positive integer fps only, not `30000/1001`. `size` contains positive integer `width` and `height`; the renderer's selected codec may impose further constraints. `assets/film.schema.json` describes allowed fields. The compiler additionally checks relationships between records and the resulting frame grid. Unknown fields, duplicate JSON keys, non-finite numbers and booleans in numeric fields are errors.

A scene has a stable `id`, positive `hold` in source seconds, optional outgoing `transition`, and optional local `cues`. IDs begin with an ASCII letter and contain letters, digits, hyphens or underscores. Omitting a transition means a hard cut. Explicit cuts have `duration: 0`; overlaps have positive duration. The final scene must omit `transition`. An overlap cannot outlast the next scene's hold: v1 deliberately supports at most two simultaneous scenes.

The exact, unrounded timing is:

```text
scene.start = sum(previous holds)
scene.holdEnd = scene.start + scene.hold
scene.end = scene.holdEnd + outgoing transition duration
next.start = scene.holdEnd
```

Ends are exclusive: scene `[start, end)`. The overlap extends the outgoing scene, without delaying the next one. This avoids accumulating transition durations into every later cue.

## Cues and references

A cue has a local `id` and exactly one of:

- `t`: non-negative seconds from its scene's start;
- `ref`: a global cue ID such as `detail.title`, with optional non-negative `offset` in seconds from that cue.

Global cue IDs are `sceneId.localId`; scenes and local IDs must be unique in their scope. References may point forward. Unknown targets and cycles are errors. A reference is resolved in film time, then checked against the scene containing the referencing cue. Deleting a target scene therefore exposes orphaned references instead of moving them silently.

Optional `d` is a positive window duration. It must fit inside the scene. Optional `text` and `source` are non-empty strings: display text and its provenance or an explicit illustrative label. These metadata do not prove a claim or automatically draw text; the composition must use them. Zero-duration cues omit `d` and represent an instantaneous event.

## One quantization step

The compiler parses decimal JSON numbers exactly, sums holds and resolves references before rounding. It divides all times by positive `speed`, multiplies by fps and rounds each absolute boundary to the nearest frame, ties upward. It derives durations from the rounded endpoints, never from a second independent duration rounding. A hold, overlap or cue window that collapses to zero frames is rejected. Cues rounding to an exclusive scene end are rejected.

`--speed .75` makes the film approximately 4/3 as long, subject to frame rounding. Recompile from `film.json`, not from an already generated timeline. No audio is stretched by this tool. Audio retiming remains a separate project decision.

## Generated contract

```text
{
  version: 1, fps, size: {width, height}, speed,
  duration, durationFrames,
  scenes: [{id, start, end, holdEnd, startFrame, endFrame, holdEndFrame,
            transition?: {type, duration}}],
  cuts: [seconds],
  cues: [{id, scene, t, d?, text?, source?}],
  source: {path, sha256}
}
```

All generated seconds come from integer frame / fps. Scene frame fields are authoritative if floating-point seconds need converting back to frames. `cuts` contains internal hard-cut times, not time zero, the film end or overlap boundaries. Cues are sorted by time and global ID. `source.path` is the absolute manifest path; `source.sha256` hashes the exact input bytes, not the HTML or final MP4. A QA report must separately identify the actual artifact it checked.

Writing is atomic: failed validation keeps the previous output intact. The output must not overwrite the source manifest.

## Composition integration

The renderer injects the parsed generated object as `window.__TIMELINE` before page initialization. The composition reads it and exposes the existing capture contract:

```js
window.__DURATION = window.__TIMELINE.duration;
window.__SIZE = {w: window.__TIMELINE.size.width, h: window.__TIMELINE.size.height};
window.__CUES = window.__TIMELINE.cues;
window.__CUTS = window.__TIMELINE.cuts;
// __ready resolves after assets are ready; __render(seconds) sets the complete state.
```

`assets/timeline-example.html` implements this without a network fetch. For browser preview, open the HTML and choose the compiled JSON using its local file picker. Capture mode instead requires injection. It demonstrates an overlap, a cut and timed Polish text; its neutral visual style and copy are examples to replace. Keep capture independent of the preview clock.

The sample hides text outside the declared cue windows, so its nearly uniform intervals produce frame-review warnings. Inspect those intervals; for a finished film, replace the sample timing with the actual reading windows and a meaningful first/last frame. This is a contract demonstration, not an approved storyboard.

When retiming, compile once and use that exact output for scene code, capture and review. Do not apply another speed change inside the composition to the already retimed data.
