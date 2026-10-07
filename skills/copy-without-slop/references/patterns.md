# Patterns for the edit pass

Read this after the draft exists (point 5 in SKILL.md), never before. Each heading is also the name `check_copy.py` prints. For each pattern: what it looks like, what to do instead, the substitute that tends to replace it, and when it's fine to keep.

Single words matter less than structures: word habits change with every model version, structures stay. One "comprehensive" in a policy name is fine; three ad words in a paragraph are a pattern.

## Content

### invented-detail
Looks like: a number, year, guarantee, qualification, review, price or use case that isn't in the material, also in words: "ninety per cent of leaks", „setki realizacji”, „kilka godzin pracy”, „od lat”.
Instead: remove it, or ask for it (`[MISSING: …]`). The script checks digits against `--facts` and lists quantities in words as candidates.
Second wave: vaguer invention that sounds modest ("for years", "a handful of", "most of my work").
Not this: general knowledge that is true of every business or product with the given fact ("end grain is gentler on knife edges"). It may explain a fact; say in the reply that it's general.

### inference
Looks like: a benefit or reason the material makes likely but doesn't state ("so you can drop the car off on your way to work").
Instead: list it for the user to confirm, with the sentence ready.

### generic
Looks like: a sentence that stays true with a competitor's name in it ("we put customers first", „stawiamy na jakość”).
Instead: the fact only this business has, or cut the sentence. If there is no such fact, say so to the user.

### vague-proof
Looks like: "customers say", "trusted by hundreds", "experts agree" / „klienci podkreślają”, „zaufały nam setki firm”.
Instead: a named review quoted as written, a number with its source, or nothing.

### polished-quote
Looks like: a testimonial that sounds like the rest of the page, with added adjectives, a full name or a job title the source didn't give.
Instead: the customer's own words, shortened only with an ellipsis, credited as in the source. Rough wording is what makes a quote believable.

## Structures

### contrast
Looks like: "It's not just X, it's Y", "We don't just X, we Y" / „To nie tylko X, to Y”, „Nie chodzi o X”. It argues with a claim nobody made.
Instead: say Y with the fact behind it.
Keep when: readers really believe X (it shows in reviews or questions), or it's a refusal that positions the business ("We don't fit laminate, only solid wood").

### contrast-second-wave
Looks like: "Y rather than X", "less X, more Y" / „bardziej X niż Y”, „zamiast X”. The same move after "not X but Y" was removed.
Instead: as for contrast. Keep "rather than" when both halves are facts the reader needs.

### negation-list
Looks like: "No hidden fees. No stress. Just results." / „Bez stresu. Bez niespodzianek.”, a trailing ", no guesswork".
Instead: say what happens, in order. State one real absence once, where it answers a worry ("No card needed to book").

### triad
Looks like: three adjectives or three short parallel phrases ("fast, friendly and reliable", „szybko, sprawnie i profesjonalnie”).
Instead: the one quality you can prove, with the proof. As many items as the content has.
Keep when: three real, different things (three services, three districts).
Second wave: pairs everywhere.

### tail
Looks like: a sentence that is finished, then ", ensuring…", ", making it…", „…, zapewniając pełen komfort”, „…, dbając o każdy szczegół”.
Instead: end at the claim. If the tail carries a fact, make it its own sentence with a subject.

### significance
Looks like: "plays a key role", "a testament to", "cornerstone" / „odgrywa kluczową rolę”, „stanowi nieodłączny element”.
Instead: the consequence as a fact, or cut.

### importance
Looks like: "It's worth noting", "Here's why", "matters because" / „Warto zauważyć, że”, „Kluczowe jest”, „Co ważne,”.
Instead: the fact on its own. The reader decides what's important.
Keep: one „warto” in a text is ordinary Polish.

### tradeoff
Looks like: "fast without compromising quality" / „bez kompromisów”, „szybko, a przy tym starannie”.
Instead: the real condition ("Stairs take 6–8 weeks because the wood rests in the workshop first") or one benefit.

### reveal
Looks like: a question answered at once: "The result? 30% faster." / „Efekt? Oszczędność czasu.”, also pairs like "Toothache? … Nervous? …".
Instead: state it. Questions belong in an FAQ, and only real ones.

### opener
Looks like: "In today's fast-paced world", "Whether you're X or Y", "Welcome to", "Are you looking for" / „W dzisiejszych czasach”, „Niezależnie od tego, czy”, „Witamy”, „Szukasz…?”, „Nadszedł czas”.
Instead: start with the reader's situation or the offer.

### closer
Looks like: "In conclusion", "Ready to…?", "Don't hesitate to contact us", a closing summary / „Podsumowując”, „Nie czekaj”, „Zapraszamy!” on its own, „Twój dach zasługuje na…”.
Instead: end on the last fact or the concrete next step, with the number or link.

### copula
Looks like: "serves as", "stands as", "boasts" / „stanowi”, „szczyci się”, „może pochwalić się”.
Instead: is, has, does / jest, ma, robi.

### nominal
Looks like: "carry out an inspection", "provide assistance" / „dokonać zakupu”, „przeprowadzić analizę”, „udzielić odpowiedzi”.
Instead: the verb, with someone doing it: "we inspect", „kupić”, „przeanalizujemy”, „odpowiemy”.

## Words

### ad-words
Looks like: elevate, unlock, seamless, empower, transform, cutting-edge, tailored, comprehensive, passionate, top quality, in the heart of / kompleksowy, innowacyjny, dedykowany, profesjonalny, najwyższej jakości, z pasją, wyjątkowy, indywidualne podejście, szyte na miarę, od A do Z.
Instead: the fact the word stands in for. "Comprehensive" becomes the list of what's included; „profesjonalny” becomes the qualification or the step. If there's no fact behind it, cut it.
Keep when: it's a name ("Comprehensive Car Insurance") or the user's own wording in an edit.

### calm-praise
Looks like: dependable, thoughtful, deliberate, steady, genuine / rzetelny, solidny, sprawdzony, fachowy, staranny, z sercem. The second wave of ad words: quieter, still a rating instead of a description.
Instead: the behaviour that earns the word ("we call back the same day").
Keep when: the same sentence carries the fact that proves it.

### mannered
Looks like: a metaphor or flourish where a literal phrase exists ("the beating heart of the neighbourhood", „tradycja spotyka się z nowoczesnością”).
Instead: the literal fact: the address, the method, the year.

### chat-residue
Looks like: "Certainly!", "Here's your…", "I hope this helps" / „Oczywiście!”, „Oto propozycja”, inside the text itself.
Instead: delete. The text starts with its first real sentence.

## Rhythm and form

### long-sentence
Over 25 words in English, over 20 in Polish. Split where the thought splits.

### fragments
Three or more clipped sentences in a row ("Fast. Clean. Done."). Join them into a sentence that says something, except in a deliberately short headline.

### same-opener
Three sentences in a row that start with the same word ("We… We… We…"). Vary by changing what the sentence is about, often to the reader.

### label-heading
"About us", "Services", "Why choose us" / „O nas”, „Usługi”, „Dlaczego my”. A label says what kind of section it is, not what it shows. Write the heading as a statement: "Rewiring flats and houses in Bristol", „Schody robimy 6–8 tygodni”.

### title-case
"Our Kitchen Renovation Services" in a heading. Sentence case: "Kitchens fitted in five days".

### exclamation
Outside a quote. Keep it in a customer's or the owner's own words, where it's theirs; in your own copy the fact carries the energy.

### formatting
Every list item opening with a bold label, bold on every other phrase, emoji as bullets, headings over every two short paragraphs. Use a list for separate items, bold at most once per screen, headings that say something.
