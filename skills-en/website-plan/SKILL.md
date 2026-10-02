---
name: website-plan
description: Turns company research into a plan for a short website, that is the customer's decision, 4–7 sections ordered around that decision, the hero and finished copy tied to proof. Use when you need to plan the sections or write the copy of a business website or landing page from research, notes or reviews of the company, including changes to the copy or section order. Doesn't do research (that's company-research) or code (that's website-build), doesn't translate websites and doesn't write social media posts.
license: CC-BY-4.0
metadata:
  author: Design House
  version: "1.2"
---

# Website plan and copy

The plan settles the site's argument before the layout starts fighting for space. The question isn't "what information do we have?" but "what does the customer need to hear, see and believe to take the next step?".

## Rules that always apply

- **Hierarchy of truth.** A *fact* (from the user or `verified` in the research) can be a claim. A *safe inference* can drive the order, the benefit language and the FAQ, but it can't create numbers, prices, lead times, licences or guarantees. *Missing data* you leave out, phrase conservatively or mark for a decision. You never cover it with fiction.
- **Every strong claim has a Source ID** from the research register (`F…`, `V…`, `P…`). Without an ID, weaken it or remove it. IDs never appear in the visible copy.
- **A fact is not yet an argument.** For years in business, headcount, fleet size, awards and similar numbers, write `fact → permitted inference → consequence for the customer`. Headcount doesn't prove lead times or quality. If the chain ends at "we're big/experienced", the fact is only context next to the right proof and doesn't get its own section.
- **Don't invent reviews, clients, projects or results.** Take contact details from the user only.
- **Write the copy in the language of the business's customers.** If that's unclear, use the language of the user's input and note the assumption in "Gaps and decisions".

Input: `brief/01-research.md` and `brief/00-input.md`. If there's no research, run the company-research skill first. If the user wants a plan from their own notes only, treat them as the only source: give them F/V/P identifiers marked "material from the user" and state in the plan that no research was done.

## 1. Customer decision

```md
The visitor arrives here when:
They want to decide:
Their biggest risk:
They'll believe it because of:
After the site, they should:
```

With several customer groups, choose one main path. A site for everyone is a site for no one.

## 2. A map of questions instead of a list of modules

Write down the real questions in the order the customer asks them before getting in touch, e.g. do you do exactly this, and in my area; does the result look good; can I trust you on price and timing; what's working with you like; what happens when I call. For each, record the **basis**: a risk, a job or a `V…` observation from the research. A question that appeared only because you found an impressive number is a hypothesis, not a customer need.

## 3. Candidates and the reverse-justification test

Each candidate section has: the customer's question (in their words), the basis for the question, a one-sentence thesis, how the decision changes after the section, the role of the proof (`direct / proxy / context / action`), Source IDs or an explicit gap, media and an attention budget (`first viewport / high / medium / closing`).

Then three tests:

1. **Outside-in.** Set the company facts aside and write the three most important questions that follow only from the customer's decision and risk. The candidates must map to them.
2. **Removal.** If without the section the customer would make the same decision with the same confidence, merge it with another or remove it.
3. **Wrapping.** Write a working H2 and first sentence. If, with the numbers and the company name hidden, the meaning is "we're big", it's self-promotion. Rewrite it around responsibility, process or a real person, or remove it.

## 4. Selection and order

