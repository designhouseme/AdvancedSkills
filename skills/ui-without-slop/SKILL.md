---
name: ui-without-slop
description: Removes and prevents the typical look of AI-generated interfaces, that is decorative dots in buttons, tags and menus, pills above headings, eyebrows, gradient text, purple gradients, glassmorphism, emoji instead of icons, identical cards, flat type with no hierarchy, and the stock kit of Inter-like fonts, Lucide icons and untouched shadcn/ui or Magic UI components. Replaces each pattern with a design decision, including how to choose a typeface, icons and a component look. Use when these need to be removed from or prevented in an existing or in-progress UI (website, component, dashboard), when someone wants a less obvious font, icons other than Lucide or components that don't look like shadcn, and when someone says the UI "looks AI-generated", "looks like Claude made it", "looks generic", "looks like every shadcn site", has "dots everywhere", too many badges or a flat headline. Building a site from a plan is website-build, and a full review is website-review.
license: CC-BY-4.0
metadata:
  author: Design House
  version: "1.3"
---

# UI without slop

Models generate what they've seen most often: safe, averaged patterns from Tailwind and shadcn templates. A ban alone isn't enough. According to Anthropic's documentation, general instructions like "don't use cream" push the model to *a different* fixed palette instead of producing variety. That's why every ban here comes with a replacement, and the work starts with a decision, not with a list of bans.

## Rules that always apply

- **A decoration must carry information.** A dot, pill, number, label or icon is fine only when it says something true about the content or a state. A dot with no state behind it is noise pretending to be data.
- **Every ban comes with a replacement.** Don't swap one template for another. A cream background with a serif and terracotta, mono labels, "A · B · C" separators and 01/02/03 numbering are the second wave of the same reflexes (point 3).
- **Decision first.** Before building, write down three defaults you're rejecting in this project and one signature element that belongs only to this brand. Then colours as 4–6 named values, typefaces with roles (headings, body) chosen as in `references/typefaces.md`, the reading order of the main headings (`references/text-hierarchy.md`), the icons (none, or which set and why: `references/icons.md`), the component look if the project uses a kit (`references/components.md`), corner radius and density.
- **When neither the brief nor the brand gives a direction**, propose 3–4 clearly different directions (background, accent, typeface and a one-sentence rationale), choose one and build only that. According to Anthropic's documentation, this breaks the default style better than bans alone.
- **The user and the brand take precedence.** A real live status, a purple brand, the brand's own font or a deliberately chosen style isn't slop. Keep it and do it well. In an internal tool or an admin panel, a stock component kit, a system font and Lucide for utility icons (close, chevron, search) are legitimate choices; the bar is higher on public brand pages.
- **The content belongs to the user.** Change wording (em dashes, ad slogans, content order) only when you're allowed to touch the content. When you're not, list them in the output as decisions to make.

## 1. Dots: variant → what to do

General rule: **if a dot needs explaining, a text label was the right choice. If nothing changes state, remove the dot.**

| variant | what to do instead |
|---|---|
| dot in a button before the label | remove it; the button says with a verb what will happen ("Book a measurement") |
| coloured dot in a tag, badge or pill | remove it; if the tag carries a state, the word is enough ("Slots available"); background colour only for a few real states |
| pulsing "live", "online", "active" dot | only for genuinely live data; static, with a label; motion only at the moment the state changes |
| dot before a menu item or active link | show the active state with an underline, weight or text colour |
| "A · B · C" separators in metadata and slogan bars | choose a hierarchy: one thing important, the rest on a second line or removed; at most one "·" per line |
| dots or emoji as list bullets | a plain list; icons from one set only when they distinguish meaning |
| fake system metadata ("last sync 4s ago", "v0.6.2", "Build 0048", "BETA") | remove it; never invent a state the product doesn't have |
| pagination dots under a carousel of three reviews | one strong review or a list without a carousel |
| browser window "traffic lights" in a mockup made of divs | a real product screenshot or nothing |

## 2. Other patterns (most frequently cited first)

