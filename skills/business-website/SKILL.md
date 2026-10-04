---
name: business-website
description: Runs the whole process of creating a short website for a local business, from a pasted description to a working, reviewed site. Use when someone pastes information about a business and wants a website, an online business card or a landing page for it ("make a website for…"), or comes back with new material or a change to a site made with this process and it's unclear which stage it affects. Not for online shops or apps; research alone, copy alone, code alone or a review alone are separate skills.
license: CC-BY-4.0
metadata:
  author: Design House
  version: "1.1"
---

# Business website (orchestrator)

This skill does no substantive work itself. It sets the order of the stages, looks after the handoff files and decides when to stop for approval. Each stage has its own skill, which you call by name.

## Rules that always apply

- **The user's instructions take precedence over this skill.** If the skill tells you to stop, ask or do something differently from what the user asks, name the rule you're relying on and explain briefly, instead of quietly departing from the request.
- **State lives in files, not in the conversation's memory.** That way the process can be interrupted, compacted or resumed in a new session.
- **Contact details come from the user only**, never from the internet without confirmation.
- **Don't invent facts, reviews, clients or numbers.** Mark missing data and move on.
- **No purchases and no publishing.** Don't register domains, deploy to a server or send anything without an explicit request.

## Handoff files

| file | written by | contents |
|---|---|---|
| `brief/00-input.md` | this skill | the user's inputs verbatim, append-only, dated |
| `brief/01-research.md` | company-research | facts, proof, F/V/P register, conclusions |
| `brief/02-plan.md` | website-plan | customer decision, 4–7 sections, hero, full copy, media |
| site code | website-build | the project's stack or a static `index.html` |
| `brief/screenshots/`, `brief/media.md` | website-build | 375 and 1440 px screenshots, list of images with source and truth status |
| `brief/03-review.md` | website-review | STATUS, scores, up to 5 fixes |
| `brief/progress.md` | this skill | checklist of stages, approvals, open decisions |

At the start, write this to `brief/progress.md` and tick it off as you go:

```md
- [ ] 0. Input saved
- [ ] 1. Research (company-research)
- [ ] 2. Plan and copy (website-plan)
- [ ] 3. Plan approved by the user (or: "no questions" mode)
- [ ] 4. Build (website-build)
- [ ] 5. Review (website-review), round 1
- [ ] 6. Fixes and review, round 2 (if needed)
- [ ] 7. Result handed to the user
```

## Flow

0. **Input.** Save the user's text to `brief/00-input.md`. Ask only when the business can't be identified unambiguously, contact details are missing, or it's unclear what the site should achieve (calls, a form, bookings). Work out the rest yourself and mark your assumptions. The site's language is the language of the business's customers; if that's unclear, use the language of the user's input and record it as an assumption.
1. **Research.** Run the company-research skill. Output: `brief/01-research.md`.
2. **Plan and copy.** Run the website-plan skill. Output: `brief/02-plan.md`.
3. **Checkpoint.** Show the user the H1, the list of sections (headings and CTAs) and the open gaps, and wait for approval. Skip this step only when the user asked for work with "no questions"; in that case record it in `progress.md`.
4. **Build.** Run the website-build skill on the approved plan.
5. **Review.** Run the website-review skill. If the environment lets you start a subagent, hand the review to a separate agent without this conversation's history. Fresh eyes don't know the author's reasoning, and that's why they see more. The delegation includes: the goal (a review with the website-review skill), paths to `brief/02-plan.md`, `brief/01-research.md`, `brief/screenshots/` and the site, the output format (`brief/03-review.md`) and the limits: it doesn't edit code or copy.
6. **Fix loop.** On `STATUS: NEEDS_CHANGES`, pass the fixes to the stage named next to each one, then repeat the review. At most **2 rounds**. Fixes to copy or section order go to website-plan; they are not patched in the code.
7. **Result.** Briefly: how to view the site (command or file), the review result, and a list of decisions for the user (missing photos, facts to confirm). If problems remain after 2 rounds, list them honestly.

## Resuming and changes

Don't start over. Find the **first missing or incomplete file** in the table and resume from the stage that writes it. Append new user input to `00-input.md`.

For a change, go back to the earliest affected stage:

- new fact, offer, review, contact details or a misread industry → company-research,
- different H1, section order, copy, CTA, weak proof → website-plan,
- colour, typography, layout, photo, technical bug → website-build.

Every path ends with a new review.

## Pitfalls

- **The file exists but is incomplete.** An interrupted session leaves, for example, a plan without section copy. Before resuming, check that the file has every section of its format, not just that it exists.
- **Same name, different company.** Before resuming a project, compare the business with `00-input.md`. A company with the same name in another town is a new project.
- **"It doesn't make people get in touch"** is usually weak or buried proof in the plan, not the button colour. Start with website-plan.
- **"Boring", "lifeless", "like every other site"** is about the whole site: the visual direction and the first screen. Changing the palette or one section doesn't close that kind of feedback.
