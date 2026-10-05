#!/usr/bin/env python3
"""Generate the skills' reference indices from reference frontmatter.

Every index of the references (each builder's "Which References to
Read, and When", the python skill's reading list and catalog) is a
view of one source: the frontmatter at the top of each reference. This
tool rewrites the regions of the SKILL.md files marked

    <!-- generated:start KIND key=value ... -->
    ...
    <!-- generated:end -->

and leaves everything outside them alone, so step headings and notes
stay hand-written while the lists under them are generated.

Kinds:
    reading-list front-door=<fd> step=<step>   files a build reads at a step
    always front-door=<fd>                     files every build reads first
    catalog skill=<skill>                      every reference of a skill, by concept

It also enforces the invariants that keep the map honest (see
`check_invariants`). Run with `--check` in CI: it fails if a committed
region differs from what it would generate.

Usage:
    tools/gen-index.py            # rewrite regions in place
    tools/gen-index.py --check    # exit 1 on drift or a broken invariant
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from reflib import (BUILD_STEPS, FRONT_DOORS, ROOT, SKILLS, STEPS, Ref, always_list,
                    concepts, load_refs, pinned_reboot_version, reading_list)

BLOCK = re.compile(
    r"(?P<open><!-- generated:start (?P<kind>[a-z-]+)(?P<args>[^>]*?)-->\n)"
    r"(?P<body>.*?)"
    r"(?P<close><!-- generated:end -->)",
    re.S,
)
REQUIRED = ("title", "summary", "step", "applies", "always", "verified")
LISTED: set[str] = set()  # every reference some generated region names


def display(ref: Ref, host_skill: str) -> str:
    """How a reference is named from inside `host_skill`'s SKILL.md."""
    if ref.skill == host_skill:
        return f"`references/{ref.name}`"
    return f"`{ref.skill}/references/{ref.name}`"


def bullet(ref: Ref, host_skill: str, front_door: str | None) -> str:
    # A conditional file shows only its condition: an agent whose app
    # doesn't match skips it, one whose app does opens it anyway. Every
    # word here is re-read on every turn of every build.
    when = ref.when(front_door) if front_door else ref.fm.get("when", "")
    if when:
        return f"- {display(ref, host_skill)} — only when {when}."
    return f"- {display(ref, host_skill)} — {ref.summary.rstrip('.')}."


def render(kind: str, args: dict, host_skill: str, refs: list[Ref]) -> str:
    if kind == "reading-list":
        fd, step = args["front-door"], args["step"]
        if fd not in FRONT_DOORS or step not in STEPS:
            raise ValueError(f"bad reading-list args {args}")
        items = reading_list(refs, fd, step)
        LISTED.update(r.rel for r in items)
        if not items:
            return "_No references for this step._\n"
        return "".join(bullet(r, host_skill, fd) + "\n" for r in items)
    if kind == "always":
        fd = args["front-door"]
        items = always_list(refs, fd)
        LISTED.update(r.rel for r in items)
        return "".join(bullet(r, host_skill, fd) + "\n" for r in items)
    if kind == "catalog":
        skill = args.get("skill", host_skill)
        mine = [r for r in refs if r.skill == skill]
        out = []
        for prefix, heading in concepts():
            group = sorted((r for r in mine if r.concept == prefix), key=lambda r: r.name)
            if not group:
                continue
            out.append(f"**{heading}**\n")
            for r in group:
                LISTED.add(r.rel)
                # Titles, not summaries: the catalog is for finding a file by
                # topic; the reading lists carry the summaries.
                b = f"- {display(r, host_skill)} — {r.title}"
                if r.via:
                    b += f" (via `{r.via}`)"
                out.append(b + "\n")
            out.append("\n")
        return "".join(out).rstrip("\n") + "\n"
    if kind == "never-digest":
        return never_digest(refs, host_skill)
    raise ValueError(f"unknown block kind {kind!r}")


def never_items(ref: Ref) -> list[str]:
    """First line of each bullet in a reference's "## Never" section."""
    text = ref.path.read_text(encoding="utf-8")
    m = re.search(r"^## Never\s*$(.*?)(?=^## |\Z)", text, re.S | re.M)
    if not m:
        return []
    items = []
    for bullet in re.split(r"^- ", m.group(1), flags=re.M)[1:]:
        first = " ".join(bullet.split())
        # Only the lead: a bold phrase, else the wrong form before " — ",
        # else the first sentence. The reference holds the reason.
        bold = re.match(r"\*\*(.+?)\*\*", first)
        if bold:
            lead = bold.group(1)
        elif " — " in first:
            lead = first.split(" — ", 1)[0]
        else:
            cut = re.search(r"(?<=[.;])\s", first)
            lead = first[: cut.start()] if cut else first
        items.append(lead.rstrip(".:;") )
    return items