| pattern | what to do instead |
|---|---|
| purple → blue gradient, indigo as the default primary colour | one solid accent from the brand's world (about 10% of the surface), neutrals slightly tinted in the same hue |
| three identical cards: icon in a coloured square, title, sentence | the layout follows the content (list, two columns, asymmetry); icon next to the heading; a card only for a clickable element or real hierarchy |
| Inter everywhere and the fonts models swap in for it (Space Grotesk, Geist, Satoshi, Fraunces, Instrument Serif; the full list is in `references/typefaces.md`) | a typeface chosen for the subject by the method in `references/typefaces.md`: 1–2 structurally different families, weight contrast rather than size alone, the language's accented letters checked |
| flat text: one weight, every line centred, the H1 barely bigger than the line under it, every word given the same rank | rank the words first; 2–3 levels that jump in size and weight together; one sentence split by meaning into a lockup in a single `h1` (`references/text-hierarchy.md`); the squint test in point 4 shows it |
| Lucide (or Heroicons, Feather, Tabler) at 24 px with a 2 px stroke: an icon by every heading, benefit and list item, often in a tinted square | no icon where it only decorates; where it helps find or operate something, a set whose stroke and terminals match the typeface (`references/icons.md`) |
| shadcn/ui with its default theme: grey neutrals, a black primary button, one radius and a 1 px border on everything, `CardTitle` with a grey `CardDescription` for every block, example blocks pasted whole | keep the primitives' behaviour, own the look: theme tokens from the decision, variants edited in the component code, a card only where it's needed (`references/components.md`) |
| effects from Magic UI, Aceternity and similar kits: border beam, shimmer button, spotlight, meteors, dot or grid backgrounds, logo marquee, number ticker | none by default; at most one per page, when it shows something real about the product |
| the same radius and soft shadow on everything | radius and shadow by role: control, card and image differ or have none at all |
| pill above the H1 ("✨ New", "AI powered") | remove it; put the news in the content or state it as plain text; a 6–8 px badge only where it means something |
| UPPERCASE eyebrow above every heading | remove it; the heading stands on its own; a label only for navigational content, at most 1–2 per page. A small first part of the headline's own sentence above the big word ("Stop using" + "Poppins") is a lockup, not an eyebrow: it stays inside the same `h1` |
| emoji as icons, ✨ as the "AI" sign | no icon, or one icon set with the same stroke width (`references/icons.md`) |
| dark background with neon glow | solid surfaces and contrast; glow only as a deliberate exception |
| motion on everything: fade-up on every section, `hover:scale` on every card | one planned moment of motion and responses to user actions |
| glassmorphism, `backdrop-blur` on cards | solid surfaces separated by tone; blur only for a real layer above content (menu, modal) |
| everything centred, a hero with two equal CTAs | a left-aligned or asymmetric composition; one main CTA |
| gradient text | a solid colour; emphasis through weight or size |
| cards with a coloured left stripe, cards inside cards | no stripe, one level of container; separation through spacing and typography |
| invented numbers, a "Trusted by" row without real clients | real data only; without it, no section |
| em dash (—) in interface copy | a period, comma, colon or parentheses |

## 3. The second wave: templates the model escapes into after a ban

A cream or beige background with a serif (often one word in italics) and a terracotta accent; an almost black background with a single acid accent; mono labels as a "technical" costume; hairline rules like in a newspaper; "·" separators; 01/02/03 numbering with no real sequence. The kit has its own second wave: Inter becomes Satoshi, General Sans, Bricolage Grotesque or Syne; Lucide becomes Phosphor or Tabler; shadcn's grey theme stays and gets one Magic UI effect on top; a flat heading becomes one giant black word with a small line tucked under it in every hero. These are reflexes too. If the project drifts towards them on its own, go back to the decision from the rules and write down specific values.

## 4. Check

**Quick grep (a heuristic, not a verdict).** Every hit is a candidate for a decision, e.g. `rounded-full` on an avatar is fine, but the same on an 8-pixel dot isn't.

```bash
P='rounded-full|border-radius:[[:space:]]*(50%|9{3,4}px)|animate-(ping|pulse)|·|•|bg-clip-text|background-clip:[[:space:]]*text|backdrop-(blur|filter)|(from|via|to|bg|text)-(purple|violet|indigo)-|#(667eea|764ba2|4f46e5|8b5cf6)|uppercase|border-l-(2|4|8)|border-left:[[:space:]]*[2-9]px|—|→|transition:[[:space:]]*all|hover:scale|font-family:[^;]*inter'
grep -rnEi "$P" . --include='*.html' --include='*.css' --include='*.jsx' --include='*.tsx' --include='*.vue' --include='*.svelte' --include='*.astro' --exclude-dir=node_modules --exclude-dir=.next --exclude-dir=dist
```

