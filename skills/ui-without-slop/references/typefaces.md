# Typefaces

Read before you write the typefaces into the decision (the rules in SKILL.md), and whenever you choose, change or review a font. Left alone, a model picks the family it has seen most often, and after a ban it moves to the next most-seen one. That's why this file gives a method and sources, not a list of good fonts: any list of recommendations would become the next default.

## Contents

1. [The reflex list](#1-the-reflex-list)
2. [Method](#2-method)
3. [Where to look](#3-where-to-look)
4. [Checks before you commit](#4-checks-before-you-commit)
5. [Using the typeface well](#5-using-the-typeface-well)

## 1. The reflex list

These are good typefaces. They're here because models reach for them without a reason, so on screen they read as "nobody decided". Keep one when it's the brand's font or the user chose it, and say so.

- **The defaults:** Inter, Roboto, Open Sans, Lato, Montserrat, Poppins, Nunito, Raleway, Work Sans.
- **The "modern" swaps:** Geist, Space Grotesk, DM Sans, Manrope, Plus Jakarta Sans, Outfit, Sora, Urbanist, Figtree, Lexend.
- **The "designer" swaps:** Satoshi, General Sans, Cabinet Grotesk, Clash Display, Bricolage Grotesque, Syne, Unbounded, PP Neue Montreal, and Bebas Neue, Anton or Oswald for big headings.
- **Serifs:** Fraunces, Instrument Serif, Playfair Display, Cormorant, DM Serif Display, Lora, PP Editorial New, often with one word in italics.
- **Mono as a costume:** JetBrains Mono, IBM Plex Mono, Space Mono, Geist Mono, Fira Code for labels on a site with no code on it.

An unstyled system stack on a brand site is no decision either. In a product UI it can be a good one (section 2).

## 2. Method

1. **Describe the voice with things, not adjectives.** "Modern, clean, professional" leads straight back to Inter. Name where letters live in the company's world: stamped tool tags in a workshop, a 1970s pharmacy label, municipal signage, a printed menu, a ledger, an engineering drawing. One or two such references per project.
2. **Choose the genre from the voice** before any family name: grotesque with quirks, neo-grotesque, humanist sans, geometric, square or technical sans, wide or condensed, slab, wedge or glyphic serif, old-style, transitional, high contrast, stencil, rounded. A genre written down first keeps the choice from sliding to whatever comes to mind.
3. **Make a shortlist of 4–6 families from at least two sources** in section 3, none from section 1. Prefer families you couldn't have named before searching. For a site in a language other than English, also look at designers from that language's region: they draw its accents with care.
4. **Run the checks in section 4** on the shortlist. Most candidates drop out here, usually on accented letters or missing weights.
5. **Choose and write it down:** the family, its role (display, text, numerals), one sentence on why it fits this subject, the source, the licence, the accented letters checked. Then the swap test: would another model given the same brief land on the same family? If so, choose again, or let the signature live in the composition.

**Pairing.** One family is often enough when it has range (widths, optical sizes, a real italic). Two families should differ in structure, e.g. a wedge serif for headings and a humanist sans for text, not only in weight; two similar geometric sans look like a mistake. Never three.

**Product UI.** In an app or a dashboard, readability at 13–15 px, tabular numerals and a fast load matter more than character. A system stack or a workhorse sans is fine there, with the reason written down. The character goes on the brand surfaces: the marketing site, onboarding, empty states.

## 3. Where to look

Go past the first screen of every catalogue: its most popular entries are the next reflex. Fontshare's front page (Satoshi, General Sans, Clash Display, Cabinet Grotesk) is already in section 1.

| Source | What it is | Licence |
|---|---|---|
| Google Fonts, filtered by the site's language and not sorted by popularity | the largest free library | OFL or Apache, free for commercial use |
| Fontsource (fontsource.org) | open-source fonts packaged for self-hosting | the font's own, mostly OFL |
| Velvetyne (velvetyne.fr) | French libre foundry, expressive display faces | OFL |
| Collletttivo (collletttivo.it) | Italian open-source foundry | OFL |
| Use & Modify (usemodify.com) | a curated catalogue of open-source typefaces | per font (OFL, MIT, Creative Commons, GPL and others); check each one |
| Uncut (uncut.wtf) | a curated catalogue of free typefaces by independent designers | per font; check each one |
| Fontshare (fontshare.com) | free fonts from the Indian Type Foundry | ITF Free Font License: commercial use allowed, but it isn't OFL; read its terms before committing the files to a public repository |
| commercial foundries, e.g. Klim, Grilli Type, Dinamo, Commercial Type, Colophon | the widest choice when the client has a budget | a paid web licence, usually priced by traffic |

Pangram Pangram's free downloads are for personal use only. A company site needs a paid licence.

## 4. Checks before you commit

- **Accented letters, in every weight you use.** Render a test line in the site's language at the real sizes: for Polish "Zażółć gęślą jaźń ĄĆĘŁŃÓŚŹŻ", for German "Größe Übermaß", for Czech "Příliš žluťoučký kůň". A missing glyph silently falls back to another font. Look at the shapes too: ogoneks (ą, ę) attached to the letter, the stroke of Ł not colliding, accents not clipped by the line above.
- **The weights and styles the layout needs:** at least regular and bold for the text face, a real italic if the copy has emphasis, tabular numerals if there are prices, tables or a timetable.
- **A licence that covers a company website.** OFL and Apache fonts can be self-hosted and committed; ITF and commercial fonts as their terms say; "free for personal use" is not free for a business. Put the licence in the output.
- **Weight on the wire:** WOFF2, subset to the languages used (latin plus latin-ext for Polish), at most two families and four files above the fold, the H1's font preloaded.
- **Self-hosted**, or loaded at build time (e.g. `next/font`, which serves the files from your own domain). Don't load fonts from Google's servers at runtime on a site for EU visitors: a Munich court ruled in 2022 that this passes visitors' IP addresses to Google without consent.
- **A fallback that doesn't jump:** `font-display: swap` and a fallback with matched metrics (`size-adjust`, `ascent-override`, or `next/font`'s automatic fallback), so the swap doesn't shift the layout.

## 5. Using the typeface well

A good family at its defaults still looks generic. Use what it offers:

- contrast between roles in weight and width, not only in size;
- optical sizes (`font-optical-sizing: auto`) or the display cut for large headings;
- stylistic sets and alternates when they carry the voice (`font-feature-settings: "ss01"`), checked on the real copy;
- real small caps (`font-variant-caps: all-small-caps`), or no label at all, instead of UPPERCASE with letter-spacing;
- tight tracking only at display sizes, body text at the font's own spacing;
- `font-variant-numeric: tabular-nums` in prices and tables, old-style numerals in running text if the family has them.

Don't let the browser fake a weight or an italic the family doesn't have: `font-synthesis: none` shows where it does.
