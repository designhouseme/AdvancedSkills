# Label content in the EU (flag, don't advise)

Read when the brand has labels for food, supplements or cosmetics, and when you audit an existing label. This is a checklist for building templates and the verify list, not legal advice: the client's regulatory person approves every label, and national rules (language, notifications) weren't covered. Sources: Regulation (EU) 1169/2011, Directive 2002/46/EC, Regulation (EC) 1924/2006 with Regulation (EU) 432/2012, Regulation (EC) 1223/2009, Regulation (EU) 655/2013, Directive 2011/91/EU; checked October 2026.

## Contents

1. [Keys in brand.json](#1-keys-in-brandjson)
2. [Food](#2-food)
3. [Food supplements](#3-food-supplements)
4. [Cosmetics](#4-cosmetics)
5. [Claims](#5-claims)
6. [Legibility](#6-legibility)
7. [Auditing an existing label](#7-auditing-an-existing-label)

## 1. Keys in brand.json

`check_brand.py` and the book check these keys in `labels[].legal`. The name and the net quantity live in `front`.

| Category | Keys |
|---|---|
| `food` | `ingredients`, `best_before`, `storage`, `operator`, `lot`, plus `nutrition` or `nutrition_exempt_reason` |
| `supplement` | the food keys (no nutrition table) plus `nutrient_categories`, `daily_dose`, `dose_warning`, `diet_statement`, `children_warning`, `amounts_per_dose` |
| `cosmetic` | `responsible_person`, `nominal_content`, `durability_or_pao`, `precautions`, `batch`, `function`, `ingredients_inci` |
| `other` | none checked; say in `01-verify.md` which rules might apply (e.g. CLP pictograms on candles or cleaning products) and that nobody checked them |

Add keys for what applies to the product: `allergens` notes, `origin`, `alcohol`, `quid`, `warnings`. Instructions for use go into `info[]`; put them in `legal[]` under the key `usage` only when they're needed to use the food safely, because everything in `legal[]` is measured against the minimum x-height.

## 2. Food

Mandatory particulars (1169/2011, art. 9): the name of the food; the list of ingredients with allergens emphasised in it (bold, for example); the quantity of certain ingredients where the name or picture highlights them; the net quantity; the date of minimum durability or the "use by" date; special storage or use conditions; the name and address of the food business operator; the country of origin where required; instructions for use where needed; the alcohol content above 1.2%; the nutrition declaration. A lot number is required by Directive 2011/91/EU.

- **Same field of vision:** the name, the net quantity and (for drinks) the alcohol content (art. 13(5)). On the front, next to the name. On a round pack, flag it whenever the two sit in different zones and give the distance along the circumference; the regulatory person decides.
- **Net quantity figures** have a minimum height by quantity: 2 mm up to 50 g or ml, 3 mm up to 200, 4 mm up to 1000, 6 mm above (Directive 76/211/EEC, Annex I 3.1; in Poland the law on prepackaged goods). `render.mjs check` measures them; confirm the rule with the regulatory person.
- **Dates:** with the day: "Najlepiej spożyć przed: 12.05.2027"; with month and year only: "Najlepiej spożyć przed końcem: 05.2027" (Annex X). When the date depends on the packing day, the label may say where it is instead ("Najlepiej spożyć przed końcem: patrz dno puszki") with the date coded next to the lot; a date printed on the label goes out of date with every reprint.
- **Nutrition declaration exemptions** (Annex V) include single-ingredient unprocessed products, herbs and spices, whole or ground coffee beans, herbal and fruit infusions and tea, salt, and foods whose largest surface is under 25 cm². Write the exemption and its basis in `nutrition_exempt_reason` and flag it for confirmation.
- **Language:** the particulars must be in a language consumers understand; in Poland, Polish.
- **Organic terms:** "eko", "bio", "ekologiczny" and "organic" are reserved for certified products (Regulation (EU) 2018/848); keep them out of names, labels and posts without a certificate.

## 3. Food supplements

On top of the food rules (Directive 2002/46/EC, art. 6 and 8): the names of the categories of nutrients or substances that characterise the product; the recommended daily portion; a warning not to exceed it; a statement that supplements are not a substitute for a varied diet; a statement to store them out of reach of young children; the amounts of nutrients per daily portion, with the percentage of the reference intake for vitamins and minerals. The product may not claim to prevent, treat or cure a disease. In Poland a supplement is notified before it goes on sale; that's the client's job, but ask whether it has been done.

## 4. Cosmetics

Regulation (EC) 1223/2009, art. 19: the name and address of the responsible person; the nominal content by weight or volume; the date of minimum durability when durability is 30 months or less, otherwise the period after opening (the open-jar symbol with months); particular precautions; the batch number; the function unless it is clear from the presentation; the ingredients in INCI names in descending order. Claims must meet the six common criteria of Regulation (EU) 655/2013: legal compliance, truthfulness, evidential support, honesty, fairness, informed decision-making.

## 5. Claims

- A health or nutrition claim on food is allowed only in the wording of the EU register (Regulation 1924/2006, list in Regulation 432/2012) and only when the product meets its conditions. In `brand.json` every claim has `register_ref`; without it `check_brand.py` errors.
- Claims about plants (botanicals) are "on hold" at EU level: none is authorised, and whether one may be used under the transitional rules is the regulatory person's call. Never write one into a label or the voice section yourself; flag it.
- The voice section lists banned words (treats, cures, prevents, detox, "before and after", "approved by…").
- The same claim rules apply to every commercial message, not only the label: posts, the website, a newsletter, a stand at a fair. Say so in the voice section, because posts are often written by someone who never sees the label.
- Never generate a nutrition or supplement facts panel in an image: keep the approved label artwork.

## 6. Legibility

Mandatory food particulars need an x-height of at least 1.2 mm, or 0.9 mm when the largest surface of the pack is under 80 cm² (1169/2011, art. 13 and Annex IV; the European Commission's Q&A on the regulation explains the surface). The x-height depends on the typeface, so it is measured, not assumed from points: `render.mjs check` measures each mandatory line and tells you the minimum `legal_pt` for the face you use.

When the mandatory text doesn't fit at that size, don't shrink it. Options, in this order: a larger or different format (a wider label, a peel-off or booklet label), a narrower typeface for the small print that still has the language's letters, cutting optional text (stories, slogans, repeated claims).

## 7. Auditing an existing label

Compare the label with the product data and with sections 2–6, and write each finding into `01-verify.md` with where it is, why it matters and who decides:

- the spelling of the brand and product name against the brief, the data and the logo;
- composition and amounts against the latest product sheet; percentages recomputed from the amounts where they can be (a reference intake can be recalculated, so a wrong one is a finding);
- missing mandatory particulars for the category;
- the net quantity in the same field of vision as the name;
- the date form, the lot number, the operator's address;
- claims without a register entry, or claims about plants;
- the measured x-height of the small print against 1.2 or 0.9 mm (measure from a vector file or a scan at a known scale, give the tolerance).

- on a wrap-around label, mandatory text inside the overlap, where the other end covers it.

Show an existing label in the book only as an example of layout, with the words "layout only, content to be corrected" next to it, until those findings are resolved.

**When the question is only "is this label OK, can we print it?"**, don't build a brand book. Measure the label (`render.mjs measure`), go through the list above, and answer in this order: no verdict, and who decides; what doesn't match the client's own data or measurement (these need fixing whatever the legal reading); the legal flags for the regulatory person; reprinting this file and selling stock already printed as two separate decisions; the questions you need answered; what you didn't check. Keep the findings in `brand/01-verify.md`.