On GNU/Linux you can catch emoji with `grep -rnP '[\x{1F300}-\x{1FAFF}\x{2728}]' .`. On macOS grep has no `-P`, so check for emoji by eye.

**Kit grep.** Case-sensitive on purpose, so words like "spotlight" in the copy don't match. `K` finds stock icons, fonts loaded from a CDN, shadcn's default tokens and card structure, and animated-kit components; `F` finds the reflex fonts from `references/typefaces.md`. A utility icon inside a component, a font that is the brand's own, or a stock kit in an internal tool can stay; say why.

```bash
INC=(--include='*.html' --include='*.css' --include='*.scss' --include='*.js' --include='*.ts' --include='*.jsx' --include='*.tsx' --include='*.vue' --include='*.svelte' --include='*.astro' --exclude-dir=node_modules --exclude-dir=.next --exclude-dir=dist)
K='lucide|heroicons|react-icons|fonts\.googleapis|@fontsource|--radius:[[:space:]]*0?\.(5|625)rem|text-muted-foreground|CardDescription|magicui|aceternity|BorderBeam|ShimmerButton|ShineBorder|Spotlight|Meteors|Sparkles|AuroraBackground|BackgroundBeams|AnimatedBeam|OrbitingCircles|Marquee|NumberTicker|DotPattern|GridPattern|RetroGrid|TypingAnimation|WordRotate'
F='Inter|Roboto|Open[ _+]Sans|Lato|Montserrat|Poppins|Nunito|Raleway|Work[ _+]Sans|Geist|Space[ _+]Grotesk|DM[ _+]Sans|Manrope|Plus[ _+]Jakarta[ _+]Sans|Outfit|Sora|Urbanist|Figtree|Lexend|Satoshi|General[ _+]Sans|Cabinet[ _+]Grotesk|Clash[ _+]Display|Bricolage[ _+]Grotesque|Syne|Unbounded|Bebas[ _+]Neue|Anton|Oswald|Fraunces|Instrument[ _+]Serif|Playfair[ _+]Display|Cormorant|DM[ _+]Serif|Lora|JetBrains[ _+]Mono|IBM[ _+]Plex[ _+]Mono|Space[ _+]Mono|Fira[ _+]Code'
grep -rnE "$K" . "${INC[@]}"
grep -rnwE "$F" . "${INC[@]}"
```

**Render.** Take screenshots at 1440 and 375 px and check:

1. **Squint:** is there one point of focus, or is everything shouting equally loud?
2. **Swap test:** would another model with a similar prompt produce almost the same thing? If so, a signature is missing.
3. **"AI made this" test:** would someone say at a glance that it's generated? Point to the specific element and apply the table.
4. **Library-spotting test:** would a front-end developer name the font, the icon set or the component kit from one screenshot? If so, that element is still at its default.

## Pitfalls

- **Removing everything indiscriminately.** A dot next to a real state (server online/offline, a free slot from a calendar) stays, just static and with a label. The close button in a dialog, the chevron in a select and the search icon in a field stay too; only decorative icons go.
- **A new font set flat.** Swapping the typeface without ranking the words leaves the text as generated as before. The hierarchy comes first; the font only carries it.
- **Swapping Inter for Space Grotesk, Geist, Satoshi or Fraunces, or Lucide for Phosphor,** trades one reflex for another; it isn't a decision. Choose the typeface and the icons for the subject and write down why.
- **Throwing out the kit along with its look.** Replacing shadcn's `Dialog` or `DropdownMenu` with hand-written divs loses keyboard and focus handling. Restyle the primitives; don't remove them.
- **A typeface without the language's letters.** A display face picked from a catalogue often lacks ą, ę, ł or ś in some weights, and the browser silently fills them in from another font. Render a test line in the site's language before you commit.
- **A colour "from the subject's world" is often what every model would pick** (joinery → brown, florist → pink). Do the swap test: if the accent is obvious, the signature has to live elsewhere, e.g. in the composition or typography.

## Output

A list of the patterns found with their location in the code, a decision for each (removed, replaced with what, kept and why), plus the three rejected defaults and the project's signature. When you chose or changed a typeface: the family, its role, the reason, the source, the licence and the accented letters checked. When icons or a component kit are involved: where icons were removed, which set stays and why, and what changed in the theme.
