# Text hierarchy

Read before you set a headline, a hero or any block of text, and when text looks "flat": every word at the same weight, every line centred, the heading barely bigger than the line under it. The typeface is only half of it. A reflex font set with a clear hierarchy can look designed, and a well-chosen font set flat still looks generated. Swapping the font fixes nothing by itself.

## Contents

1. [Method](#1-method)
2. [A lockup is not an eyebrow](#2-a-lockup-is-not-an-eyebrow)
3. [Display settings](#3-display-settings)
4. [On the web](#4-on-the-web)
5. [Check](#5-check)

## 1. Method

1. **Rank the words before you set them.** Write down what is read first (one word or a short phrase), second and third. Usually one word carries the meaning and the rest are function words or context. If everything has the same rank, the eye has no way in.
2. **Split the sentence by meaning, not by line width.** "Stop using / Poppins": the word that carries the point gets the size, the words around it stay small. Line breaks follow the sense; never let the width break a key phrase or leave one short word on a line of its own.
3. **Make jumps, not nudges.** By default levels differ in size and weight together. In a long sentence, weight alone can carry the emphasis; size alone rarely does. Diagnostic, not a target: if level 1 is less than about twice the size of level 2 and in the same weight, it reads flat. Two or three levels in one composition; with more, it goes flat again.
4. **Lock the pieces together.** The levels share edges and sit close: small text aligns to the edge of a letter's stem (optically, not to the text box), a short line can sit in the empty space beside a descender or under the end of the big word, and the gaps inside the lockup are smaller than the gap to anything else. The lockup reads as one shape.
5. **Push everything else away and make it quiet.** Body copy, contact details and small print go smaller and further away, so the empty space separates the groups. The composition has one loud thing.

**The shape comes from the sentence.** A giant black word with a small line tucked under it is itself a template on Behance and Instagram; repeated in every hero, it becomes the next reflex. Which word gets the size, how many words there are and how long they are in this language decide the shape, so it differs from project to project. Sometimes the right lockup is two equal lines in different weights, sometimes a long sentence with one word in a heavier weight.

## 2. A lockup is not an eyebrow

The small part above a big word looks like the eyebrow that SKILL.md bans. The difference:

- **a lockup** splits one sentence by importance; the small part is read as part of the headline ("Stop using" + "Poppins"), and the whole sentence is one heading;
- **an eyebrow** is a separate label that repeats the heading's category ("SERVICES" above "Our services"), usually in UPPERCASE with letter-spacing.

Test: read the small part and the big part together as one sentence. If it works, it's a lockup. If it's a category name followed by the heading, it's an eyebrow: remove it.

## 3. Display settings

- **Leading:** about 0.85–1.0 for large headings, 1.4–1.6 for body text. Large type at body leading falls apart into separate lines. With tight leading, check the language's accented capitals on the second line (Ś, Ż, Ź under a p, g or ę), not only the sample word.
- **Tracking:** slightly negative at display sizes (about −0.01 to −0.04 em, by eye on the real word), the font's own spacing at text sizes, never letter-spacing on running text.
- **Kerning:** at display sizes, look at the pairs in the real word (e.g. "Ty", "Wo", "ł" next to round letters); `font-kerning: normal` and a manual tweak where needed.
- **Alignment:** align the lockup to its own axis, usually a left letter edge, instead of centring every line on the page; centred lines of different lengths make a ragged outline. The lockup as a whole may sit where the composition needs it.
- **One family is often enough** when it has a wide weight range: the levels then differ in size and weight, not in typeface.

## 4. On the web

The reference images are posters; a website has to survive every width, a screen reader and real content.

- **One heading in the markup.** The whole sentence is one `h1` (or `h2`) with a `span` per level, displayed as blocks, so a screen reader reads "Stop using Poppins". No chains of `<br>`, no separate elements for the pieces of one sentence.
- **Never text as an image or as SVG outlines.** It can't be read, translated or found.
- **Fluid sizes** with `clamp()`, and a cap tied to the width (`min(…vw, …rem)`) so the big word always fits the screen.
- **Place the tucked line with grid**, overlapping grid areas rather than `position: absolute` with pixel offsets that break at the next width.
- **Design the mobile lockup separately.** At 375 px the tucked line often has to move below the big word. Test with the longest real word in the site's language: Polish and German words run long ("Zabezpieczenia", "Rechtsanwaltskanzlei"). Use `hyphens: manual` with `&shy;` only where a break is acceptable, and `text-wrap: balance` for multi-line headings.
- **Check 375, 768 and 1440 px.** A lockup that works on the extremes often collides at tablet widths.

## 5. Check

- **Squint test** (point 4 of SKILL.md): one point of focus, which is the word ranked first.
- **Read-order test:** someone who sees the composition for a second reads the words in the order you ranked them.
- **Sentence test:** the levels together read as one sentence with the right emphasis; the eyebrow test from section 2 passes.
- **Width test:** no overflow and no single-word line at 375 px with the longest real copy.
