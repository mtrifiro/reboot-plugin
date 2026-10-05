#!/usr/bin/env python3
"""Lint reference files against skills/_template.md.

Every reference must carry the navigation frontmatter (step, applies,
always, summary, verified). A reference counts as converted to the
template once it has a "## When you are here" heading; converted
references must also have the seven section headings, exactly once each
and in order. Unconverted ones are counted, not failed, so the lint can
gate CI while conversion is still in progress (pass `--all` to fail on
them too).

Usage:
    tools/lint-references.py           # lint converted files, report progress
    tools/lint-references.py --all     # every reference must be converted
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"

SECTIONS = ("When you are here", "Do this", "Never", "Limits", "Scales as",
            "Errors you will see", "See also")
FIELDS = ("title", "impact", "impactDescription", "tags", "summary", "step",
          "applies", "always", "verified")
NAV_ONLY = ("step", "applies", "always", "summary", "verified")
STEPS = {"shell", "api", "servicer", "auth", "frontend", "tests", "run", "deploy", "any"}
FRONT_DOORS = {"mcp-ui", "web-app", "backend-only"}
WORD_BUDGET = 1500
MAX_SEE_ALSO = 3


def frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.index("\n---", 4)
    data = {}
    for line in text[4:end].splitlines():
        m = re.match(r"^([A-Za-z_]+):\s*(.*?)\s*(#.*)?$", line)
        if m:
            data[m.group(1)] = m.group(2)
    return data, text[end + 4 :]


def lint(path: Path, sections: bool) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    text = path.read_text(encoding="utf-8")
    fm, body = frontmatter(text)

    for f in (FIELDS if sections else NAV_ONLY):
        if f not in fm:
            errors.append(f"frontmatter missing {f}")
    if len(fm.get("summary", "").split()) > 30:
        warnings.append("summary longer than 30 words")
    if fm.get("via") and not (path.parent / fm["via"].strip("\"'")).exists():
        errors.append(f"via points at missing file {fm['via']}")
    if fm.get("step") and fm["step"] not in STEPS:
        errors.append(f"step {fm['step']!r} not in {sorted(STEPS)}")
    applies = {a.strip() for a in fm.get("applies", "").strip("[]").split(",") if a.strip()}
    if not applies or applies - FRONT_DOORS:
        errors.append(f"applies must be a non-empty subset of {sorted(FRONT_DOORS)}")
    if fm.get("always") not in ("true", "false"):
        errors.append("always must be true or false")
    if path.name.startswith("patterns-") and fm.get("step") not in ("any", None):
        warnings.append("patterns-* files normally use step: any")
    if not sections:
        return errors, warnings

    # Strip fenced code so `## ` inside examples isn't read as a heading.
    prose = re.sub(r"^(```|~~~).*?^\1", "", body, flags=re.S | re.M)
    headings = re.findall(r"^## (.+?)\s*$", prose, flags=re.M)
    present = [h for h in headings if h in SECTIONS]
    for s in SECTIONS:
        n = present.count(s)
        if n == 0:
            errors.append(f"missing section '## {s}'")
        elif n > 1:
            errors.append(f"section '## {s}' appears {n} times")
    if len(set(present)) == len(SECTIONS) and present != list(SECTIONS):
        errors.append("sections out of order: " + " / ".join(present))
    extra = [h for h in headings if h not in SECTIONS]
    if extra:
        errors.append("unexpected ## headings (use ### inside a section): " + ", ".join(extra))

    see_also = re.search(r"^## See also\s*$(.*?)(?=^## |\Z)", prose, flags=re.S | re.M)
    if see_also:
        links = re.findall(r"^\s*[-*] ", see_also.group(1), flags=re.M)
        if len(links) > MAX_SEE_ALSO:
            errors.append(f"See also has {len(links)} links (max {MAX_SEE_ALSO})")
        for target in re.findall(r"\]\(([^)#]+)", see_also.group(1)):
            if not target.startswith("http") and not (path.parent / target).resolve().exists():
                errors.append(f"See also link to missing file {target}")

    words = len(body.split())
    if words > WORD_BUDGET:
        warnings.append(f"{words} words (budget {WORD_BUDGET})")
    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()

    refs = sorted(SKILLS.glob("*/references/*.md"))
    refs = [r for r in refs if not r.name.startswith("_")]
    converted, pending, failures = [], [], 0
    for path in refs:
        text = path.read_text(encoding="utf-8")
        (converted if re.search(r"^## When you are here\s*$", text, re.M) else pending).append(path)

    for path in refs:
        errors, warnings = lint(path, sections=path in converted)
        rel = path.relative_to(ROOT)
        for e in errors:
            print(f"{rel}: error: {e}")
        for w in warnings:
            print(f"{rel}: warning: {w}")
        failures += bool(errors)

    print(f"\n{len(converted)}/{len(refs)} references converted; "
          f"{failures} with errors")
    if args.all and pending:
        for path in pending:
            print(f"{path.relative_to(ROOT)}: not converted")
        return 1
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
