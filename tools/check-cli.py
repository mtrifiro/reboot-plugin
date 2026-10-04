#!/usr/bin/env python3
"""Check every `rbt` invocation in the skills against the pinned CLI.

Extracts each `rbt …` command (in code blocks and inline code) and each
`.rbtrc` line (`<subcommand>[:config] --flag`) from every SKILL.md and
reference, resolves its subcommand path, and checks every `--flag`
against `rbt <subcommand> --help` from the plugin's own `bin/rbt`, so
the check runs against exactly the Reboot version the plugin pins.

Invocations inside a code block introduced as an incorrect example
("Incorrect", "Don't", "Never", "Wrong", "Bad") are reported separately
and do not fail the check.

Usage:
    tools/check-cli.py            # report; exit 1 on any unknown flag/subcommand
    tools/check-cli.py --json
"""

from __future__ import annotations

import argparse
import functools
import json
import re
import shlex
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
RBT = ROOT / "bin" / "rbt"

INCORRECT = re.compile(r"incorrect|don'?t|never|wrong|\bbad\b|avoid", re.IGNORECASE)
FENCE = re.compile(r"^\s*(```+|~~~+)")
INLINE = re.compile(r"`(rbt [^`]+)`")
FLAG = re.compile(r"(?<![\w-])--[a-z][a-z0-9-]*")


@functools.cache
def help_text(path: tuple[str, ...]) -> str:
    result = subprocess.run(
        [str(RBT), *path, "--help"], capture_output=True, text=True, timeout=120
    )
    return result.stdout + result.stderr


@functools.cache
def subcommands(path: tuple[str, ...]) -> frozenset[str]:
    m = re.search(r"^\s*\{([a-z0-9_,-]+)\}", help_text(path), re.MULTILINE)
    return frozenset(m.group(1).split(",")) if m else frozenset()


@functools.cache
def known_flags(path: tuple[str, ...]) -> frozenset[str]:
    # Flags accepted at this level plus the top-level ones (e.g.
    # --state-directory) which argparse accepts before the subcommand.
    flags = set(FLAG.findall(help_text(path)))
    flags |= set(FLAG.findall(help_text(())))
    return frozenset(flags)


@dataclass
class Finding:
    file: str
    line: int
    command: str
    problem: str
    incorrect_example: bool


def tokens(command: str) -> list[str]:
    try:
        return shlex.split(command, comments=True)
    except ValueError:
        return command.split()


def check(command: str) -> list[str]:
    """Return problems with one `rbt`-relative command (no leading `rbt`)."""
    words = tokens(command)
    path: list[str] = []
    rest = words
    while rest:
        head = rest[0].split(":", 1)[0]  # .rbtrc named configs: `dev:run`
        if head in subcommands(tuple(path)):
            path.append(head)
            rest = rest[1:]
        else:
            break
    if not path:
        return [f"unknown subcommand {words[0]!r}" if words else "empty command"]
    if subcommands(tuple(path)) and not any(w.startswith("-") for w in rest):
        # A group such as `rbt cloud` with no leaf; only flag it when it
        # is followed by something that is clearly a subcommand attempt.
        if rest and re.fullmatch(r"[a-z][a-z-]+", rest[0]):
            return [f"unknown subcommand {' '.join(path)} {rest[0]!r}"]
        return []
    problems = []
    flags = known_flags(tuple(path))
    for w in rest:
        if not w.startswith("--"):
            continue
        flag = w.split("=", 1)[0]
        if flag not in flags and flag != "--":
            problems.append(f"unknown flag {flag} for `rbt {' '.join(path)}`")
    return problems


def is_rbtrc_line(line: str) -> bool:
    first = line.split(maxsplit=1)
    if len(first) < 2:
        return False
    head = first[0].split(":", 1)[0]
    return head in subcommands(()) and (
        first[1].startswith("--") or first[1].split()[0] in subcommands((head,))
    )


def scan(path: Path) -> list[Finding]:
    findings: list[Finding] = []
    rel = str(path.relative_to(ROOT))
    lines = path.read_text(encoding="utf-8").splitlines()
    in_block = False
    block_incorrect = False
    pending = ""
    pending_line = 0

    def emit(command: str, lineno: int, incorrect: bool) -> None:
        for problem in check(command):
            findings.append(Finding(rel, lineno, "rbt " + command, problem, incorrect))

    for i, raw in enumerate(lines, start=1):
        if FENCE.match(raw):
            if not in_block:
                context = " ".join(lines[max(0, i - 4) : i - 1])
                block_incorrect = bool(INCORRECT.search(context))
            in_block = not in_block
            continue
        if in_block:
            line = raw.strip()
            if pending:
                line = pending + " " + line
            if line.endswith("\\"):
                pending, pending_line = line[:-1].strip(), pending_line or i
                continue
            lineno = pending_line or i
            pending, pending_line = "", 0
            line = re.sub(r"^(\$\s+|.*?/bin/)", "", line)
            # Comments (shell / Dockerfile / layout trees) mention rbt in prose.
            line = re.sub(r"(^|\s)#.*$", "", line).strip()
            m = re.search(r"(?:^|[\s;&|(])rbt\s+(?![=.(:])(.+)", line)  # not `rbt = Reboot()`
            if m:
                emit(m.group(1), lineno, block_incorrect)
            elif is_rbtrc_line(line):
                emit(line, lineno, block_incorrect)
        else:
            for m in INLINE.finditer(raw):
                command = m.group(1)[4:]
                if "<" in command or "…" in command or "..." in command:
                    command = re.sub(r"\S*(<[^>]*>|…|\.\.\.)\S*", "", command)
                emit(command, i, bool(INCORRECT.search(raw)))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    files = sorted(SKILLS.rglob("*.md"))
    findings = [f for path in files for f in scan(path)]
    real = [f for f in findings if not f.incorrect_example]

    if args.json:
        print(json.dumps([asdict(f) for f in findings], indent=2))
    else:
        for f in real:
            print(f"{f.file}:{f.line}: {f.problem}\n    {f.command}")
        examples = [f for f in findings if f.incorrect_example]
        if examples:
            print(f"\n{len(examples)} in incorrect-example blocks (not failures):")
            for f in examples:
                print(f"  {f.file}:{f.line}: {f.problem}")
        print(f"\n{len(real)} problem(s) across {len(files)} files")
    return 1 if real else 0


if __name__ == "__main__":
    sys.exit(main())
