---
name: company-research
description: Produces verifiable research on a specific company. Confirms its identity, scope of services, customer voice and trust signals, and records every fact with a source and date. Use when someone asks to research a company, vet a client or contractor, find out "what we know about company X", or prepare for a meeting or proposal. If someone wants a whole website for the company, use business-website, which runs this research. Not for market or competitor analysis, and not for a single fact such as a tax ID alone.
license: CC-BY-4.0
metadata:
  author: Design House
  version: "1.1"
---

# Company research

The goal is not a company chronicle but material you can make decisions from: what the company really does, for whom, and why a customer would trust it. The result must be auditable, so every fact has a source, an access date and a status.

## Rules that always apply

- **Don't guess facts about the company.** You may infer customers' needs and worries, but numbers, prices, lead times, licences, guarantees and client names go in only when you have a source. Missing data is also a result: record it explicitly.
- **Contact details come from the user only.** Take the phone number, email, address and tax ID for further use from what the user gave you. Record discrepancies with the internet, but don't correct them: directories often carry outdated data.
- **A company's claim is not an objective fact.** Record "the highest quality" from the company's own site as a claim, not as a confirmation.
- **Public, business-related information only.** Don't collect private data about people beyond what the company itself publishes about its team.
- **Without internet access**, work from the user's material and say plainly what could not be checked.

## 1. Confirm it's the right company

Before attributing a source to the company, match at least **two** strong identifiers: address or town, phone, domain, tax or company registration number (e.g. VAT or Companies House number; in Poland NIP, KRS or REGON), owner, or a link from an official profile. With similar names, discard ambiguous results. A name match alone is not enough: in small towns several companies have almost the same name.

## 2. Go through the sources

Search: name + town, name + phone or tax ID, owner + industry. Check:

- the current website and its subpages (services, projects, about, contact, FAQ),
- the Google Business Profile and reviews,
- official social media and industry profiles,
- official business registers (e.g. Companies House in the UK, CEIDG or KRS in Poland) and directories, but only to confirm existence, years in business or licences.

## 3. Establish scope before choosing a narrative

An activity code (SIC, NACE, PKD), a directory category and the company name are leads, not a description of the offer. Compare current services, described projects and audiences, and record a matrix:

| scope / specific jobs | audience B2B/B2C | core / additional / unconfirmed | Source IDs | limitation |
|---|---|---|---|---|

Don't reduce a specialisation to one photogenic job, and don't add services just because they fit the category. The absence of a mention doesn't prove the company doesn't do something, so never write "we don't do X" without a source. Unconfirmed services stay out of the promises.

## 4. Customer voice

Go through 10–30 of the most recent substantive reviews from at least two sources and skip duplicate copies. Extract:

- what jobs or situations customers come with,
- what they worried about before buying,
- the words they use to describe a good result,
- which of the company's behaviours they praise,
- who the offer may not suit.

Give frequency as `frequent / several times / isolated` unless you counted a full sample. A handful of reviews is not a statistic.

## 5. Proof

Separate: projects (job, place, result), reviews with author and link, photos of the work, team and premises, qualifications and certificates, and published prices, response times and guarantees, as long as they are confirmed.

Each entry gets a status: `verified`, `needs-confirmation` or `do-not-use`. Distinguish the company's own claims from independent confirmation, and establish the company's exact role in each project.

Along the way, record direct links to the company's photos and logo: what they probably show, why they belong to the company and whether the rights are clear. Don't download competitors' photos and don't treat stock as projects.

## 6. Claims register

Give the material permanent identifiers, so later work (proposal, copy, review) doesn't have to guess where anything came from:

- `F001…` fact about the company, offer, location, price, lead time or qualification,
- `V001…` observation from reviews (voice of the customer) or a short customer quote,
- `P001…` proof: project, review, result, certificate, confirmed way of working.

Row format: `ID | claim | direct URL or "material from the user" | access date YYYY-MM-DD | status | limitation`. The identifiers are internal and never appear in customer-facing copy.

## 7. Conclusions

Finish with five decisions:

- main audience and their situation,
- the most important job or outcome,
- the biggest worry,
- the strongest proof,
- recommended next step and the simplest way to get in touch.

Check the sentence: **"A customer with the job ___ has a reason to consider this company because of ___, as confirmed by ___."** If all you can fill in is years in business or headcount, the research has confirmed the company exists but has not yet found a reason to choose it. Say so plainly.

## Output

Save the report to `brief/01-research.md` unless the user named another location. Without a file system, return it in your reply.

```md
# Research: <company name>
## Identity and sources
## Scope and audience matrix
## The offer through the customer's eyes
## Customer voice: jobs, worries, language, outcomes
## Proof
## Claims register
| ID | claim | URL/source | access date | status | limitation |
## Company visual materials
| what it shows | URL | link to the company | rights/status |
## Discrepancies and things to confirm
## Conclusions
- Audience and situation:
- Job/outcome:
- Biggest worry:
- Strongest proof:
- Next step:
- Reason to choose (test sentence):
```

A short quote from a review is fine; don't copy long ones. Missing material doesn't stop the work: mark it and move on.

## Pitfalls

- **A photo of a building is not proof of quality.** If the company did only part of a project (e.g. the installations), a photo of the whole building shows context, not their work. Look for close-ups of the work and a description of the scope.
- **The same description in three directories is one source.** Directories copy the company's own text, so they don't count as independent confirmation.
- **"No website" in notes is often outdated.** If you find the company's own site, record the discrepancy and work from the new fact instead of defending the old assumption.
- **Reviews from one month or one project** can distort the picture. Note the period and how many sources they come from.
