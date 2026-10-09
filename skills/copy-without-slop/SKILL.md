---
name: copy-without-slop
description: >-
  Writes, edits and reviews website copy, emails, newsletters, social posts, ads,
  offers, product descriptions, replies to reviews, articles, letters and
  announcements. Works from facts and customers' own words, decides the voice,
  and replaces generic or
  generated-sounding patterns with concrete proof. Handles Polish voice and
  typography. Use when asked to write, rewrite, edit, shorten or check text, or when it
  "sounds like ChatGPT", "brzmi jak AI", is generic, salesy or stiff. Planning a
  whole website from research belongs to website-plan, which uses this skill for
  the words. Not for translation, fiction, code documentation or AI-detector scores.
license: CC-BY-4.0
metadata:
  author: Design House
  version: "1.3"
---

# Copy without slop

Generated text sounds generated mostly because the model had no facts and filled the gap with the most likely words: general, positive and interchangeable. A list of banned words doesn't fix that. Ban "seamless" and the model writes "dependable"; ban "not X but Y" and it writes "Y rather than X". So this skill starts from the material, decides the voice, and only then edits patterns out, each one replaced with a fact or cut.

**Proof over promise.** Show named suppliers, ingredients, methods, people and documented results when the material contains them. Replace "trusted sources" with who supplies what, and why that choice matters if the reason is known. Help the reader picture the work and the result; an unsupported precise detail is still invention. Keep marketing proportionate to the actual offer.

## Pitfalls

- **Invented details.** Without facts the model fills in plausible ones: "for years", "fully insured", "no artificial additives", a use the product was never sold for. Every number, name, claim and promise about the business comes from the material or from the user, including numbers written as words ("in ninety per cent of cases", „setki zadowolonych klientów”, „kilka godzin pracy”). Writing in the owner's voice doesn't license inventing what they do, how often or for how much. An invented exact detail is worse than a plain sentence, because a reader can catch it and then doubts the rest.
- **Inferred benefits.** The subtler form: "so you don't have to wait for anyone else to sign it off", "drop the car off on your way to work". If the material doesn't say it, it doesn't go in the text. Offer it to the user as a suggestion to confirm.
- **General knowledge is not invention.** Explaining a fact with what is true of every product or business that has it is fine: "end grain is gentler on knife edges", "a valley is where two roof slopes meet". Say in the reply which sentences come from general knowledge. When the user asked for a length, reach it by explaining the facts and the reader's next step; if that still falls short, say so instead of padding.
- **A ban without a replacement moves the habit.** Replace a pattern with a fact from the material, a plain statement or a cut. Never with a synonym or a fresher phrase.
- **Read the pattern lists after the draft.** `references/patterns.md` and the second half of `references/polish.md` are for the edit pass. Read before drafting, a list of patterns pulls the draft towards them.
- **Other people's words stay theirs.** Customer quotes and an owner's own sentences keep their wording. A polished quote reads as invented. Fix spelling, cut with an ellipsis, nothing more.
- **"Human" is not a costume.** Typos, slang, filler words, invented anecdotes and a quirky tone are what humanizer tools add, and readers spot them as quickly. Text reads as written by a person when it says what only this person or company could say.
- **No em dash (U+2014).** Prefer a period, comma, colon or parentheses. If a sentence needs a dash, use a standard hyphen (-), as the house style; numeric ranges may keep an en dash. Preserve quoted wording.

## 1. The job

Decide which of four jobs this is, because they change how much you may touch.

- **Write** from notes or material.
- **Rewrite** text the user says sounds generated: keep every fact, cut the rest, and say what you removed.
- **Edit** someone's own text ("fix the typos", "polish this"): the smallest change that solves the problem. Keep their register (ty, wy or Państwo), their asides and roughly their length (±15%). If the text already works, say so, name what makes it work and return it almost unchanged.
- **Review** without changing anything: quote each problem, say why, and give a decision (cut, replace with which fact, or keep because…).

Write in the language of the text's readers. For Polish, read part 1 of `references/polish.md` now.

## 2. Material

