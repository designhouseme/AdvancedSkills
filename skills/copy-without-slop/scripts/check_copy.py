#!/usr/bin/env python3
# SPDX-License-Identifier: CC-BY-4.0
# © 2026 Design House (https://designhouse.me)
"""Points at places in a text that need a decision. It doesn't judge the text.

Usage: python3 check_copy.py TEXT [--lang pl|en] [--facts FILE] [--baseline FILE] [--json]

TEXT is a .md, .txt or .html file, or - for standard input.
--facts     notes or research the text was written from: every number in the text
            (price, year, time, count, phone) must appear there, otherwise ERROR.
            Quantities written as words are listed as candidates.
--baseline  the original, when the task was editing someone's text: prints how much changed
            and only the candidates the edit introduced.
--json      the findings as a list, for evals.

Levels:
  ERROR      typography and template residue that are wrong in any text, numbers missing
             from --facts. Fix them.
  WARNING    Polish typography and register that are almost always wrong. Fix them or say why not.
  CANDIDATE  a pattern from references/patterns.md or references/polish.md (the name after the
             level is the heading there). Not a failure: give each one a decision in the reply,
             e.g. cut, replace with which fact, or keep because…
  REPORT     numbers only: sentence lengths, how much changed.

A clean run doesn't mean the text is good, and a CANDIDATE doesn't mean it was written by AI.
Standard library only, no network. Exit code: 0 when there are no errors, 1 when there are
errors, 2 when an input file is missing.
"""
import argparse
import difflib
import html.parser
import json
import re
import statistics
import sys
from pathlib import Path

PL_LETTERS = set("ąćęłńóśźżĄĆĘŁŃÓŚŹŻ")
UPPER = "A-ZĄĆĘŁŃÓŚŹŻ"
# Abbreviations after which a period doesn't end a sentence.
ABBR = {"ul", "al", "pl", "tel", "nr", "np", "itp", "itd", "tj", "tzn", "pon", "wt", "śr", "czw", "pt",
        "sob", "ndz", "godz", "min", "ok", "r", "zł", "gr", "mgr", "inż", "dr", "prof", "św", "m.in",
        "e.g", "i.e", "etc", "vs", "mr", "mrs", "ms", "st", "no"}

