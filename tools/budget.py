#!/usr/bin/env python3
"""Measure the reading cost of a build, per front door.

An agent that follows the skills exactly reads a fixed set of SKILL.md
files plus every reference the builder's reading list names, before
it writes application code. Everything it reads is re-sent on every
later turn, so this number is a release metric: reported against a
target of 30,000 words per front door, and held under a ceiling that
only moves down (`--check` fails when a path grows past its ceiling;
a cut lowers the ceiling).

The reading list comes from the references' frontmatter (`step:`,
`applies:`, `always:`, `when:`; see skills/_template.md): every
reference with `always: true`, plus every reference whose `step` is a
build step and whose `applies` includes the front door. The "minimal"
column leaves out the ones with a `when:` condition for that front
door.

Usage:
    tools/budget.py                    # table for every front door
    tools/budget.py --json
    tools/budget.py --check            # README table current; every path under its ceiling
    tools/budget.py --readme write     # refresh the README's budget table
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import reflib

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"

FRONT_DOORS = ("mcp-ui", "web-app", "backend-only")

# SKILL.md files every build of a front door reads in full, in order:
# the router, the build spine, the dashboard it starts before Step 1,
# the front door's delta, the feature workflow and run. Backend-only
# work starts from the python skill.
SKILLS_READ = {
    "mcp-ui": ["app", "build", "dashboard", "mcp-ui", "feature", "run"],
    "web-app": ["app", "build", "dashboard", "web-app", "feature", "run"],
    "backend-only": ["python", "feature", "run"],
}

# Words on each front door's minimal path to aim for.
TARGET = 30000

# The most words each front door's minimal path may hold: `--check`
# fails above it. Lower one when a cut lands. Raise one only with the
# reason in the commit, since this is the line every later edit is
# held to.
CEILINGS = {"mcp-ui": 39000, "web-app": 38500, "backend-only": 26000}

README_LABELS = {"mcp-ui": "MCP UI", "web-app": "Web App", "backend-only": "Backend only"}


def words(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").split())


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
    fixed: list[tuple[str, int]] = field(default_factory=list)
    items: list[Item] = field(default_factory=list)

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


def measure(front_door: str, refs: list) -> Report:
    report = Report(front_door)
    report.fixed = [(f"{s}/SKILL.md", words(SKILLS / s / "SKILL.md"))
                    for s in SKILLS_READ[front_door]]
    for r in reflib.always_list(refs, front_door):
        report.items.append(Item(r.path, "always", False))
    for step in reflib.BUILD_STEPS:
        for r in reflib.reading_list(refs, front_door, step):
            report.items.append(Item(r.path, step, bool(r.when(front_door))))
    return report


def print_table(report: Report) -> None:
    print(f"## {report.front_door}\n")
    print(f"{'step':<14}{'files':>6}{'words':>9}{'minimal':>9}")
    fixed = sum(n for _, n in report.fixed)
    print(f"{'SKILL.md':<14}{len(report.fixed):>6}{fixed:>9}{fixed:>9}")
    for step, items in report.by_step().items():
        all_words = sum(words(i.path) for i in items)
        minimal = sum(words(i.path) for i in items if not i.conditional)
        print(f"{step:<14}{len(items):>6}{all_words:>9}{minimal:>9}")
    total, minimal = report.total(False), report.total(True)
    print(f"{'total':<14}{len(report.fixed) + len(report.items):>6}{total:>9}{minimal:>9}")
    print(f"\n~{round(minimal * 4 / 3):,} tokens on the minimal path; "
          f"ceiling {CEILINGS[report.front_door]:,}, target {TARGET:,}\n")


def readme_text(reports: list[Report]) -> tuple[Path, str, str]:
    """The README, as it is and as the budget table should make it."""
    rows = ["| Front door | Words on the minimal path | Ceiling | Target |",
            "| --- | ---: | ---: | ---: |"]
    for r in reports:
        rows.append(f"| {README_LABELS[r.front_door]} | {r.total(True):,} "
                    f"| {CEILINGS[r.front_door]:,} | {TARGET:,} |")
    path = ROOT / "README.md"
    text = path.read_text(encoding="utf-8")
    m = re.search(r"(<!-- budget:start[^>]*-->\n)(.*?)(<!-- budget:end -->)", text, re.S)
    if not m:
        print("README.md has no budget:start/budget:end region", file=sys.stderr)
        sys.exit(1)
    return path, text, text[: m.start(2)] + "\n".join(rows) + "\n" + text[m.end(2):]


def check(reports: list[Report]) -> int:
    problems = []
    _, current, wanted = readme_text(reports)
    if current != wanted:
        problems.append("README.md budget table is stale (run tools/budget.py --readme write)")
    for r in reports:
        if r.total(True) > CEILINGS[r.front_door]:
            problems.append(f"{README_LABELS[r.front_door]}: {r.total(True):,} words on the "
                            f"minimal path, over its ceiling of {CEILINGS[r.front_door]:,}; "
                            "cut, or raise CEILINGS in tools/budget.py with the reason")
    for p in problems:
        print(f"budget: {p}", file=sys.stderr)
    if not problems:
        print("budget: " + ", ".join(
            f"{README_LABELS[r.front_door]} {r.total(True):,}/{CEILINGS[r.front_door]:,}"
            for r in reports))
    return 1 if problems else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true", help="list every file")
    parser.add_argument("--check", action="store_true",
                        help="the README table is current and every path is under its ceiling")
    parser.add_argument("--readme", choices=("write",), help="rewrite the README's budget table")
    args = parser.parse_args()

    refs = reflib.load_refs()
    reports = [measure(fd, refs) for fd in FRONT_DOORS]

    if args.check:
        return check(reports)
    if args.readme:
        path, _, wanted = readme_text(reports)
        path.write_text(wanted, encoding="utf-8")
        return 0
    if args.json:
        print(json.dumps(
            {
                r.front_door: {
                    "fixed": dict(r.fixed),
                    "references": [
                        {"path": i.rel, "step": i.step, "conditional": i.conditional,
                         "words": words(i.path)}
                        for i in r.items
                    ],
                    "total_words": r.total(False),
                    "minimal_words": r.total(True),
                    "ceiling": CEILINGS[r.front_door],
                }
                for r in reports
            },
            indent=2,
        ))
        return 0
    for r in reports:
        print_table(r)
        if args.verbose:
            for i in r.items:
                flag = " (conditional)" if i.conditional else ""
                print(f"  {i.step:<10} {words(i.path):>6}  {i.rel}{flag}")
            print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
