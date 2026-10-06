# brand.json, field by field

Read when you fill or change `brand.json`. Start from `assets/brand.example.json`, a fictional coffee roastery that uses every field. JSON has no comments, so the rules for each field are here. Paths in the file are relative to the folder that holds `brand.json`.

## Contents

1. [meta and sections](#1-meta-and-sections)
2. [strategy and voice](#2-strategy-and-voice)
3. [logo](#3-logo)
4. [colours and pairs](#4-colours-and-pairs)
5. [type](#5-type)
6. [imagery and applications](#6-imagery-and-applications)
7. [labels](#7-labels)
8. [print, files, decisions, references, changelog](#8-print-files-decisions-references-changelog)

## 1. meta and sections

- `meta.name`: the exact spelling. `name_confirmed`: true only after the user confirmed it.
- `meta.language`: `pl` or `en`, the language of the book's own labels ("Czytam jako", "Pobierz"). The content is in whatever language you write it.
- `meta.version`, `date` (YYYY-MM-DD), `owner` (who answers questions about the book), `contact`, `made_by`, `status` (`draft` or `approved`).
- `sections`: one headline per section, written as the rule the reader should remember. Keys: `strategy`, `voice`, `applications`, `logo`, `colour`, `type`, `imagery`, `labels`, `print`, `files`, `decisions`. A missing key falls back to the topic name, and `check_brand.py` warns.

## 2. strategy and voice

- `strategy.purpose`: one sentence, why the brand exists; it also goes on the cover.
- `audience`, `instead_of` (what the customer would use otherwise), `proof` (facts from the brief only), `values` (`value` + `behaviour`: what people do, not an adjective), `decision_rules` (2–3 for cases the book doesn't cover), `signature` (the one element that belongs only to this brand), `rejected` (default looks you rejected and what instead).
- `voice.traits`: pairs `is` / `is_not` ("plainly", "not dryly"). `tone`: per channel, `how` and a real `example`. `words_use`, `words_avoid`, `before_after`, `name_rule`.
- `voice.claims`: health or nutrition claims the brand may use, each with `register_ref` (the EU register entry). Without one, `check_brand.py` errors. Leave it empty rather than invent.

## 3. logo

- `variants[]`: `id`, `name`, `file` (SVG from the client, never redrawn), `use`, `min_px` (screen), `min_mm` (print), `on` (colour ids of backgrounds it may sit on). The first variant is the primary. A variant whose id contains `neg`, `white`, `light` or `inverse` is used on dark backgrounds when `on` doesn't decide.
- `clear_space`: `defined_as` (a part of the mark: "the height of the letter O") and `ratio` (its share of the logo height, used to draw the diagram). Never mm or px.
- `dont[]`: `rule` (a short imperative) and optional `demo`: `stretch`, `squeeze`, `rotate`, `shadow`, `recolor` or `busy`, drawn on the primary logo.
- `finish` (optional): `type` (`foil`, `emboss`, `none`), `min_line_mm`, `min_mm`.

## 4. colours and pairs

- `colours[]`: `id` (lowercase, used everywhere else), `name` (the brand's own name for it), `role` (`background`, `text`, `secondary-text`, `accent`, `line`, `support`), `hex`, `share` (percent of use), `cmyk` (`value` [c, m, y, k], `profile`, `status`, `source`, `date` when proofed), `pantone` (`c`, `u`, `status`).
- The book takes its own look from the roles: the first `background`, `text`, `secondary-text`, `line` and `accent`. So do `tokens.css` and the label text colour.
- `pairs[]`: text and background ids with their `use`. Name at least body text on the background. The book draws a contrast matrix of all text and background colours and outlines the declared pairs.

## 5. type

- `families[]` (one or two): `family` (the CSS name), `role` (`display`, `text`, `numerals`), `files` (paths, or objects `{file, weight, style}` for static weights; a plain path is treated as a variable font 100–900), `weights`, `licence`, `licence_file`, `source`, `why` (one sentence, this brand), `office_substitute` (a font available in Word, Google Docs and Canva), `reflex_reason` (only when the family is on the reflex list).
- `scale[]`: `level`, `role`, `px`, `pt`, `line`, `use`.
- `sample`: a sentence with the language's accented letters, shown in every face.

## 6. imagery and applications

- `imagery`: `light`, `composition`, `casting`, `props`, `styling`, `grading` (all six, each a rule a photographer can follow), `do[]`, `dont[]`, `images[]` (`file`, `alt`, `generated`, `caption`, `prompt`), `ai` (`allowed`, `banned`, `label`, `approver`).
- `applications[]`: `id`, `kind` (`post`, `card`, `email`, `web`), `title`, `headline`, `text`, optional `image`. The book draws each one at its real size from the tokens and places the logo at no less than its minimum, so a mockup can't break the book's own rule.

## 7. labels

- `id` (lowercase letters, digits, hyphens: it becomes the file name), `product`, `category` (`food`, `supplement`, `cosmetic`, `other`), `colour` (a colour id for the label field), `status` (`template`).
- `format`: `name`, `w_mm`, `h_mm` (trim size), `bleed_mm`, `safe_mm`, `largest_surface_cm2` (decides 1.2 or 0.9 mm x-height).
- `zones[]`: `id`, `role` (`front`, `info`, `legal`), `x_mm`, `w_mm`, laid left to right across the width (a wrap-around label: legal, front, info). One `front` zone carries everything when there is nothing else; then the net quantity sits under the name.
- `front`: `name`, `variant`, `benefit`, `net`. `info[]`: `label` + `text` (usage, origin, roast date). `legal[]`: `key` + `label` + `text`; the keys per category are in `references/labels-eu.md`.
- `nutrition_exempt_reason` when a food is exempt from the nutrition declaration (with the legal basis, to confirm).
- `barcode`: `ean` (13 digits from the client, or null) and `note`. The template draws a box with the size, never bars.
- `legal_pt`, optional `name_pt`, `variant_pt`, `net_pt`: type sizes in points. `render.mjs check` measures the real x-height of the mandatory text.

## 8. print, files, decisions, references, changelog

- `print`: `printer` (null until chosen), `technology`, `pdf`, `profile`, `bleed_mm`, `safe_mm`, `small_text`, `finishes[]` (`type`, `colour`, `layer`), `proof`.
- `files[]`: `path`, `what`, `print_ready` (true only for files a printer can use as they are).
- `decisions[]`: `what`, `who`, `by` (date), `recommendation`. Every open question gets your recommendation, so the client confirms or overrides instead of starting from nothing.
- `references[]`: `name`, `layer` (`structure`, `presentation`, `photography`), `borrow`, `not`. Internal: never shown in the book.
- `changelog[]`: `version`, `date`, `change`.