def never_digest(refs: list[Ref], host_skill: str) -> str:
    """Every converted reference's Never list, one line per item."""
    out = []
    order = {p: i for i, (p, _) in enumerate(concepts())}
    for r in sorted(refs, key=lambda r: (r.skill != "python", order.get(r.concept, 99), r.name)):
        items = never_items(r)
        if not items or r.name == "patterns-common-gotchas.md":
            continue
        LISTED.add(r.rel)
        where = (f"`{r.name}`" if r.skill == host_skill else f"`{r.skill}/references/{r.name}`")
        out.append(f"**{where}**\n")
        out.extend(f"- {item}\n" for item in items)
        out.append("\n")
    return "".join(out).rstrip("\n") + "\n"


def parse_args(raw: str) -> dict:
    return dict(re.findall(r"([a-z-]+)=([^\s]+)", raw))


def process(path: Path, refs: list[Ref]) -> tuple[str, str, int]:
    text = path.read_text(encoding="utf-8")
    host = path.parent.name if path.name == "SKILL.md" else path.parent.parent.name
    count = 0

    def sub(m: re.Match) -> str:
        nonlocal count
        count += 1
        body = render(m.group("kind"), parse_args(m.group("args")), host, refs)
        return m.group("open") + body + m.group("close")

    return text, BLOCK.sub(sub, text), count


def check_invariants(refs: list[Ref], listed: set[str]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    known = {p for p, _ in concepts()}

    for r in refs:
        for f in REQUIRED:
            if f not in r.fm or r.fm[f] in ("", []):
                errors.append(f"{r.rel}: missing {f}")
        if r.step and r.step not in STEPS:
            errors.append(f"{r.rel}: step {r.step!r} not in {STEPS}")
        for fd in r.applies:
            if fd not in FRONT_DOORS:
                errors.append(f"{r.rel}: applies names unknown front door {fd!r}")
        if r.skill == "python" and r.concept not in known:
            errors.append(f"{r.rel}: prefix {r.concept!r} is not a concept in _sections.md")
        if r.via:
            router = r.path.parent / r.via
            if not router.exists():
                errors.append(f"{r.rel}: via {r.via} does not exist")
            elif r.name not in router.read_text(encoding="utf-8"):
                errors.append(f"{r.rel}: router {r.via} does not mention {r.name}")
        for m in re.finditer(r"\]\(([^)#\s]+\.md)", r.path.read_text(encoding="utf-8")):
            target = m.group(1)
            if not target.startswith("http") and not (r.path.parent / target).resolve().exists():
                errors.append(f"{r.rel}: link to missing file {target}")
        if not r.fm.get("docs"):
            warnings.append(f"{r.rel}: no docs: URL")

    # verified must not lag the pinned Reboot by more than one minor version.
    pinned = pinned_reboot_version()
    if pinned:
        major, minor = (int(x) for x in pinned.split(".")[:2])
        for r in refs:
            v = str(r.fm.get("verified", ""))
            if re.match(r"^\d+\.\d+", v):
                vmaj, vmin = (int(x) for x in v.split(".")[:2])
                if (vmaj, vmin) < (major, minor - 1):
                    errors.append(f"{r.rel}: verified {v} lags pinned reboot {pinned}")

    for prefix, heading in concepts():
        if not any(r.skill == "python" and r.concept == prefix for r in refs):
            errors.append(f"_sections.md: concept {heading!r} ({prefix}) has no reference")

    for r in refs:
        if r.rel not in listed and not r.via:
            warnings.append(f"{r.rel}: not listed in any generated index")
    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--quiet", "-q", action="store_true", help="hide warnings")
    args = parser.parse_args()

    refs = load_refs()
    drift, total = [], 0
    hosts = sorted(SKILLS.glob("*/SKILL.md")) + [
        r.path for r in refs if "<!-- generated:start" in r.path.read_text(encoding="utf-8")]
    for path in hosts:
        before, after, count = process(path, refs)
        total += count
        if before != after:
            drift.append(path)
            if not args.check:
                path.write_text(after, encoding="utf-8")

    errors, warnings = check_invariants(refs, LISTED)
    for e in errors:
        print(f"error: {e}")
    if not args.quiet:
        for w in warnings:
            print(f"warning: {w}")

    rel = [str(p.relative_to(ROOT)) for p in drift]
    if args.check:
        for p in rel:
            print(f"drift: {p} differs from its generated form (run tools/gen-index.py)")
    elif rel:
        print("rewrote: " + ", ".join(rel))
    print(f"{total} generated region(s); {len(refs)} references; "
          f"{len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors or (args.check and drift) else 0


if __name__ == "__main__":
    sys.exit(main())
