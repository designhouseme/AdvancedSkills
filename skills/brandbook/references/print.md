# Colour per medium and print

Read when you set colour values, write the print section or prepare label templates. Values change with paper, press and printer, so every print value in the book carries its status, and anything not confirmed by the printer is labelled as such.

## Contents

1. [Four notations and a status](#1-four-notations-and-a-status)
2. [Which CMYK profile](#2-which-cmyk-profile)
3. [Converting without guessing](#3-converting-without-guessing)
4. [The print file](#4-the-print-file)
5. [Labels and packaging](#5-labels-and-packaging)
6. [Proof and handoff](#6-proof-and-handoff)

## 1. Four notations and a status

| Notation | For | Note |
|---|---|---|
| HEX, RGB | screens, the web, slides | the source of truth for digital |
| CMYK | four-colour print | only with the profile it was computed for |
| Pantone C / U | spot colour, or matching a print run | coated and uncoated look different; give both or say which |
| Foil, varnish, white | finishes | not a colour: a separate spot layer with a name agreed with the printer |

The CMYK `status`:

- `proposed`: chosen by eye or from a swatch book, not converted. Say "to confirm on a proof".
- `converted`: computed from the HEX through an ICC profile (section 3). Still not seen on paper.
- `proofed`: confirmed on a proof on the final paper; write the date and where in `date` and `source`.

Pantone is either given (with C and U) or a decision in `decisions[]` with a person and a date ("choose on the swatch book at the first print run"). "We'll sort it out with the printer" without a name is how values stay undecided for months.

## 2. Which CMYK profile

| Profile | Characterisation | Paper | Total ink |
|---|---|---|---|
| ISO Coated v2 | FOGRA39 | coated; still what many Polish printers ask for | 330% |
| PSO Coated v3 | FOGRA51 | coated, the successor of FOGRA39 | 300% |
| PSO Uncoated v3 | FOGRA52 | uncoated with optical brighteners | 300% |

Digital, large-format and UV printing often limit total ink lower (around 250%). When the printer isn't chosen yet, convert for the paper you expect (coated or uncoated), name the profile, and put "confirm the profile with the printer" in the decisions. The total-ink figures come from secondary sources; the printer's spec wins.

## 3. Converting without guessing

Never turn RGB into CMYK with the naive formula: the numbers look precise and print wrong. Use an ICC profile when a tool is installed:

```bash
# ImageMagick 7 with the profiles downloaded from the ECI (www.eci.org); prints e.g. cmyk(12%,72%,90%,3%)
magick -size 1x1 xc:"#B5502A" -profile sRGB.icc -profile PSOcoated_v3.icc -format "%[pixel:p{0,0}]\n" info:
```

LittleCMS (`transicc`) works too. Write the result with `status: "converted"` and the profile in `source`. Without a tool or profile, write the values from a swatch book with `status: "proposed"` and say so in the reply. Check the profile's licence before you ship it in a client package.

## 4. The print file

The brand book defines the print file; the designer makes it.

- PDF/X-4 (transparency stays live, ICC profiles are embedded); PDF/X-1a or X-3 only when the printer asks.
- Fonts embedded or outlined in production files only; the brand book's own PDF stays searchable.
- Small text and barcodes in 100% K, overprinting; large black areas in rich black (e.g. C40 M40 Y40 K100, or the value from the book); UV printing often wants pure 0/0/0/100.
- RGB converted to the target profile; Pantone kept as a spot colour only when it prints as a separate ink.
- Finishes on separate layers as spot colours, named exactly as the printer wants: commonly `Diecut`, `Varnish`, `Foil`, `White`. The dieline on top, the artwork below; a white underprint under foil and on clear labels.
- 300 ppi at final size; line art 1200 ppi.

## 5. Labels and packaging

- The dieline comes from the printer or converter, never drawn by eye. Until it arrives, the template's format is an assumption: say so in the decisions.
- Bleed: 3 mm is the offset default; label printers often want about 1.5–2 mm. Safe margin: keep text and logos at least as far from the cut as the printer requires (3 mm is a safe default).
- Keep barcodes and mandatory text inside the safe zone and away from folds. On a wrap-around label one end covers the other: ask the printer which end and by how much, and set `overlap_mm` and `overlap_side` so the template keeps content out of it.
- On a round pack the barcode bends with the surface; agree its orientation and position with the printer against GS1 guidance for curved surfaces.
- EAN-13: the number comes from the client's GS1 membership. Nominal size 37.29 × 25.93 mm at 100%; 80% (29.83 × 20.74 mm) is a common minimum. Keep the quiet zones; dark bars on a light background. Never generate a barcode image yourself: the template reserves the space and the designer or printer makes the code.
- Minimum line widths and type sizes for foil, embossing and spot UV depend on the converter: write "to confirm" instead of a number.
- The front hierarchy, as a numbered list: brand, product name or category, the main benefit, the variant marker (colour, number, illustration), the net quantity in the same field of vision as the name for food.
- A product line: write what stays (grid, logo position, type, material) and what changes (colour or illustration). Test: at the size of a shop thumbnail, the variants still look different.

## 6. Proof and handoff

Before a colour is approved: a proof on the final paper, under daylight-balanced light, next to the swatch book. After it: CMYK `proofed` with the date, Pantone filled in, the decision closed in `decisions[]`, the changelog updated.

Checklist for the print section of the book: the PDF standard and profile; bleed and safe margin; small text and barcode in 100% K; finishes and dieline on named spot layers; the dieline from the printer; the proof on the final paper.