List what you have before writing a sentence, in the same working note: facts (what, where, for whom, how it works, what happens after someone gets in touch, what the company doesn't do), numbers with their source, customers' own words from reviews or emails, and proof (a named review, a photo, a qualification, a process step). For anything longer than a few lines, `references/voice.md` has the brief and the ladder for when facts run short.

When the material is thin, write a short text from what exists and ask 2–4 specific questions whose answers would add proof. Don't pad a short text to look complete.

## 3. Decide before drafting

For a headline, a page, a campaign or anything where voice matters, settle these first, in a working note rather than in the reply:

- **Reader and moment.** Who reads it, where they come from and what they want to know. The first sentence answers that.
- **Outcome and concerns.** What the reader wants to experience, what makes them doubt this offer, and what they need to know about time, effort and the next step. Answer with supported specifics at the point the question arises. Use their language so they feel understood; don't inflate the outcome or assume everyone buys for status.
- **The one thing only this business can say.** Put a competitor's name into the sentence. If it still holds, it isn't the one thing. For a headline the test applies to the headline itself, not to the line under it. A label like "NHS and private dentist in Norwich" helps search, but every practice in town can use it: put it in the page title or the line below, and build the headline on the fact only this business has, unless the user asked for a label.
- **Voice as values, not adjectives.** Who speaks (we, I, a named person), the form of address, sentence length, a few words the customers themselves use, a few words this business would never say. Describe the voice by what it does ("answers the price question in the first line"), never as "calm, competent, friendly": adjectives like that produce text that rates itself ("dependable", "steady") instead of saying something.
- **Three defaults you're rejecting** in this text (for example: opening with the company's history, three benefit adjectives, ending on "Zapraszamy!") and one element that belongs only to this text.

When nothing gives a direction and the text is prominent (a headline, a hero, an ad), write 2–3 genuinely different candidates, each built on a different fact, and pick one with a reason.

## 4. Draft

Lead with the fact the reader came for. One thought per paragraph. Verbs with someone doing them ("we measure", "Tom signs the certificate"), "is" and "has" instead of "serves as" and "boasts". Numbers and names from the material. Let length follow content: a short sentence for a fact, a longer one for a condition. Vary the rhythm and section length without forcing fragments, symmetry or a word-count band. End on the next step or the last fact, not on a summary. Headings state something, in sentence case. Use a list only for items that really are separate.

For persuasive copy, make one primary action clear at a time and explain what follows it. Use real stories and the owner's documented choices when they help; don't invent personal history or blame for earlier failures. A deadline, bonus, guarantee or limited quantity is a business claim and needs support in the material. Suggestions that change the offer stay outside the ready-to-paste copy until confirmed.

Respect hard limits of the format and count them: characters in ad headlines, the subject line of an email, the length the user gave.

## 5. Edit pass

Now open `references/patterns.md`, and for Polish part 2 of `references/polish.md`. Go through the draft and for each problem:

1. quote the span,
2. name the pattern (the heading in the reference),
3. replace it with a fact from the material, simplify it, or delete it.

Deletion is the default for scene-setting openers, summaries, restated benefits and sentences that only say something is important. Keep a short log of what changed; in a rewrite or review it goes into the reply.

## 6. The second wave

After a pattern is removed, the model reaches for its nearest substitute. Look for these in your own edit: "rather than", "less X, more Y" and lists of negations ("No X. No Y.") in place of "not X but Y"; calm praise ("dependable", "thoughtful", "rzetelny", "solidny", "z sercem") in place of ad words; pairs everywhere in place of threes; a colon or a short punchy fragment in place of an em dash; invented round numbers ("in 20 minutes") in place of vague claims. If you find one, go back to the material and write the fact instead.

## 7. Check

- **Swap test.** Would the text still be true with a competitor's name in it? Make that sentence specific or cut it.
- **Could a customer check it?** "Highest quality" can't be checked; "we answer email the same working day" can.
- **So what?** After each feature, does the reader learn what it means for them? Only from the material.
- **Read it aloud.** Would the owner say this to a customer on the phone?
- **Proofread.** Read every word for spelling, endings and agreement. In Polish check the case after prepositions and numbers („w kwietniu”, „5 lat”, „poprawimy suknię”) and that the form of address stays the same. The script doesn't check grammar.
- **Script.** Save the text to a file and run `python3 scripts/check_copy.py FILE` (from this skill's folder). When you wrote from notes or research, save them exactly as given and always pass them with `--facts NOTES`; don't tell the user the text has no invented details unless that check ran and you read the text against the notes yourself. Pass `--baseline ORIGINAL` when you edited someone's text. Fix every ERROR. Fix every WARNING or say why not. Give every CANDIDATE a decision in your reply: cut, replace with which fact, or keep because. The script finds candidates; it doesn't say whether the text is good, and a clean run proves nothing on its own. Where you can't run scripts or write files, do the same checks by reading against `references/patterns.md` and tell the user the script didn't run.

## Output

The text first, ready to paste. Then only what the user needs to act on: what you removed or changed (for a rewrite, edit or review), questions for the user (at most four), inferences to confirm with the sentence ready to paste, sentences that rest on general knowledge, and decisions on any CANDIDATE you kept. Mention the voice decision only when it is a choice the user should know about, such as ty or Państwo. Keep these notes as short as the job allows (for a few lines of copy, a few lines of notes and the questions), and don't explain what the user can see in the text. The notes follow the same rules as the text: no em dash, no ad words, Polish quotation marks in Polish.
