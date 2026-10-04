# Icons

Read when the layout seems to need icons, before you choose an icon set, and when you review icons in an existing UI. The look most models produce is Lucide (or Heroicons, Feather, Tabler) at 24 px with a 2 px round stroke, one by every heading and list item, often in a tinted rounded square. Changing the set doesn't fix that. Start by asking whether the place needs an icon at all.

## 1. Does this place need an icon?

An icon earns its place when it helps someone find or operate something:

- controls with little room: close, menu, search, play, previous and next, expand;
- actions people recognise faster as a symbol than as a word, always with a text label or an `aria-label`;
- states shown next to their word (error, done, warning);
- repeated items someone scans in a product UI: file types, statuses in a table, sections of an app's navigation.

It doesn't when it only decorates: above a benefit or feature card, before every list item, next to every link in a site's menu, or as a picture of an abstract idea (a shield for security, a rocket for growth, lightning for speed). Replace it with nothing, a stronger heading, a number that means something, or a real photo or product detail.

## 2. Choosing a set

When icons are needed, choose the set by its drawing, the way you'd choose a typeface, not by its name:

- **The stroke matches the text.** At the size used, the icon's stroke is close to the stem of the text next to it. A 2 px stroke next to light text looks heavy; a hairline next to bold text looks lost.
- **Terminals and corners match the typeface:** round caps and joins with rounded or humanist type, square ends and sharp corners with grotesques, slabs and technical faces.
- **Outline or filled follows the density.** Filled reads better small and on dense screens; a thin outline suits spacious brand pages. Don't mix the two in one context, except to mark the active state.
- **The grid fits the size.** A set drawn on a 15–16 px grid stays crisp in compact UI; a 24 px set scaled down to 14 px goes soft.
- **The set covers everything the project needs.** Check before committing: a second set brought in for two missing symbols breaks the consistency.

Compare candidate sets side by side on Iconify (icon-sets.iconify.design) or Icônes (icones.js.org), next to the project's typeface at the real size. Moving from Lucide to Phosphor or Tabler only because they're "not Lucide" is the same reflex; the choice needs a reason from the list above.

**Custom icons.** The brand's own pictograms, drawn by its designer on the logo's grid, are the strongest signature an icon can give. Don't draw icons yourself as SVG paths: icons drawn by a model come out uneven and look broken next to text. When the brand has none, use a set.

## 3. When the project already uses Lucide

shadcn/ui installs Lucide by default, and many projects keep it. You don't have to swap the library:

- keep it for utility icons inside components (chevrons, close, check, search), where nobody reads them as a style;
- remove the decorative ones (section 1);
- tune the rest to the typeface: `strokeWidth` (e.g. 1.5 or 1.25 next to light text), `absoluteStrokeWidth` so the stroke doesn't change with the size, a size tied to the text and `currentColor`;
- drop the tinted squares and circles around icons.

Swap the library when icons are a visible part of the design (navigation, the feature list that survived section 1, empty states) and their drawing clashes with the typeface.

## 4. Implementation

- Inline SVG or the package's components. Never Unicode symbols (→ ✓ ★) or emoji in place of icons.
- A decorative icon next to text gets `aria-hidden="true"`. An icon-only button gets an `aria-label` naming the action.
- Size the icon with the text (`1em` to `1.25em`, or set together with the font size) and align it to the text's x-height or cap height, not to the line box.
- Colour from `currentColor`. An accent colour only when the icon itself carries meaning, such as a state.
