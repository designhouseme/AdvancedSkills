---
name: website-review
description: Performs an independent review of a finished business website based on screenshots and the render. Scores architecture, copy and design on a 1–10 scale and returns a STATUS with at most five concrete fixes. Use after building a site, before showing it to the client, or when someone asks for an assessment or critique of a company's website, including a client's existing site. Not for technical SEO, performance or accessibility (WCAG) audits. Doesn't fix the code or copy itself; it only names the stage that should do it.
license: CC-BY-4.0
metadata:
  author: Design House
  version: "1.2"
---

# Website review

The review assesses whether a potential customer understands the offer, trusts the company and knows what to do next. Correct code, a passing build and a good performance score are technical prerequisites. They don't raise the copy or design scores.

## Rules that always apply

- **Judge what's visible.** The basis is screenshots at 375×812 and 1440×900 (or a render you open yourself), not the code, the plan or the author's claims. Without seeing the render you don't give scores, only `STATUS: BLOCKED`.
- **Observation first, then the number.** 5–6 means significant problems, 7 works with visible weaknesses, 8 is a strong result with no blockers, and 9–10 needs exceptional justification. Don't give a 9 for the mere presence of sections and photos.
- **Report only what changes the customer's decision, the truth or usability.** Reviewers asked to look for gaps report too many. At most 5 fixes, most important first.
- **Be honest about independence.** If you built the site yourself in the same conversation, say it's a self-review, not an independent one.
- **Don't claim the site "will increase conversion".** This is an expert assessment, not a measurement.
- **A fix goes to the stage that owns the problem.** Copy, section order, proof or an untrue claim go to website-plan. A missing or unconfirmed fact goes to company-research or becomes a question for the user. Layout, code, images and technical bugs go to website-build. One fix is one problem and one stage. For someone else's site, give the type instead of the stage: copy, fact or code.
- **A fix doesn't add new claims.** If a fact is missing (e.g. "free measurement" without a Source ID), record it as a question for the user, not as text to insert.

Input: screenshots from `brief/screenshots/` or the site's local address, plus `brief/02-plan.md` and `brief/01-research.md` if they exist. Without a plan (e.g. reviewing someone else's site), skip the comparison with the plan.

## 1. First look, without the plan

Before you read the plan, look at the hero at both widths and write down, as someone outside the industry would:

- what the company does, for whom or where, why to consider it and what to click (the 5-second test),
- what caught your eye and what idea stays in memory once the logo and name are covered.

The order is deliberate. Whoever knows the author's reasoning starts seeing the intention instead of the effect.

## 2. Comparison with the plan and the truth

- **Scan:** do the H1, H2s and CTAs on the render alone make the same argument as the scan test in the plan?
- **Proof:** is the strongest proof before the halfway point of the page and close to the claim it supports?
- **Truth:** every strong claim can be traced to a fact in the research. Reviews, numbers, prices and lead times aren't invented. Stock doesn't pose as projects or the team.
- **Contact:** phone, email and address match the data from the user. The contact section says what happens next, and the FAQ is directly below it.

## 3. Scores

For each dimension write: `section/viewport → observation → score → what's left`.

| Architecture | Copy | Design |
|---|---|---|
| customer decision: the order answers the questions asked before getting in touch | relevance: says what the customer needs to hear | first screen: catches the eye, offer is clear |
| argument: the H1, H2s and CTAs tell one story | clarity: understandable without rereading | images: meaningful, well cropped, honest |
| proof: strong and early | specificity: sentences specific to this company | hierarchy: the eye starts with the answer for the customer |
| selection: every section changes the decision | truth: claims are backed | mobile: designed, not just collapsed into a column |
| closing: contact and FAQ remove the last worries | naturalness: sounds like the company, not a generator | character: one memorable idea that fits the company |

**Caps that other points can't make up for:**

- A physical service without meaningful photos: design at most 5.
- Default font, equal cards and generic stock unrelated to the company: design at most 6.
- Decorative dots, pills and eyebrows that carry no information, gradient text or a purple gradient unrelated to the brand (list in the ui-without-slop skill): character at most 6.
- Years in business, headcount or awards with their own section and no consequence for the customer: selection at most 6.
- An invented review, number, or stock labelled as a project: truth 1, which means automatic `NEEDS_CHANGES`.

**Threshold:** each of the three columns averages at least **8**, and no dimension falls below **7**.

## Output: `brief/03-review.md`

```md
STATUS: READY | NEEDS_CHANGES | BLOCKED
Review: independent / self

## First look
## Scores (dimension | observation | score)
Averages: architecture x.x · copy x.x · design x.x

## Fixes (at most 5, most important first)
1. [section, viewport] problem → fix in one sentence → stage: website-plan | website-build | company-research

## What was checked
```

- `READY`: threshold met and no truth problems.
- `NEEDS_CHANGES`: threshold not met or there's a truth problem. Each fix names the stage that should carry it out.
- `BLOCKED`: the render couldn't be seen or a decision from the user is needed (e.g. missing contact details, a key fact unconfirmed).

## Pitfalls

- **Correct elements aren't character yet.** A big photo, a big H1 and a different palette can score well in their own dimensions while the whole stays predictable. If you can't point to an idea beyond them, character and first screen don't get an 8.
- **A screenshot with an unloaded image, an animation frame or a duplicated header** isn't a basis for scoring. Ask for a new one or take your own.
- **The site faithfully implements a weak plan.** If the problem is prominent years in business or an "About us" section, the fix goes to website-plan, not website-build.
- **No reviews isn't a flaw in itself.** Judge the quality of the honest substitute (process, person responsible, qualification, photo of the work), not the absence of stars.
