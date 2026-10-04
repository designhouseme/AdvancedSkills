# Look: colour and type

Read in step 2, before the three directions, and again in step 4, before you fill in `:root` and `@font-face`. Left alone, a model picks the palette and typeface it has seen most often, and the video looks generated before anything moves. The rules come from the ui-without-slop skill and are adapted here to video.

## Contents

1. [Where colours and type come from](#1-where-colours-and-type-come-from)
2. [The decision](#2-the-decision)
3. [Colour: patterns and replacements](#3-colour-patterns-and-replacements)
4. [Type: patterns and replacements](#4-type-patterns-and-replacements)
5. [The second wave](#5-the-second-wave)
6. [Fonts offline](#6-fonts-offline)
7. [Check](#7-check)

## 1. Where colours and type come from

In this order:

1. **The brand's files:** CSS tokens, the logo SVG, a brand book, the font files the site uses. Take exact values, not values eyeballed from a screenshot.
2. **The brief:** colours and fonts the user names.
3. **Your decision**, only when 1 and 2 give nothing. Record it as an assumption.

The user and the brand take precedence. A purple brand, a café that really is cream and serif, or a font the brand already uses isn't slop: keep it and do it well. The template's grey palette and Urbanist are placeholders so the demo renders, never a fallback style.

## 2. The decision

Before the first scene, write down in the concept:

- three default looks you reject for this project, each with what you do instead;
- the palette as named values with roles, one for each `:root` token (background, ink, secondary ink, line, accent); the accent has one meaning and takes at most about a tenth of the frame (a single small accent is fine);
- the typeface with its roles (display, text, numerals) and one sentence on why it fits this subject; at most two clearly different families;
- where the signature lives if the colours are the obvious ones for the subject.

Each of the three directions in `references/concept.md` names its own palette and typeface. Directions that differ only in colour are one direction.

## 3. Colour: patterns and replacements

A ban alone pushes the model to the next fixed palette, so every pattern has a replacement.

| Pattern | Instead |
|---|---|
| purple → blue gradient, indigo as the main colour | one solid accent from the brand's world; neutrals slightly tinted in the same hue |
| dark background with a neon glow, a glowing logo at the end | solid colour fields and contrast; light as a motif only when it belongs to the product (a lamp, a screen, a sunrise) |
| gradient text | a solid colour; emphasis through weight, size or motion |
| glassmorphism, frosted cards (`backdrop-filter`) | solid surfaces separated by tone; blur on a large area also slows every frame |
| a slowly circling glow in the accent colour behind everything | a flat background, or light in the background's own hue |
| a different accent in every scene | one accent with one meaning; the whole frame may change colour once or twice per video, as a chapter change |
| the subject's obvious colour as the whole idea (coffee → brown, eco → green, finance → navy) | keep it when it's the brand, and put the signature in the composition, the type or the motion |

## 4. Type: patterns and replacements

| Pattern | Instead |
|---|---|
| a family from the reflex list below | a typeface chosen by the method below, with the reason written down |
| thin weights (100–300) everywhere as the "premium" look | weight by role: thin only at large sizes (roughly 150 px and up in a 1080 px frame); text under 60 px at 400 or heavier, because x264 at the size limit and WebP at 800 px eat thin strokes |
| a serif headline with one word in italics | emphasis from motion, weight or colour; italics only when the typeface's italic is the point |
| UPPERCASE letter-spaced labels above every line; mono labels as a "technical" costume | no label, or the brand's own mark; mono only for real code or data |
| a typewriter font or a script font to add "warmth" | the brand's real lettering, or a text face with character |
| flat text: every line at the same weight and a similar size, centred in the frame | rank the words, then 2–3 levels that jump in size and weight, one sentence split by meaning into a lockup (the ui-without-slop skill, `references/text-hierarchy.md`); the word ranked first also gets the strongest entrance; set each level with its own `wordRow()` (`references/techniques.md`) |

**The reflex list** (the same as in the ui-without-slop skill, `references/typefaces.md`). Good typefaces that models reach for without a reason, so on screen they read as "nobody decided". Keep one when it's the brand's font or the user chose it, and say so.

- the defaults: Inter, Roboto, Open Sans, Lato, Montserrat, Poppins, Nunito, Raleway, Work Sans;
- the "modern" swaps: Geist, Space Grotesk, DM Sans, Manrope, Plus Jakarta Sans, Outfit, Sora, Urbanist, Figtree, Lexend;
- the "designer" swaps: Satoshi, General Sans, Cabinet Grotesk, Clash Display, Bricolage Grotesque, Syne, Unbounded, PP Neue Montreal, and Bebas Neue, Anton or Oswald for big headings;
- serifs: Fraunces, Instrument Serif, Playfair Display, Cormorant, DM Serif Display, Lora, PP Editorial New, often with one word in italics;
- mono as a costume: JetBrains Mono, IBM Plex Mono, Space Mono, Geist Mono, Fira Code.

**Method.**

1. Describe the voice with things, not adjectives: where letters live in the subject's world (the stamp on a kiln shelf, a café's chalkboard, a ledger, municipal signage). "Modern, clean" leads straight back to Inter.
2. Choose the genre before any family name: grotesque with quirks, humanist sans, geometric, square or technical sans, wide or condensed, slab, wedge serif, old-style, high contrast, stencil, rounded.
3. Make a shortlist of 3–5 families, none from the reflex list: the installed fonts first (section 6), then sources sorted by anything but popularity (Google Fonts filtered by the language, Velvetyne, Collletttivo, Use & Modify, Uncut).
4. Check each on a specimen: the accented letters of the language in every weight you use, the weights themselves, a real italic if you need one.
5. Write down the family, its role, one sentence on why it fits this subject, and the licence; then the swap test.

## 5. The second wave

After a ban, the model escapes to the next template: a cream or beige background with a serif (often one word in italics) and a terracotta accent; an almost black background with a single acid accent; mono labels as a "technical" costume; hairline rules like in a newspaper; "·" separators; 01/02/03 numbering without a real sequence. These are reflexes too. When the project drifts there on its own, go back to the decision in section 2 and write down specific values. When the brand itself looks like this, keep it (section 1).

## 6. Fonts offline

The render runs without the internet, so the font has to be a local file in `fonts/`:

1. the brand's font files (from the site's repository or from the user);
2. fonts installed on the system: `fc-list : family file | sort` on Linux; on macOS also `/System/Library/Fonts`, `/Library/Fonts` and `~/Library/Fonts`;
3. when nothing fits, propose 2–3 typefaces with reasons and ask the user for the files or for permission to download them. When the user isn't at the keyboard, take the best installed font whose licence allows it and list the alternatives in the reply.

A static family (one file per weight) has only the weights its `@font-face` blocks declare, and the browser fakes the rest. Declare each weight you use and set `WT` in the template to them; the template warns in the console about a weight a scene asks for but nothing declares.

To choose, set the name and a line in 3–5 candidates on one specimen (a single `chromium --headless --screenshot` of an HTML page) and compare them side by side.

Copy the licence with the font. OFL and Apache fonts can go into the repository. Fonts from a Linux distribution come under their own licences (OFL, Apache, or GPL and AGPL with a font exception): read it in the package (`pacman -Qi`, `dpkg -s`, `rpm -qi`), copy its text, and leave GPL and AGPL fonts out of the repository unless the user agrees. Fonts that come with macOS or Windows can be used for a local render, but not committed or redistributed; say so in the reply. Never link Google Fonts from the composition: `check_film.py` reports resources from the internet as an error. After the swap, look at a still with accented letters, because a missing glyph falls back to another font without a warning.

## 7. Check

- `check_film.py --composition` warns about the template's demo palette and font, default typefaces, gradient text, `backdrop-filter`, the default purples and emoji. Fix each one or say in the reply why it stays (e.g. it's the brand's font).
- **Swap test for the look:** would another model pick the same palette and typeface from this brief? If so, change one of them, or make the signature carry the video.
- **"AI made this" test** on the contact sheet: would someone say at a glance that it's generated? Point to the element and use the tables above.
