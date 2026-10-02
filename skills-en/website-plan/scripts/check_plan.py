#!/usr/bin/env python3
# SPDX-License-Identifier: CC-BY-4.0
# © 2026 Design House (https://designhouse.me)
"""Checks a website plan against the research register.

Usage: python3 check_plan.py [brief/02-plan.md] [brief/01-research.md]

Checks only the sections with site content (Sections, Hero, Section copy, Contact, FAQ,
Meta, Media). IDs in justifications (e.g. "Rejected", "Gaps") may point to do-not-use
claims, because that's where they document what we're not using.

Standard library only, no network. Exit code: 0 when there are no errors, 1 when there
are errors, 2 when an input file is missing.
"""
import re
import sys
from pathlib import Path

ID = re.compile(r"\b[FVP]\d{3,}\b")
STATUSES = ("do-not-use", "needs-confirmation", "verified")
COPY_SECTIONS = ("sections", "hero", "section copy", "contact", "faq", "meta", "media")


def read(path):
    p = Path(path)
    if not p.is_file():
        print(f"ERROR: file not found: {path}")
        sys.exit(2)
    return p.read_text(encoding="utf-8")


def registry(text):
    """Returns {ID: status} from the register table rows in the research."""
    reg = {}
    for line in text.splitlines():
        m = re.match(r"\s*\|\s*([FVP]\d{3,})\s*\|", line)
        if m:
            status = next((s for s in STATUSES if s in line.lower()), "no status")
            reg[m.group(1)] = status
    return reg


def sections(text):
    """Returns a list of (title, body) for second-level headings."""
    parts = re.split(r"^##\s+(.+)$", text, flags=re.M)
    return [(parts[i].strip(), parts[i + 1]) for i in range(1, len(parts) - 1, 2)]


def plural(n, word):
    """1 error, 2 errors."""
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


def main():
    plan_path = sys.argv[1] if len(sys.argv) > 1 else "brief/02-plan.md"
    research_path = sys.argv[2] if len(sys.argv) > 2 else "brief/01-research.md"
    plan, reg = read(plan_path), registry(read(research_path))
    errors, warnings = [], []

    secs = sections(plan)
    copy = "\n".join(body for title, body in secs if title.lower().startswith(COPY_SECTIONS))
    if not copy:
        warnings.append("no site content sections found (format from SKILL.md); checking the whole file")
        copy = plan
    copy_ids = set(ID.findall(copy))

    for sid in sorted(set(ID.findall(plan))):
        status = reg.get(sid)
        if status is None:
            errors.append(f"{sid} is in the plan but not in the research register")
        elif sid in copy_ids and status == "do-not-use":
            errors.append(f"{sid} has status do-not-use, but the plan uses it in the site content")
        elif sid in copy_ids and status != "verified":
            warnings.append(f"{sid} has status {status}; weaken the claim or mark it for confirmation")

    for line in copy.splitlines():
        if "—" in line:
            errors.append(f"em dash (—) in the site content: \"{line.strip()[:60]}\"; use a period, comma, colon or parentheses")

    meta = next((body for title, body in secs if title.lower().startswith("meta")), "")
    for field, limit in (("title", 60), ("description", 155)):
        m = re.search(rf"^\W*{field}\W*:\s*(.+)$", meta, re.M | re.I)
        if not m:
            warnings.append(f"no {field} field in the Meta section")
        elif len(m.group(1).strip()) > limit:
            errors.append(f"{field} has {len(m.group(1).strip())} characters (limit {limit})")

    table = next((body for title, body in secs if title.lower().startswith("sections")), "")
    rows = [r for r in table.splitlines() if re.match(r"\s*\|\s*\d+\s*\|", r)]
    if rows and not 4 <= len(rows) <= 7:
        warnings.append(f"the plan has {len(rows)} sections (expected 4–7)")
    if len(rows) >= 2 and not ("contact" in rows[-2].lower() and "faq" in rows[-1].lower()):
        warnings.append("contact should be second to last and FAQ last")

    for e in errors:
        print(f"ERROR: {e}")
    for w in warnings:
        print(f"WARNING: {w}")
    print(f"Source IDs checked: {len(set(ID.findall(plan)))}, sections: {len(rows)}. Result: "
          f"{plural(len(errors), 'error')}, {plural(len(warnings), 'warning')}.")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
