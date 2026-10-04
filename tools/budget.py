#!/usr/bin/env python3
"""Measure the reading cost of a build, per front door.

An agent that follows the skills exactly reads a fixed set of SKILL.md
files plus every reference the builder's reading list names, before
it writes application code. Everything it reads is re-sent on every
later turn, so this number is a release metric: it is printed on every
run and, with `--ceiling`, fails when a front door exceeds its budget.

Two sources for the reading list, picked automatically:

* frontmatter: once every reference carries `step:` / `applies:` / `always:`
  frontmatter (see skills/_template.md), the list is every reference
  with `always: true` plus every reference whose `step` is a build
  step and whose `applies` includes the front door.
* legacy: otherwise, the list is parsed from the builder SKILL.md's
  "Which References to Read, and When" section, grouped by its
  "**Before the …**" headings. A mention whose sentence says "only
  when", "whenever", "for custom steps" and the like counts as
  conditional; the "minimal" column excludes those.

Usage:
    tools/budget.py                    # table for every front door
    tools/budget.py --json
    tools/budget.py --ceiling 30000    # exit 1 if any minimal path exceeds it
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"

FRONT_DOORS = ("mcp-ui", "web-app")

# SKILL.md files every build of a front door reads in full, in order:
# the router, the builder, the foundation, the feature workflow and run.
FIXED_SKILLS = {
    "mcp-ui": ["app", "mcp-ui", "python", "feature", "run"],
    "web-app": ["app", "web-app", "python", "feature", "run"],
}

BUILD_STEPS = ("shell", "api", "servicer", "auth", "frontend", "tests")

READING_LIST_HEADING = "## Which References to Read, and When"

CONDITIONAL = re.compile(
    r"\bonly when\b|\bwhenever\b|\bfor custom steps\b|\bwhen you pick\b"
    r"|\bwhen the API declares\b|\bwhen a widget\b|\bwhen none of\b"
    r"|\bacting on the user's behalf\b|\bcalling an external\b"
    r"|\bwriting your own\b",
    re.IGNORECASE,
)

REF = re.compile(
    r"(?:\.\./)?(?:(?P<skill>[a-z-]+)/)?references/"
    r"(?P<name>[A-Za-z0-9_-]*(?:\{[^}]+\})?[A-Za-z0-9_-]*)\.md"
)
BARE_REF = re.compile(r"`(?P<name>[a-z]+-[a-z0-9-]+)\.md`")


def words(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").split())


def expand(name: str) -> list[str]:
    m = re.search(r"\{([^}]+)\}", name)
    if not m:
        return [name]
    head, tail = name[: m.start()], name[m.end() :]
    return [head + part.strip() + tail for part in m.group(1).split(",")]


def frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end < 0:
        return {}
    out: dict = {}
    for line in text[4:end].splitlines():
        if ":" not in line or line.startswith(" "):
            continue
        key, value = line.split(":", 1)
        value = value.split("#", 1)[0].strip()
        if value.startswith("[") and value.endswith("]"):
            out[key.strip()] = [v.strip() for v in value[1:-1].split(",") if v.strip()]
        elif value in ("true", "false"):
            out[key.strip()] = value == "true"
        else:
            out[key.strip()] = value
    return out


def all_references() -> list[Path]:
    return sorted(p for p in SKILLS.glob("*/references/*.md") if not p.name.startswith("_"))


@dataclass
class Item:
    path: Path
    step: str
    conditional: bool

    @property
    def rel(self) -> str:
        return str(self.path.relative_to(SKILLS))


@dataclass
class Report:
    front_door: str
    source: str
    fixed: list[tuple[str, int]] = field(default_factory=list)
    items: list[Item] = field(default_factory=list)
    unresolved: list[str] = field(default_factory=list)

    def by_step(self) -> dict[str, list[Item]]:
        out: dict[str, list[Item]] = {}
        for item in self.items:
            out.setdefault(item.step, []).append(item)
        return out

    def total(self, minimal: bool) -> int:
        fixed = sum(n for _, n in self.fixed)
        refs = sum(
            words(i.path) for i in self.items if not (minimal and i.conditional)
        )
        return fixed + refs


def resolve(skill: str | None, name: str, builder: str) -> Path | None:
    candidates = []
    if skill:
        candidates.append(SKILLS / skill / "references" / f"{name}.md")
    else:
        candidates.append(SKILLS / builder / "references" / f"{name}.md")
        candidates.append(SKILLS / "python" / "references" / f"{name}.md")
    for c in candidates:
        if c.exists():
            return c
    return None


def chunks(section: str) -> list[tuple[str, str]]:
    """Split a reading-list section into (step, chunk) pairs.

    A chunk is one bullet (with its continuation lines) or one
    sentence of a prose paragraph.
    """
    step = "preamble"
    out: list[tuple[str, str]] = []
    bullet: list[str] = []
    prose: list[str] = []

    def flush() -> None:
        if bullet:
            out.append((step, " ".join(bullet)))
            bullet.clear()
        if prose:
            for sentence in re.split(r"(?<=[.;])\s+", " ".join(prose)):
                out.append((step, sentence))
            prose.clear()

    for line in section.splitlines():
        heading = re.match(r"\*\*Before (?:the |running )?([^*:(]+)", line)
        if heading:
            flush()
            step = heading.group(1).strip().rstrip(":").lower()
            prose.append(line[heading.end() :])
        elif line.startswith("- "):
            flush()
            bullet.append(line[2:])
        elif line.startswith("  ") and bullet:
            bullet.append(line.strip())
        elif line.startswith(">"):
            flush()  # callouts name references to avoid, not to read
        elif line.strip():
            if bullet:
                flush()
            if step != "preamble":
                prose.append(line.strip())
        else:
            flush()
    flush()
    return out


def legacy(front_door: str) -> Report:
    report = Report(front_door, "legacy")
    text = (SKILLS / front_door / "SKILL.md").read_text(encoding="utf-8")
    start = text.find(READING_LIST_HEADING)
    end = text.find("\n## ", start + len(READING_LIST_HEADING))
    section = text[start:end]
    seen: set[Path] = set()
    for step, chunk in chunks(section):
        if step == "preamble":
            continue
        conditional = bool(CONDITIONAL.search(chunk))
        names = [(m.group("skill"), m.group("name")) for m in REF.finditer(chunk)]
        names += [(None, m.group("name")) for m in BARE_REF.finditer(chunk)]
        for skill, raw in names:
            for name in expand(raw):
                path = resolve(skill, name, front_door)
                if path is None:
                    report.unresolved.append(f"{skill or '?'}/references/{name}.md")
                    continue
                if path in seen:
                    continue
                seen.add(path)
                report.items.append(Item(path, step, conditional))
    return report


def from_frontmatter(front_door: str) -> Report:
    report = Report(front_door, "frontmatter")
    for path in all_references():
        fm = frontmatter(path)
        applies = fm.get("applies", [])
        if fm.get("always"):
            report.items.append(Item(path, "always", False))
        elif fm.get("step") in BUILD_STEPS and front_door in applies:
            report.items.append(Item(path, fm["step"], False))
    return report


def measure(front_door: str) -> Report:
    # Switch only once every reference is converted; a partial switch
    # would silently drop the unconverted files from the count.
    uses_frontmatter = all("step" in frontmatter(p) for p in all_references())
    report = from_frontmatter(front_door) if uses_frontmatter else legacy(front_door)
    report.fixed = [
        (f"{s}/SKILL.md", words(SKILLS / s / "SKILL.md"))
        for s in FIXED_SKILLS[front_door]
    ]
    return report


def print_table(report: Report) -> None:
    print(f"## {report.front_door}  (reading list: {report.source})\n")
    print(f"{'step':<14}{'files':>6}{'words':>9}{'minimal':>9}")
    fixed = sum(n for _, n in report.fixed)
    print(f"{'SKILL.md':<14}{len(report.fixed):>6}{fixed:>9}{fixed:>9}")
    for step, items in report.by_step().items():
        all_words = sum(words(i.path) for i in items)
        minimal = sum(words(i.path) for i in items if not i.conditional)
        print(f"{step:<14}{len(items):>6}{all_words:>9}{minimal:>9}")
    total, minimal = report.total(False), report.total(True)
    print(f"{'total':<14}{len(report.fixed) + len(report.items):>6}{total:>9}{minimal:>9}")
    print(f"\n~{round(minimal * 4 / 3):,} tokens on the minimal path\n")
    if report.unresolved:
        print("unresolved references: " + ", ".join(sorted(set(report.unresolved))) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--ceiling", type=int, help="max words on any minimal path")
    parser.add_argument("--verbose", "-v", action="store_true", help="list every file")
    args = parser.parse_args()

    reports = [measure(fd) for fd in FRONT_DOORS]

    if args.json:
        print(json.dumps(
            {
                r.front_door: {
                    "source": r.source,
                    "fixed": dict(r.fixed),
                    "references": [
                        {"path": i.rel, "step": i.step, "conditional": i.conditional,
                         "words": words(i.path)}
                        for i in r.items
                    ],
                    "total_words": r.total(False),
                    "minimal_words": r.total(True),
                    "unresolved": sorted(set(r.unresolved)),
                }
                for r in reports
            },
            indent=2,
        ))
    else:
        for r in reports:
            print_table(r)
            if args.verbose:
                for i in r.items:
                    flag = " (conditional)" if i.conditional else ""
                    print(f"  {i.step:<12}{words(i.path):>6}  {i.rel}{flag}")
                print()

    if args.ceiling is not None:
        over = [r for r in reports if r.total(True) > args.ceiling]
        for r in over:
            print(
                f"FAIL: {r.front_door} minimal path is {r.total(True):,} words, "
                f"ceiling is {args.ceiling:,}",
                file=sys.stderr,
            )
        return 1 if over else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
