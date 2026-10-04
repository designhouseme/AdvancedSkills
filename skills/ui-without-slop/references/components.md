# Components and UI kits

Read when the project uses shadcn/ui, a Tailwind template, or effects from Magic UI, Aceternity UI and similar kits, and before you write the component look into the decision. The library isn't the problem. shadcn/ui and the Radix primitives under it give keyboard support, focus handling and ARIA that are hard to write by hand. The problem is shipping the default theme and the example blocks unchanged: thousands of sites share them, so on screen they read as "nobody decided".

## 1. What the stock look is made of

**shadcn/ui at its defaults:**

- grey neutrals (neutral, zinc, slate or stone) with a near-black primary button, inverted in dark mode;
- one `--radius` (0.5 or 0.625 rem) on every button, input, card, badge and popover;
- a 1 px border on every card and input, plus a faint `shadow-xs` or `shadow-sm`;
- every content block as `Card` → `CardHeader` → `CardTitle` with a small grey `CardDescription` (`text-muted-foreground`);
- `Badge` pills, segmented `Tabs` on a grey track, an FAQ in an `Accordion` with a chevron, `Sonner` toasts in the corner, the soft default focus ring;
- Geist or Inter, and Lucide icons;
- example blocks pasted whole: the dashboard with a sidebar, an area chart and a data table; the centred login card.

**Tailwind templates at their defaults:** the stock palette used as the brand's colours (`blue-600` buttons, `gray-50` sections, `slate-900` text) and `rounded-xl shadow-lg` on everything.

**Animated kits** (Magic UI, Aceternity UI, React Bits and similar): border beam, shimmer or shine buttons, spotlight, meteors, sparkles, aurora or beam backgrounds, dot, grid and retro-grid patterns, an animated beam connecting logos, orbiting circles, a logo or testimonial marquee, a number ticker, typing or rotating words, a bento grid with hover reveals, 3D tilt cards, a globe.

## 2. What to do

1. **Keep the behaviour, own the look.** Keep Radix, Base UI, React Aria or whatever primitives the project uses: dialogs, menus, popovers, selects and tabs must still work with the keyboard and a screen reader. Change what they look like, not what they do.
2. **Tokens first.** Before touching components, rewrite the theme from the decision: colours from the 4–6 named values (neutrals tinted towards the accent rather than pure grey), radius by role instead of one `--radius` for everything (controls, containers and images may differ or have none), separation by tone or spacing instead of a border on every box, a focus style in the brand's colours that stays clearly visible, the chosen typeface.
3. **Edit the variants in the component code.** That's the point of shadcn: the code is yours. A primary button that isn't a black rounded rectangle, tabs as an underline or as text with weight, a badge only for a real state, an accordion only where people really need to skip between answers.
4. **A card holds a clickable thing or a real group, it isn't the default wrapper.** Most sections are text, a list or an image held together by spacing; see the identical-cards row in SKILL.md.
5. **Blocks are starting points, not layouts.** Compose the page from the content. If you start from a block, change its structure, not only its colours.
6. **Effects from the animated kits: none by default.** At most one per page, and only when it shows something true about the product, such as a real data flow. Logo marquee → a static row of real clients' logos, or no section; number ticker → the number with its source; dot or grid background → a plain surface, the brand's texture or a photo; spotlight, meteors, beams, border beam → remove.

## 3. Where a stock kit is fine

In internal tools, admin panels and early prototypes, a stock kit with the brand's colour, the chosen typeface and a few token changes is a legitimate choice: consistency and accessibility matter more there than a signature, and Lucide is fine for utility icons. The bar is higher on public brand surfaces: the marketing site, onboarding, empty states.

## 4. Check

- **Theme reset test:** if you replaced the theme (`globals.css`, the Tailwind config) with the kit's default, would the page visibly change? If it would barely change, the kit was never styled.
- **Library-spotting test:** would a front-end developer name the library from one screenshot? If so, find the elements that give it away and apply section 2.
- **Keyboard after the restyle:** go through dialogs, menus, selects and tabs with the keyboard alone (Tab, Shift+Tab, Esc, arrows, Enter). Focus is visible at every step and returns to the trigger after a dialog closes.
- The kit grep in point 4 of SKILL.md finds the default tokens, the stock card structure and the animated-kit components.
