#!/usr/bin/env python3
"""Report facts a rewrite dropped from the skills.

Compares the skills at a base git revision with the working tree and
lists every fact that existed somewhere under skills/ before and exists
nowhere after. A fact that moved from one file to another is not a
loss. Facts are approximated mechanically:

* inline code spans (`like_this`) and identifiers/strings in code blocks
* the first cell of every error-table row (the literal error text)
* the lead of every "## Never" bullet
* numbers with a unit or context (`30 s`, `150 actors`, `1.6.0`, `5 minutes`)
* link targets

It is a tripwire, not a proof: a rewrite can keep every token and still
lose meaning, and a reworded Never lead shows up as a loss even when the
rule survives. Every reported loss must be either restored or justified.

Usage:
    tools/check-facts.py                  # vs HEAD
    tools/check-facts.py --base 18a2073   # vs a commit
    tools/check-facts.py --file python/references/rpc-refs.md
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"

FENCE = re.compile(r"^(```|~~~).*?^\1", re.S | re.M)
INLINE = re.compile(r"`([^`\n]{2,})`")
CODE_TOKEN = re.compile(r"\"[^\"\n]{4,}\"|'[^'\n]{4,}'|\b[A-Za-z_][\w.]*\([^)]{0,0}|\b[A-Z][A-Za-z0-9]+[a-z][A-Za-z0-9]*\b|\b[a-z]+_[a-z_0-9]+\b")
NUMBER = re.compile(r"\b\d+(?:\.\d+)*\s?(?:%|ms|s\b|seconds?|minutes?|hours?|days?|MB|GB|KB|x\b|×|actors?|rows?|words?|subscriptions?|calls?|items?|participants?|levels?|connections?|requests?)|\b\d+\.\d+\.\d+\b", re.I)
LINK = re.compile(r"\]\(([^)#\s]+)")
ERROR_SECTION = re.compile(r"^## (?:Errors you will see|Known issues)\s*$(.*?)(?=^## |\Z)", re.S | re.M)
NEVER_SECTION = re.compile(r"^## Never\s*$(.*?)(?=^## |\Z)", re.S | re.M)

GENERATED = re.compile(r"<!-- generated:start.*?<!-- generated:end -->", re.S)


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().strip("`").lower())


def facts(text: str) -> dict[str, set[str]]:
    text = GENERATED.sub("", text)  # generated regions are views, not sources
    out: dict[str, set[str]] = defaultdict(set)
    for block in FENCE.finditer(text):
        for t in CODE_TOKEN.findall(block.group(0)):
            out["code"].add(norm(t))
    prose = FENCE.sub("", text)
    for span in INLINE.findall(prose):
        out["inline"].add(norm(span))
    for n in NUMBER.findall(prose):
        out["number"].add(norm(n))
    for target in LINK.findall(text):
        if not target.startswith("http"):
            out["link"].add(Path(target).name)
    for m in ERROR_SECTION.finditer(text):
        for line in m.group(1).splitlines():
            if line.startswith("|") and not re.match(r"^\|[\s|:-]+\|$", line):
                first = line.strip("|").split("|")[0]
                if first.strip() and not first.strip().lower().startswith(("error", "none")):
                    out["error"].add(norm(first))
    for m in NEVER_SECTION.finditer(text):
        for bullet in re.split(r"^- ", m.group(1), flags=re.M)[1:]:
            lead = " ".join(bullet.split())
            bold = re.match(r"\*\*(.+?)\*\*", lead)
            lead = bold.group(1) if bold else re.split(r" — |\. ", lead)[0]
            out["never"].add(norm(lead)[:90])
    return out


def tree_files(base: str | None) -> dict[str, str]:
    if base is None:
        return {str(p.relative_to(SKILLS)): p.read_text(encoding="utf-8")
                for p in SKILLS.rglob("*.md")}
    names = subprocess.run(["git", "-C", str(ROOT), "ls-tree", "-r", "--name-only", base, "skills/"],
                           capture_output=True, text=True, check=True).stdout.split()
    out = {}
    for name in names:
        if name.endswith(".md"):
            out[name[len("skills/"):]] = subprocess.run(
                ["git", "-C", str(ROOT), "show", f"{base}:{name}"],
                capture_output=True, text=True, check=True).stdout
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--base", default="HEAD")
    parser.add_argument("--file", action="append", default=[],
                        help="only report losses from this file (path under skills/); repeatable")
    parser.add_argument("--kinds", default="inline,code,error,never,number,link")
    args = parser.parse_args()
    kinds = args.kinds.split(",")

    before, after = tree_files(args.base), tree_files(None)
    after_all: dict[str, set[str]] = defaultdict(set)
    for text in after.values():
        for k, v in facts(text).items():
            after_all[k] |= v

    lost_total = 0
    for name in sorted(before):
        if args.file and name not in args.file:
            continue
        if name in after and after[name] == before[name]:
            continue
        old = facts(before[name])
        lost = {k: sorted(v - after_all[k]) for k, v in old.items() if k in kinds}
        lost = {k: v for k, v in lost.items() if v}
        if not lost:
            continue
        print(f"\n{name}")
        for k, items in lost.items():
            for item in items:
                print(f"  lost {k:<7} {item[:110]}")
                lost_total += 1
    words_before = sum(len(t.split()) for t in before.values())
    words_after = sum(len(t.split()) for t in after.values())
    print(f"\n{lost_total} fact(s) no longer anywhere in skills/; "
          f"skills/ words {words_before:,} → {words_after:,}")
    return 1 if lost_total else 0


if __name__ == "__main__":
    sys.exit(main())
