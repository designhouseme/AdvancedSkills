#!/usr/bin/env python3
# SPDX-License-Identifier: CC-BY-4.0
# © 2026 Design House (https://designhouse.me)
"""Sprawdza plan strony względem rejestru researchu.

Użycie: python3 sprawdz_plan.py [brief/02-plan.md] [brief/01-research.md]

Sprawdza tylko sekcje z treścią strony (Sekcje, Hero, Teksty, Kontakt, FAQ, Meta, Media).
ID w uzasadnieniach (np. „Odrzucone”, „Braki”) mogą wskazywać twierdzenia do-not-use,
bo tam opisują, czego nie używamy.

Tylko biblioteka standardowa, bez sieci. Kod wyjścia: 0 gdy brak błędów, 1 gdy są błędy,
2 gdy brakuje pliku wejściowego.
"""
import re
import sys
from pathlib import Path

ID = re.compile(r"\b[FVP]\d{3,}\b")
STATUSES = ("do-not-use", "needs-confirmation", "verified")
COPY_SECTIONS = ("sekcje", "hero", "teksty", "kontakt", "faq", "meta", "media")


def read(path):
    p = Path(path)
    if not p.is_file():
        print(f"BŁĄD: nie ma pliku {path}")
        sys.exit(2)
    return p.read_text(encoding="utf-8")


def registry(text):
    """Zwraca {ID: status} z wierszy tabeli rejestru w researchu."""
    reg = {}
    for line in text.splitlines():
        m = re.match(r"\s*\|\s*([FVP]\d{3,})\s*\|", line)
        if m:
            status = next((s for s in STATUSES if s in line.lower()), "brak statusu")
            reg[m.group(1)] = status
    return reg


def sections(text):
    """Zwraca listę (tytuł, treść) dla nagłówków drugiego poziomu."""
    parts = re.split(r"^##\s+(.+)$", text, flags=re.M)
    return [(parts[i].strip(), parts[i + 1]) for i in range(1, len(parts) - 1, 2)]


def pl(n, one, few, many):
    """Polska odmiana: 1 błąd, 2 błędy, 5 błędów."""
    if n == 1:
        return f"{n} {one}"
    if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14):
        return f"{n} {few}"
    return f"{n} {many}"


def main():
    plan_path = sys.argv[1] if len(sys.argv) > 1 else "brief/02-plan.md"
    research_path = sys.argv[2] if len(sys.argv) > 2 else "brief/01-research.md"
    plan, reg = read(plan_path), registry(read(research_path))
    errors, warnings = [], []

    secs = sections(plan)
    copy = "\n".join(body for title, body in secs if title.lower().startswith(COPY_SECTIONS))
    if not copy:
        warnings.append("nie znaleziono sekcji z treścią strony (format z SKILL.md); sprawdzam cały plik")
        copy = plan
    copy_ids = set(ID.findall(copy))

    for sid in sorted(set(ID.findall(plan))):
        status = reg.get(sid)
        if status is None:
            errors.append(f"{sid} jest w planie, ale nie ma go w rejestrze researchu")
        elif sid in copy_ids and status == "do-not-use":
            errors.append(f"{sid} ma status do-not-use, a plan używa go w treści strony")
        elif sid in copy_ids and status != "verified":
            warnings.append(f"{sid} ma status {status}; osłab twierdzenie albo oznacz do potwierdzenia")

    for line in copy.splitlines():
        if "—" in line:
            errors.append(f"długa pauza (—) w treści strony: „{line.strip()[:60]}”; użyj półpauzy (–), kropki albo przecinka")

    meta = next((body for title, body in secs if title.lower().startswith("meta")), "")
    for field, limit in (("title", 60), ("description", 155)):
        m = re.search(rf"^\W*{field}\W*:\s*(.+)$", meta, re.M | re.I)
        if not m:
            warnings.append(f"brak pola {field} w sekcji Meta")
        elif len(m.group(1).strip()) > limit:
            errors.append(f"{field} ma {len(m.group(1).strip())} znaków (limit {limit})")

    table = next((body for title, body in secs if title.lower().startswith("sekcje")), "")
    rows = [r for r in table.splitlines() if re.match(r"\s*\|\s*\d+\s*\|", r)]
    if rows and not 4 <= len(rows) <= 7:
        warnings.append(f"plan ma {len(rows)} sekcji (oczekiwane 4–7)")
    if len(rows) >= 2 and not ("kontakt" in rows[-2].lower() and "faq" in rows[-1].lower()):
        warnings.append("kontakt powinien być przedostatni, a FAQ ostatnie")

    for e in errors:
        print(f"BŁĄD: {e}")
    for w in warnings:
        print(f"UWAGA: {w}")
    print(f"Sprawdzono Source ID: {len(set(ID.findall(plan)))}, sekcje: {len(rows)}. Wynik: "
          f"{pl(len(errors), 'błąd', 'błędy', 'błędów')}, {pl(len(warnings), 'uwaga', 'uwagi', 'uwag')}.")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