# Candidate patterns. The id is the heading in references/patterns.md (both languages)
# or references/polish.md (pl only). Keep the three in sync.
# Each entry: (id, languages, regex). Matching is case-insensitive.
PATTERNS = [
    # Quantities in words escape the --facts check of digits, so they are listed for checking.
    ("invented-detail", "en", r"\b(?:hundreds|thousands|dozens|countless|for (?:years|decades)|years of experience|\w+(?:[- ]\w+)? per ?cent|\w+ percent)\b"),
    ("invented-detail", "pl", r"\b(?:setk\w*|setek|tysiąc\w*|tysięcy|dziesiątk\w*|dziesiątek|kilkadziesiąt|kilkaset|kilkanaście lat|kilka(?:naście)? (?:godzin|minut|dni|tygodni|lat)|\w+ procent\w*|od (?:wielu )?lat|wieloletni\w*)\b"),
    # Promises and guarantees: fine when the material states them, invented otherwise.
    ("invented-detail", "en", r"\b(?:guarantee\w*|we promise|lifetime|for decades|for generations|heirloom)\b"),
    ("invented-detail", "pl", r"\b(?:gwarant\w+|gwarancj\w+|obiecujemy|na (?:długie )?lata|dziesięcioleci\w*|na całe życie|dożywotn\w+)\b"),
    ("contrast", "en", r"\b(?:not (?:just|only|merely|simply) [^.!?]{1,60}?,? (?:but|it'?s)|isn'?t (?:just|only) [^.!?]{1,40}?\s*[,;—–-]+\s*it'?s|it'?s not (?:about )?[^.!?]{1,40}?\s*[,;—–-]+\s*it'?s|don'?t just [^.!?]{1,40}?[,;—–-]+ we)\b"),
    ("contrast", "pl", r"\b(?:to nie tylko|nie tylko [^.!?]{1,60}?,? (?:ale|lecz)|nie chodzi o [^.!?]{1,40}?[,;] (?:chodzi|ale)|to coś więcej niż|to nie (?:kolejn\w+|zwykł\w+))"),
    ("contrast-second-wave", "en", r"\b(?:rather than (?:just |merely |simply )?\w+|less (?:like )?(?:an? )?\w+(?: \w+)?,? (?:and )?more (?:like )?)\b"),
    ("contrast-second-wave", "pl", r"\b(?:bardziej [^.!?]{1,30}? niż|zamiast (?:po prostu |tylko )?\w+(?:ć|ać|ić)\b)"),
    ("negation-list", "en", r"(?:\bno \w+(?: \w+)?[.,] no \w+|, no (?:guesswork|guessing|surprises|hassle|stress|fuss)\b)"),
    ("negation-list", "pl", r"(?:\bbez \w+(?: \w+)?[.,] bez \w+|, bez (?:stresu|niespodzianek|zbędnych formalności|ukrytych kosztów)\b)"),
    ("tail", "en", r", (?:ensuring|highlighting|making|allowing|enabling|providing|offering|reflecting|fostering|giving|helping|leaving|creating|delivering|underscoring) [^.!?]{3,}[.!?]"),
    ("tail", "pl", r", (?:\w+ąc)\b [^.!?]{3,}[.!?]"),
    ("significance", "en", r"\b(?:plays? an? (?:key|crucial|pivotal|vital|significant|important) role|stands? as an? testament|testament to|underscores?|pivotal|indelible|cornerstone)\b"),
    ("significance", "pl", r"\b(?:odgrywa\w* (?:kluczow\w+|ważn\w+|istotn\w+) rol\w+|stanowi\w* (?:kluczow\w+|ważn\w+|nieodłączn\w+) (?:element|część)|jest kluczem do)\b"),
    ("importance", "en", r"\b(?:it'?s (?:worth|important to) (?:noting|note|mentioning)|matters because|here'?s why|notably|it is crucial to)\b"),
    ("importance", "pl", r"\b(?:warto (?:zauważyć|podkreślić|pamiętać|wiedzieć|wspomnieć|dodać)|należy pamiętać|kluczowe jest|co ważne|co istotne)\b"),
    ("tradeoff", "en", r"\bwithout (?:sacrificing|compromising|losing|requiring|breaking)\b"),
    ("tradeoff", "pl", r"\b(?:bez kompromisów|bez utraty|bez rezygnacji z)\b"),
    ("ad-words", "en", r"\b(?:elevat\w+|unlock\w*|unleash\w*|seamless\w*|empower\w*|supercharg\w+|transformative|revolutioni[sz]\w+|game.?chang\w+|cutting.edge|state.of.the.art|world.class|best.in.class|next level|one.stop.shop|look no further|tailored|comprehensive|robust|leverag\w+|streamlin\w+|innovative|passion\w*|meticulous\w*|curated|journey|delve|tapestry|vibrant|nestled|in the heart of|hassle.free|effortless\w*|peace of mind|top.quality|high.quality|exceptional|unparalleled|trusted partner|second to none|crafted with)\b"),
    ("ad-words", "pl", r"\b(?:kompleksow\w+|innowacyjn\w+|dedykowan\w+|profesjonaln\w+|najwyższ\w+ jakości|wysokiej jakości|z pasją|pasj\w+|wyjątkow\w+|unikaln\w+|holistyczn\w+|synergi\w+|bezproblemow\w+|indywidualn\w+ podejści\w+|szyt\w+ na miarę|od A do Z|na (?:jeszcze )?wyższy poziom|odkryj\w*|uwolnij|zanurz się|na każdym etapie|w sercu \w+|z sercem|z zaangażowaniem|premium|bezkompromisow\w+|niepowtarzaln\w+|kompletn\w+ obsług\w+|doświadczon\w+ zesp\w+|wieloletni\w+ doświadczeni\w+|szerok\w+ (?:zakres|gam\w+|ofert\w+)|bogat\w+ ofert\w+|najlepsz\w+|nr 1|tradycja spotyka)\b"),
    ("calm-praise", "en", r"\b(?:deliberate(?:ly)?|steady|measured|dependable|thoughtful(?:ly)?|meaningful|genuine(?:ly)?|reliable)\b"),
    ("calm-praise", "pl", r"\b(?:rzeteln\w+|solidn\w+|sprawdzon\w+|fachow\w+|przemyślan\w+|staranni\w+|starann\w+|niezawodn\w+)\b"),
    ("opener", "en", r"(?:^|[.!?]\s+)(?:in today'?s|in a world where|whether you'?re|look no further|welcome to|are you looking for|have you ever|discover)\b"),
    ("opener", "pl", r"(?:^|[.!?]\s+)(?:w dzisiejszych czasach|w dzisiejszym \w*\s*świecie|w erze|niezależnie od tego, czy|witamy|szukasz|czy wiesz, że|w tym artykule|nadszedł czas)\b"),
    ("closer", "en", r"\b(?:in conclusion|to sum up|ultimately,|ready to [^.!?]{1,40}\?|don'?t hesitate|feel free to|contact us today|what are you waiting for)"),
    ("closer", "pl", r"(?:\b(?:podsumowując|reasumując|w skrócie,|nie czekaj|nie zwlekaj|skontaktuj się z nami już dziś|gotow[ya] na [^.!?]{1,40}\?|na co czekasz|zaufaj profesjonalist\w+|zasługuje na)|zapraszamy(?: do kontaktu)?\s*!)"),
    ("reveal", "en", r"\b(?:the (?:result|catch|best part|secret|answer|truth)|why)\?\s+\S"),
    ("reveal", "pl", r"\b(?:efekt|rezultat|haczyk|sekret|odpowiedź|dlaczego)\?\s+\S"),
    ("copula", "en", r"\b(?:serves as|stands as|boasts|acts as)\b"),
    ("copula", "pl", r"\b(?:stanowi\w*|szczyci się|może pochwalić się|pełni rolę)\b"),
    ("vague-proof", "en", r"\b(?:(?:many|most|our) (?:clients|customers) (?:say|agree|love|praise)|experts (?:say|agree)|trusted by (?:thousands|hundreds|many)|studies show|countless)\b"),
    ("vague-proof", "pl", r"\b(?:klienci (?:podkreślają|chwalą|doceniają|cenią)|wielu klientów|zaufał\w* nam (?:setki|tysiące)|eksperci (?:twierdzą|zgodnie)|badania pokazują)\b"),
    ("chat-residue", "en", r"(?:^|\n)\s*(?:certainly!|sure!|here'?s (?:a|the|your)|i hope this helps|great question)"),
    ("chat-residue", "pl", r"(?:^|\n)\s*(?:oczywiście!|jasne!|oto (?:propozycja|tekst|wersja)|mam nadzieję, że to pomoże)"),
    ("nominal", "en", r"\b(?:conduct|perform|carry out|provide|make|undertake) (?:an? |the )?\w+(?:tion|ment|ance|ence)\b"),
    ("nominal", "pl", r"\b(?:dokon\w+|przeprowadz\w+|udziel\w+|dokonywa\w+) (?:\w+ )?\w+(?:nia|cji|ści|nie)\b"),
    ("impersonal", "pl", r"\b(?:wykonano|zrealizowano|zaprojektowano|przeprowadzono|zastosowano|wykorzystano|zapewniono|stworzono|zaleca się|(?:został|została|zostało|zostały|zostali|zostanie|zostaną) \w+(?:ny|na|ne|ni|ty|ta|te|ci))\b"),
    ("calque", "pl", r"\b(?:na koniec dnia|adresow\w+ (?:problem|potrzeb)\w*|podj\w+ akcj\w+|dostarcza\w* (?:wartość|rezultat\w*|wynik\w*)|aplikow\w+|destynacj\w+|jako (?:właściciel|ekspert|specjalista)\w*,)"),
    ("intro-comma", "pl", r"(?:^|[.!?]\s+)(?:dodatkowo|ponadto|co więcej|ostatecznie|finalnie|jednak),"),
    ("gendered-you", "pl", r"\b(?:\w+łeś|jesteś (?:zainteresowany|gotowy|pewny|ciekawy)|gotowy na|\w+y/a|\w+\(a\))\b"),
]

