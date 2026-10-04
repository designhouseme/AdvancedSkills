# The craft of motion

Read before building scenes. The concept says what to do; this file says how to do it properly: starting values and rules that separate designed motion from motion "out of the box".

## Starting values

| Element | Starting value |
|---|---|
| Text entrance | `outExpo` 0.7–0.8 s; letter stagger 40–50 ms, word stagger 50–70 ms; 5–9° rotation |
| Exit | `in3` 0.3–0.4 s, shorter than the entrance |
| Camera, moves | `io3` / `io4`; drift at most 1% of scale per second |
| Whip pan | `ioExpo` 0.6–0.7 s and directional blur proportional to speed (48 px cap) |
| Pops of small objects | spring f 2.4–3, z 0.35–0.5; stagger 60–80 ms |
| Accent | a 2.5% camera punch fading in 0.3 s and a ring spreading from the object |
| Motion and stillness | about 1/3 of a shot for motion, 2/3 for reading; constant motion is tiring and nothing can be read |
| Text size (1080 px tall) | headline 8–20% of the frame height; body at least 40 px, in 9:16 reels at least 48 px |
| Time on screen | at least words × 0.3 s + 1 s; one thought per shot, at most 7 words |
| First and last frame | the first already has content (thumbnail, autoplay); the end card stays 2–3 s |
| Motion blur | 5 subframes, shutter 0.5; 2 subframes give a double image; 8–10 for a large object turning fast |
| Texture | only when it belongs to the world: grain at 4–5% and a neutral vignette for film or print, flat for interfaces; no glow in the accent colour (`references/look.md`) |

## Rules

- **One main action at a time.** The background (drift, glow, grain) is quiet. When two things shout at once, you see neither.
- **Lead the eye.** New information appears where the eye already is, or the motion leads the eye to it (the dot falls where the zoom will be). Jumping across the whole frame at every cut is tiring.
- **A consistent direction.** Progress goes one way (usually right), exits the other; a whip pan goes the same way the content flows.
- **Moving objects don't pass through each other.** In the ReviewLink showreel the mark drove onto the incoming letters. Separate the starts, or shrink the object before it moves (scale on `outExpo`, position on `io4`). Cursors and pointers disappear during a big move and come back in the new place instead of flying through the text.
- **Depth from layers.** The background drifts more slowly than the foreground, and interface cards have long, soft shadows (e.g. `0 40px 80px -50px`). A blurred background with a sharp foreground gives depth without 3D.
- **Overshoot only on small objects.** A springy block of text or a whole scene looks like jelly.
- **Every transition has a reason:** a shared shape, colour, direction or continuity object. A dissolve without a reason is the last resort.
- **Premium is restraint:** one accent with one meaning, 1–1.5 px borders in the line colour, plenty of empty space. The brand's illustrations come in once and then only float slightly in place. Thin numerals and grain are a look, not a rule: use them when they fit the brand.
- **A circle from the first frame.** A rectangle turning into a circle (growing `border-radius`) looks cheap.
- **Elements outside the camera need their own exit.** A caption attached to the scene rather than the camera container stayed on screen during the zoom into the dot.

## Template motion and its replacements

A ban alone isn't enough: the model escapes to the next habit. Every pattern has a replacement.

| Pattern | Replacement |
|---|---|
| everything slides up from the bottom the same way | one entrance type per chapter, and at key moments a move from the concept (letters as windows, the shape of the mark) |
| springs on everything | springs only on small objects; text and scenes on `outExpo` / `io3` |
| particles, flares, glitch | motion that comes from the product's verb (`references/concept.md`, section 1) |
| a dot with a label above a heading ("● Price"), pills, eyebrows | the brand's mark (e.g. the squares from the logo) or nothing; the full list is in the ui-without-slop skill |
| a logo with a glow at the end | a logo assembled from its own shapes or from a motif that ran through the whole video |
| the usual look: the template's grey and Urbanist, Inter, a purple gradient, cream with a serif and terracotta, black with an acid accent | the brand's colours and font, or a palette and typeface decided with `references/look.md` |
| em dashes in on-screen text | a full stop, comma, colon or en dash |