- 4–7 sections (header and footer don't count), hero first.
- The first two sections after the hero show that the company does the scope the customer needs, or give strong proof of trust. History and values don't take that spot.
- The strongest proof goes in the hero, right below it or **before the halfway point of the page**.
- **Contact second to last, FAQ last**, directly below contact.
- Prominence can't exceed the importance for the decision and the strength of the proof. An impressive big number doesn't become the dominant element.

Lay out two sequences of theses only: **A, proof first** (expensive, visual or risky service) and **B, orientation first** (the customer first needs to understand the options). Choose one based on the main worry and the quality of the material.

## 5. Hero

Write the first screen's job: *"In 5 seconds the visitor should understand ___, believe ___ because of ___ and do ___."*

Write three genuinely different directions: **service-led** (what and where/for whom), **outcome-led** (a specific result) and **proof-led** (verified proof that removes the biggest risk). Score each 1–5 for clarity, relevance, credibility and distinctness from a competitor, and write the full copy only for the winner.

The hero has: an H1 (usually 4–12 words, not just the company name, not an empty slogan), 1–2 sentences of clarification, one main CTA as "verb + a specific next step", at most one quiet secondary action and **one** strong trust signal next to the CTA instead of several weak ones. Don't cram the whole offer, three stats and a logo carousel into the hero.

## 6. Section copy

Before writing, read `references/copy-style.md`: tone, sentence length, the offer, contact, FAQ and the list of banned phrases. Keep the order from point 4. If a section turns out empty or repeats another while you write, go back to selection instead of padding it.

## 7. Media and visual direction

Plan 3–6 image slots. Each has a function and a truth status. Order of sourcing: the company's own project photos, real photos of people, premises or process, licensed stock with a specific subject as atmosphere, generated images as atmosphere. **Stock or generated images never pose as the company's projects, team, premises or clients.** A real, imperfect photo is often better proof than perfect stock.

Visual direction: propose 3 clearly different directions that fit the company, not the competition (background, accent, typeface and one idea that sticks in memory), choose one and justify it in one sentence. Avoid the patterns listed in the ui-without-slop skill, including its "second wave" (cream background with a serif and terracotta, mono labels, "·" separators).

## 8. Gate before handoff

1. **Scan test.** Read only the H1, H2s and CTAs in order. Do they form a complete, logical argument? Is any heading mainly about the company rather than the customer?
2. **Competitor swap test.** Insert the names of three local competitors. Make every sentence that still sounds credible more specific, or remove it.
3. **5-second test.** Someone outside the industry, after one glance at the hero, knows what the company does, for whom/where, why to consider it and what to click.
4. **Truth.** Every strong claim has a Source ID or is explicitly a safe inference.
5. **Cut.** Trim the whole thing by 15–25% without losing answers or proof.
6. **Adversarial pass.** Look for promises the owner couldn't prove, sentences that sound generated, and places where the customer still doesn't know what happens after they get in touch.
7. **Automatic check.** Run `python3 scripts/check_plan.py brief/02-plan.md brief/01-research.md`. In the site content (Sections, Hero, Section copy, Contact, FAQ, Meta, Media) the script checks that every Source ID exists in the register and has `verified` status, as well as the length of the title and description, the absence of em dashes, and the number and order of sections. In "Rejected" and "Gaps" list IDs openly, including `do-not-use` ones, because that's where you document what you're not using. Fix every `ERROR`. Fix every `WARNING` or justify it in "Gaps and decisions".

## Output: `brief/02-plan.md`

```md
# Website plan: <company>
## Customer decision
## Rejected or merged sections (candidate | decision | why)
## Sequence A / B and choice
## Sections
| # | customer question | basis | thesis | proof role | Source IDs | media (slot, truth status) | attention budget | CTA |
## Hero (5-second job, scores for 3 directions, H1, clarification, CTA, trust signal)
## Section copy (heading, text, proof, CTA, Source IDs)
## Contact
## FAQ
## Meta
- Title: … (up to 60 characters)
- Description: … (up to 155 characters)
## Media (slot | function | source | truth status | gap/fallback)
## Visual direction (3 directions, the chosen one and why)
## Scan test (H1, H2s, CTAs in order)
## Gaps and decisions for the user
```

## Pitfalls

- **All the reviews in one slider at the bottom of the page.** Distribute proof by function: a review about punctuality next to the worry about timing, a project photo next to the offer.
- **The same rating or quote in several sections.** Each piece of proof works once, where it removes a specific worry.
- **Before/after from two different projects.** A before-and-after pair must come from the same documented project. Anything else is manipulation.
- **A calculator or configurator without data.** An interactive section only makes sense when it helps make a real decision and can be built from confirmed prices or parameters.

Next stage: website-build, after the user approves the plan, if you're working in the business-website chain.
