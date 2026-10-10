#!/usr/bin/env python3
"""Validate and summarise the findings corpus in findings/.

Checks every item's frontmatter against the schema in
findings/README.md, then prints counts by target, status, cluster and
tag, and the list of open plugin items per skill/reference.

A `Resolved` item must have a `resolved_by` of the form
"<path under skills/> § <section heading>", and that heading must exist
in that file; an item tagged `contradiction` that names two or more files must
resolve to sections in at least two files.

Usage:
    tools/findings.py               # summary; exit 1 on schema errors
    tools/findings.py --check       # schema errors only, no summary (check-all.sh)
    tools/findings.py --open        # also list every open plugin item
    tools/findings.py --names X     # items that name skill/reference X
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FINDINGS = ROOT / "findings"
SKILLS = ROOT / "skills"

REQUIRED = ("id", "project", "source", "reboot_version", "severity", "target",
            "names", "tags", "cluster", "still_applies", "status", "resolved_by")
OPTIONAL = ("duplicate_of",)
ENUMS = {
    "severity": {"red", "yellow", "green", "unrated"},
    "target": {"plugin", "framework", "cloud", "bdd", "primer", "positive"},
    "still_applies": {"yes", "no", "unknown"},
    "status": {"Open", "Resolved", "Obsolete"},
}
TAGS = {"negative-space", "contradiction", "error-text", "version-drift", "scaffold",
        "seeding", "cost", "pattern", "operations", "index-gap", "builder-drift",
        "auth", "testing", "frontend"}


def parse(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError("no frontmatter")
    end = text.index("\n---", 4)
    data: dict = {}
    key = None
    for line in text[4:end].splitlines():
        if re.match(r"^\s+-\s+", line) and key:
            data.setdefault(key, [])
            if isinstance(data[key], list):
                data[key].append(line.split("-", 1)[1].strip().strip("\"'"))
            continue
        m = re.match(r"^([a-z_]+):\s*(.*)$", line)
        if not m:
            continue
        key, value = m.group(1), m.group(2).split(" #", 1)[0].strip()
        if value.startswith("[") and value.endswith("]"):
            data[key] = [v.strip().strip("\"'") for v in value[1:-1].split(",") if v.strip()]
        elif value == "":
            data[key] = [] if key in ("names", "tags") else ""
        else:
            data[key] = value.strip("\"'")
    data["_title"] = next(
        (l[2:].strip() for l in text[end:].splitlines() if l.startswith("# ")), "")
    return data


def heading_exists(ref: str) -> bool:
    if "§" not in ref:
        return False
    path, section = (part.strip() for part in ref.split("§", 1))
    file = SKILLS / path
    if not file.exists():
        return False
    headings = [l.lstrip("#").strip().lower() for l in file.read_text().splitlines()
                if l.startswith("#")]
    return section.lower() in headings


def validate(item: dict, ids: set[str] | None = None,
             by_id: dict[str, dict] | None = None) -> list[str]:
    errors = [f"missing {k}" for k in REQUIRED if k not in item]
    dup = item.get("duplicate_of")
    if dup and ids is not None and dup not in ids:
        errors.append(f"duplicate_of target {dup!r} does not exist")
    # A duplicate shares its canonical item's fate: one gap, one status.
    if dup and by_id is not None and dup in by_id:
        canonical = by_id[dup]
        if canonical.get("duplicate_of"):
            errors.append(f"duplicate_of {dup!r} is itself a duplicate")
        if item.get("status") != canonical.get("status"):
            errors.append(f"status {item.get('status')!r} differs from canonical {dup!r} "
                          f"({canonical.get('status')!r})")
    for name in item.get("names", []):
        if name.startswith("skills/"):
            errors.append(f"names entry {name!r} is written with a skills/ prefix")
        elif not (SKILLS / name).exists() and not (
                name.split("/")[0] in ("bin", "hooks", "hooks-handlers", "lib") and (ROOT / name).exists()):
            errors.append(f"names entry {name!r} does not exist under skills/ (or bin/, hooks/, lib/)")
    for key, allowed in ENUMS.items():
        if key in item and item[key] not in allowed:
            errors.append(f"{key}={item[key]!r} not in {sorted(allowed)}")
    for tag in item.get("tags", []):
        if tag not in TAGS:
            errors.append(f"unknown tag {tag!r}")
    if item.get("status") == "Resolved":
        refs = [r for r in re.split(r";\s*", item.get("resolved_by", "")) if r]
        if not refs:
            errors.append("Resolved without resolved_by")
        for ref in refs:
            if not heading_exists(ref):
                errors.append(f"resolved_by points at a missing section: {ref!r}")
        # A contradiction between two files must show both now agree; one
        # between a file and the runtime is closed by fixing that file. A
        # duplicate carries its canonical's resolution as it is.
        if (not dup and "contradiction" in item.get("tags", []) and len(item.get("names", [])) > 1
                and len({r.split("§")[0].strip() for r in refs}) < 2):
            errors.append("contradiction resolved without naming both sections")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--check", action="store_true",
                        help="report schema errors only, without the summary")
    parser.add_argument("--open", action="store_true", help="list open plugin items")
    parser.add_argument("--names", help="list items naming this skill/reference")
    args = parser.parse_args()

    items, failures = [], 0
    for path in sorted(FINDINGS.glob("*/*.md")):
        rel = path.relative_to(ROOT)
        try:
            item = parse(path)
        except Exception as e:
            print(f"{rel}: {e}")
            failures += 1
            continue
        item["_path"] = rel
        items.append(item)

    ids = {i.get("id") for i in items}
    by_id = {i.get("id"): i for i in items}
    for item in items:
        for error in validate(item, ids, by_id):
            print(f"{item['_path']}: {error}")
            failures += 1

    def table(title: str, counter: Counter) -> None:
        print(f"\n{title}")
        for key, n in counter.most_common():
            print(f"  {n:>4}  {key}")

    if args.check:
        if failures:
            print(f"{failures} schema error(s)", file=sys.stderr)
        return 1 if failures else 0

    print(f"{len(items)} items across {len({i.get('project') for i in items})} projects")
    table("by target", Counter(i.get("target") for i in items))
    plugin = [i for i in items if i.get("target") == "plugin"]
    open_plugin = [i for i in plugin if i.get("status") == "Open"]
    print("distinct open plugin gaps: "
          f"{sum(1 for i in open_plugin if not i.get('duplicate_of'))}")
    table("plugin items by status", Counter(i.get("status") for i in plugin))
    table("plugin items still applying at 1.6.0", Counter(i.get("still_applies") for i in plugin))
    table("plugin items by cluster", Counter(i.get("cluster") for i in plugin))
    table("tags (all items)", Counter(t for i in items for t in i.get("tags", [])))
    table("most-named skills/references (open plugin items)", Counter(
        n for i in plugin if i.get("status") == "Open" for n in i.get("names", [])))

    if args.names:
        print(f"\nitems naming {args.names}:")
        for i in items:
            if any(args.names in n for n in i.get("names", [])):
                print(f"  {i['id']:<28} [{i.get('status')}] {i['_title']}")
    if args.open:
        print("\nopen plugin items:")
        for i in sorted(plugin, key=lambda i: (i.get("cluster", ""), i["id"])):
            if i.get("status") == "Open":
                print(f"  {i.get('cluster', '?'):<4} {i['id']:<28} {i['_title']}")

    if failures:
        print(f"\n{failures} schema error(s)", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