LABELS = (r"(?:about us|our services|services|why choose us|our values|our team|contact us|o nas|usługi|"
          r"nasze usługi|oferta|dlaczego my|nasze wartości|nasz zespół|kontakt)\W*")
FACT_IGNORE = re.compile(r"^\d$")  # single digits (list numbering, "1 dzień") aren't checked


def read(path):
    if path == "-":
        return sys.stdin.read()
    p = Path(path)
    if not p.is_file():
        print(f"ERROR: file not found: {path}")
        sys.exit(2)
    return p.read_text(encoding="utf-8")


class _Text(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts, self.skip = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1
        elif tag in ("p", "br", "li", "h1", "h2", "h3", "h4", "div", "section", "td", "button", "a"):
            self.parts.append("\n")
        if tag in ("h1", "h2", "h3", "h4"):
            self.parts.append("# ")

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def plain_lines(raw, name):
    """Returns [(line_no, text, is_heading)] with markdown or HTML markup removed."""
    if name.endswith((".html", ".htm")):
        parser = _Text()
        parser.feed(raw)
        raw = "".join(parser.parts)
    out, fence = [], False
    for no, line in enumerate(raw.splitlines(), 1):
        if line.lstrip().startswith("```"):
            fence = not fence
            continue
        if fence or not line.strip():
            continue
        heading = bool(re.match(r"\s*#{1,6}\s", line)) or bool(re.fullmatch(r"\s*\*\*[^*]+\*\*\s*", line))
        text = re.sub(r"^\s*(#{1,6}\s+|>\s*|[-*+]\s+|\d+[.)]\s+)", "", line)
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
        text = re.sub(r"[*`]{1,3}|(?<!\w)_{1,3}|_{1,3}(?!\w)", "", text).strip()
        if text:
            out.append((no, text, heading))
    return out


def detect_lang(text):
    letters = [c for c in text if c.isalpha()]
    if letters and sum(c in PL_LETTERS for c in letters) / len(letters) >= 0.005:
        return "pl"
    words = re.findall(r"\w+", text.lower())
    pl = sum(w in {"i", "w", "z", "na", "się", "że", "nie", "do", "jest", "oraz"} for w in words)
    en = sum(w in {"the", "and", "of", "to", "is", "we", "you", "for", "with", "our"} for w in words)
    return "pl" if pl > en else "en"


def sentences(lines):
    """Splits body lines into sentences, respecting the abbreviations in ABBR."""
    out = []
    for no, text, heading in lines:
        if heading:
            continue
        start = 0
        for m in re.finditer(rf"[.!?…]+[”\"»)]?\s+(?=[{UPPER}0-9„\"(])", text):
            prev = re.findall(r"([\w.]+)\.?$", text[start:m.start() + 1])
            if prev and prev[-1].lower().rstrip(".") in ABBR:
                continue
            out.append((no, text[start:m.end()].strip()))
            start = m.end()
        if text[start:].strip():
            out.append((no, text[start:].strip()))
    return [(no, s) for no, s in out if re.search(r"\w", s)]


def outside_quotes(text, pos):
    """True when position pos isn't inside „…”, "…" or “…” on the same line."""
    before = text[:pos]
    return before.count("„") <= before.count("”") and before.count('"') % 2 == 0 and before.count("“") <= before.count("”")


def check(lines, lang, facts=None):
    """Returns findings as dicts: level, rule, line, excerpt, note."""
    found = []

    def add(level, rule, no, excerpt, note=""):
        found.append({"level": level, "rule": rule, "line": no, "excerpt": excerpt[:70], "note": note})

    for no, text, heading in lines:
        if "—" in text:
            add("ERROR", "typography.em-dash", no, text, "use a period, comma, colon or parentheses; in Polish a range takes an unspaced en dash")
        if re.search(r"\[(?:company name|nazwa firmy|name|imię|xx+)\]|lorem ipsum|\{\{|\bTODO\b|\bXXX\b", text, re.I):
            add("ERROR", "template.residue", no, text, "a placeholder left in the text")
        if "..." in text:
            add("WARNING", "typography.ellipsis", no, text, "use … (one character)")
        if lang == "pl":
            if re.search(r'"[^"\n]+"|“[^”\n]+”', text):
                add("ERROR", "typography.quotes", no, text, "Polish quotation marks are „…”, nested »…«")
            if re.search(r"\S - \S", text):
                add("WARNING", "typography.hyphen-as-dash", no, text, "a dash between words is an en dash with spaces ( – ), never a hyphen")
            for m in re.finditer(r"(?<![\d-])(\d{1,2}(?::\d{2})?)-(\d{1,2}(?::\d{2})?)(?![\d-])", text):
                if not re.fullmatch(r"\d{2}-\d{3}", text[m.start():m.end() + 1].strip()):
                    add("WARNING", "typography.range", no, m.group(0), "a range takes an unspaced en dash: 8–16, 7:00–17:00")
            if re.search(rf"(?<=[a-ząćęłńóśźż,] )(?:Nasz\w*|My|Nam|Nas|Swoj\w*|Swój)\b", text):
                add("WARNING", "capital-we", no, text, "first-person pronouns are never capitalised mid-sentence")
            if heading and len(text.split()) >= 3:
                rest = text.split()[1:]
                caps = [w for w in rest if w[0].isupper() and not w.isupper()]
                if len(caps) >= 2 and len(caps) >= len(rest) / 2:
                    add("WARNING", "title-case", no, text, "Polish headings are in sentence case (unless these are proper names)")
        if heading and re.fullmatch(LABELS, text, re.I):
            add("CANDIDATE", "label-heading", no, text, "a label, not a statement; say what the section shows")
        if lang == "en" and heading and len(text.split()) >= 4:
            rest = [w for w in text.split()[1:] if len(w) > 3]
            if rest and all(w[0].isupper() for w in rest):
                add("CANDIDATE", "title-case", no, text, "a heading in Title Case; sentence case reads as written, not generated")
        for m in re.finditer(r"!", text):
            if outside_quotes(text, m.start()):
                add("CANDIDATE", "exclamation", no, text, "keep it only in a customer's or the owner's own words")
                break
        for rule, langs, rx in PATTERNS:
            if lang not in langs:
                continue
            for m in re.finditer(rx, text, re.I):
                add("CANDIDATE", rule, no, m.group(0).strip())

    full = "\n".join(t for _, t, _ in lines)
    if lang == "pl":
        dashes = len(re.findall(r" – ", full))
        sections = max(1, sum(h for _, _, h in lines))
        if dashes > sections:
            add("WARNING", "typography.dash-count", 0, f"{dashes} spaced en dashes, {sections} section(s)", "at most one per section; prefer a period, comma or colon")
        if len(re.findall(r"\bwarto\b", full, re.I)) > 1:
            add("CANDIDATE", "importance", 0, "„warto” more than once", "keep at most one per text")
        formal = re.search(r"\b(?:Państw\w*|Pan\b|Pani\b)", full)
        informal = re.search(r"\b(?:ty|ci|cię|ciebie|tobie|twój|twoj\w+|masz|chcesz|możesz|potrzebujesz|szukasz|zadzwoń|napisz|sprawdź|umów|zapisz)\b", full, re.I)
        if formal and informal:
            add("WARNING", "register-mix", 0, f"{formal.group(0)} … {informal.group(0)}", "one form of address throughout: ty or Państwo")
        caps_you = re.findall(rf"(?<=[a-ząćęłńóśźż,] )(?:Ty|Ci|Cię|Ciebie|Tobie|Twój|Twoj\w+|Wy|Was|Wam|Wasz\w*)\b", full)
        if caps_you:
            add("CANDIDATE", "capital-you", 0, ", ".join(sorted(set(caps_you))), "capitalised „Ty/Twój” is optional in ads and reads like a letter on a page; choose and keep one")

    sents = sentences(lines)
    limit = 20 if lang == "pl" else 25
    for no, s in sents:
        n = len(re.findall(r"\w+", s))
        if n > limit:
            add("CANDIDATE", "long-sentence", no, s, f"{n} words; split it where the thought splits")
    run = []
    for no, s in sents + [(0, "x " * 10)]:
        if len(re.findall(r"\w+", s)) <= 4:
            run.append((no, s))
            continue
        if len(run) >= 3:
            add("CANDIDATE", "fragments", run[0][0], " ".join(x for _, x in run), f"{len(run)} clipped sentences in a row")
        run = []
    firsts = [(no, (re.findall(r"\w+", s) or [""])[0].lower()) for no, s in sents]
    for i in range(len(firsts) - 2):
        if firsts[i][1] and firsts[i][1] == firsts[i + 1][1] == firsts[i + 2][1]:
            add("CANDIDATE", "same-opener", firsts[i][0], firsts[i][1], "three sentences in a row start with the same word")
            break

    if facts is not None:
        norm = lambda s: re.sub(r"(?<=\d)[\s  ](?=\d{3}\b)", "", s)
        known = set(re.findall(r"\d+", norm(facts)))
        for no, text, _ in lines:
            for num in re.findall(r"\d+", norm(text)):
                if not FACT_IGNORE.match(num) and num not in known:
                    add("ERROR", "facts.number", no, text, f"{num} isn't in the facts; remove it or ask for it")
    return found, sents


def report(sents):
    lengths = [len(re.findall(r"\w+", s)) for _, s in sents]
    if not lengths:
        return "no sentences"
    sd = statistics.pstdev(lengths) if len(lengths) > 1 else 0
    return (f"sentences {len(lengths)}, words {sum(lengths)}, sentence length mean "
            f"{statistics.mean(lengths):.1f}, sd {sd:.1f}, min {min(lengths)}, max {max(lengths)}")


def plural(n, word):
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("text")
    ap.add_argument("--lang", choices=("pl", "en"))
    ap.add_argument("--facts")
    ap.add_argument("--baseline")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    raw = read(args.text)
    lines = plain_lines(raw, args.text)
    lang = args.lang or detect_lang(raw)
    facts = read(args.facts) if args.facts else None
    found, sents = check(lines, lang, facts)
    extra = [f"REPORT: language {lang}; {report(sents)}"]

    if args.baseline:
        base_raw = read(args.baseline)
        base_lines = plain_lines(base_raw, args.baseline)
        before = {(f["rule"], f["excerpt"].lower()) for f in check(base_lines, lang)[0]}
        found = [f for f in found if f["level"] != "CANDIDATE" or (f["rule"], f["excerpt"].lower()) not in before]
        old = re.findall(r"\w+", " ".join(t for _, t, _ in base_lines).lower())
        new = re.findall(r"\w+", " ".join(t for _, t, _ in lines).lower())
        kept = sum(b.size for b in difflib.SequenceMatcher(None, old, new, autojunk=False).get_matching_blocks())
        changed = 1 - kept / max(1, len(old))
        extra.append(f"REPORT: {changed:.0%} of the original words changed or removed; {len(new)} words now, {len(old)} before")
        if changed > 0.3:
            found.append({"level": "WARNING", "rule": "edit.too-much", "line": 0, "excerpt": f"{changed:.0%} changed",
                          "note": "if the task was a light edit of someone's own text, this rewrites their voice"})

    if args.json:
        print(json.dumps({"language": lang, "findings": found, "report": extra}, ensure_ascii=False, indent=2))
    else:
        order = {"ERROR": 0, "WARNING": 1, "CANDIDATE": 2}
        for f in sorted(found, key=lambda f: (order[f["level"]], f["line"])):
            where = f"L{f['line']} " if f["line"] else ""
            note = f"; {f['note']}" if f["note"] else ""
            print(f"{f['level']}: {where}{f['rule']} \"{f['excerpt']}\"{note}")
        for line in extra:
            print(line)
        counts = {lvl: sum(f["level"] == lvl for f in found) for lvl in order}
        print(f"Result: {plural(counts['ERROR'], 'error')}, {plural(counts['WARNING'], 'warning')}, "
              f"{plural(counts['CANDIDATE'], 'candidate')}. Candidates aren't failures: "
              "give each one a decision (cut, replace with which fact, keep because…).")
    sys.exit(1 if any(f["level"] == "ERROR" for f in found) else 0)


if __name__ == "__main__":
    main()
