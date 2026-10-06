# Choosing the typefaces

Read at the direction stop, before you write `type.families`, and whenever a typeface changes. Left alone, a model picks the family it has seen most often, and after a ban it moves to the next most-seen one. So this file gives a method and sources, not a list of good fonts: a list of recommendations would become the next default.

## Contents

1. [The reflex list](#1-the-reflex-list)
2. [Method](#2-method)
3. [Where to look](#3-where-to-look)
4. [Checks before the book](#4-checks-before-the-book)

## 1. The reflex list

These are good typefaces. They're here because models reach for them without a reason, so in a brand they read as "nobody decided". `check_brand.py` warns on each one unless `reflex_reason` says why it stays (it's the client's font, or the user chose it after seeing alternatives).

- **The defaults:** Inter, Roboto, Open Sans, Lato, Montserrat, Poppins, Nunito, Raleway, Work Sans.
- **The "modern" swaps:** Geist, Space Grotesk, DM Sans, Manrope, Plus Jakarta Sans, Outfit, Sora, Urbanist, Figtree, Lexend.
- **The "designer" swaps:** Satoshi, General Sans, Cabinet Grotesk, Clash Display, Bricolage Grotesque, Syne, Unbounded, PP Neue Montreal, and Bebas Neue, Anton or Oswald for big headings.
- **Serifs:** Fraunces, Instrument Serif, Playfair Display, Cormorant, DM Serif Display, Lora, PP Editorial New, often with one word in italics.
- **Mono as a costume:** JetBrains Mono, IBM Plex Mono, Space Mono, Geist Mono, Fira Code.

## 2. Method

1. **Describe the voice with things, not adjectives.** "Modern, clean, natural" leads straight back to the list above. Name where letters live in the brand's world: a stencil on a sack, a 1970s pharmacy label, a market chalkboard, a seed packet, an engineering drawing. One or two such references per brand.
2. **Choose the genre from the voice** before any family name: grotesque with quirks, neo-grotesque, humanist sans, geometric, technical sans, wide or condensed, slab, wedge or glyphic serif, old-style, transitional, high contrast, stencil, rounded.
3. **Make a shortlist of 4–6 families from at least two sources** in section 3, none from section 1. Prefer families you couldn't have named before searching, and for a brand in a language other than English, designers from that language's region: they draw its accents with care.
4. **Run the checks in section 4.** Most candidates drop out on accented letters, missing weights or the licence.
5. **Write it down in `type.families`:** the role (display, text, numerals), `why` (one sentence about this brand, not about the font), `source`, `licence` and `licence_file`, `office_substitute`. Then the swap test: would another model given the same brief land on the same family? If so, choose again, or let the signature live in the layout and the colour.

**Pairing.** One family is often enough when it has range (widths, a real italic, optical sizes). Two families differ in structure, e.g. a wedge serif for names and a humanist sans for the small print, not only in weight; two similar sans look like a mistake. Never three.

**Small print decides.** On a label the text face carries the mandatory particulars at the legal x-height (`references/labels-eu.md`, section 6). A face with a large x-height and open shapes fits more text at the minimum; measure it with `render.mjs check` before you commit.

## 3. Where to look

Go past the first screen of every catalogue: its most popular entries are the next reflex.

| Source | What it is | Licence |
|---|---|---|
| Google Fonts, filtered by the brand's language, not sorted by popularity | the largest free library | OFL or Apache: print, packaging, web and embedding allowed |
| Fontsource (fontsource.org) | open-source fonts packaged for self-hosting | the font's own, mostly OFL |
| Velvetyne (velvetyne.fr) | French libre foundry, expressive display faces | OFL |
| Collletttivo (collletttivo.it) | Italian open-source foundry | OFL |
| Use & Modify (usemodify.com), Uncut (uncut.wtf) | curated catalogues of free typefaces | per font; check each one |
| Fontshare (fontshare.com) | free fonts from the Indian Type Foundry | ITF Free Font License, not OFL: read its terms for packaging and redistribution |
| commercial foundries, e.g. Klim, Grilli Type, Dinamo, Commercial Type, Colophon | the widest choice when the client has a budget | separate desktop (print, packaging), web and app licences |

"Free for personal use" is not free for a brand, and Pangram Pangram's free downloads are personal only.

## 4. Checks before the book

- **The language's letters in every weight used.** `render.mjs check` measures each face against two fallbacks and errors on a missing glyph; `check_brand.py` reads the font files for the Polish letters. Look at the shapes too: ogoneks attached to ą and ę, the stroke of Ł clear, accents not clipped by the line above.
- **The weights the system needs:** a regular and a bold for the text face, a real italic if the copy uses emphasis, tabular figures if the labels carry tables or amounts.
- **A licence for every use the book defines:** desktop for print and packaging (the designer and the printer get the files), web for the site, embedding in PDFs. Keep the licence file next to the fonts (`licence_file`); a commercial licence often doesn't allow handing the font files to a printer, so write who holds it in `decisions[]`.
- **An office substitute** that people outside the studio have (Word, Google Docs, Canva), with the same genre, so a price list or a newsletter written in-house still looks related.
- **The files in `fonts/`** under the brand's folder, in the formats the licence allows; the book and `tokens.css` point at them, so the book opens without a network as long as the folder travels whole.
