#!/usr/bin/env python3
"""The shape of a real build session, read from its Claude Code transcript.

    tools/check-transcript.py <session.jsonl>
    tools/check-transcript.py <project dir>     # its newest session
    tools/check-transcript.py <...> --json

A build speaks in four reports and is quiet between them (the build
skill, "How the build talks"): the welcome, the proposed model, "From
model to working code", and the review at the handoff. The planning-only evals squeeze a build into one
message, so they cannot see that rhythm; a real session can. This reads
every message the build showed the user and reports:

- whether the first message is the welcome;
- whether a proposed-model report and a review appear, and in order;
- the messages between reports that are none of the allowed lines (the
  scope questions, one line naming the objects, a question only the user
  can answer, a long-step notice), with their opening words;
- lines in the first person, "settled", em or en dashes, semicolons.

Exit 0 always: it is a report, not a gate.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

WELCOME = re.compile(r"\bWelcome to Reboot\b")
PROPOSED = re.compile(r"\bA proposed model is being built\b")
WORKING = re.compile(r"\bThe model is now working code\b")
REVIEW = re.compile(r"\b(first prototype is running|for your review)\b", re.I)
SCOPE_LINE = re.compile(r"\bA proposed model is being built\. Objects include\b")
FIRST_PERSON = re.compile(r"(?:^|[.!?]\s+|\n)\s*(I|I'll|I'm|I've|I'd|We|We'll|We're|Let me|Let's)\b")
SETTLED = re.compile(r"\bsettled\b", re.I)
DASH = re.compile(r"[—–]")
CODE = re.compile(r"```.*?```|`[^`\n]*`", re.S)


def project_dir_for(path: Path) -> Path:
    encoded = "-" + str(path.resolve()).strip("/").replace("/", "-").replace(".", "-")
    return Path.home() / ".claude" / "projects" / encoded


def newest_session(target: Path) -> Path:
    if target.is_file():
        return target
    folder = target if target.name.startswith("-") else project_dir_for(target)
    sessions = sorted(folder.glob("*.jsonl"), key=lambda p: p.stat().st_mtime)
    if not sessions:
        sys.exit(f"check-transcript: no session found under {folder}")
    return sessions[-1]


def shown_messages(session: Path) -> list[str]:
    """Each assistant turn's visible text, in order (thinking excluded)."""
    out = []
    for line in session.read_text(errors="replace").splitlines():
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        if entry.get("type") != "assistant" or entry.get("isSidechain"):
            continue
        content = (entry.get("message") or {}).get("content") or []
        text = "\n".join(c.get("text", "") for c in content
                         if isinstance(c, dict) and c.get("type") == "text").strip()
        if text:
            out.append(text)
    return out


def kind(text: str) -> str:
    if WELCOME.search(text):
        return "welcome"
    if PROPOSED.search(text) and not SCOPE_LINE.search(text.strip()[:200]) or "| Object" in text and PROPOSED.search(text):
        return "proposed-model"
    if WORKING.search(text):
        return "working-code"
    if SCOPE_LINE.search(text) and len(text) < 400:
        return "scope-line"
    if REVIEW.search(text):
        return "review"
    if text.rstrip().endswith("?") and len(text) < 600:
        return "question"
    return "other"


def check(session: Path) -> dict:
    messages = shown_messages(session)
    kinds = [kind(m) for m in messages]
    prose = [CODE.sub(" ", m) for m in messages]
    first_person = [m for p in prose for m in FIRST_PERSON.findall(p)]
    def lines(rx):
        return [l.strip()[:100] for p in prose for l in p.splitlines() if rx.search(l)]
    reports = [k for k in kinds if k in ("welcome", "proposed-model", "working-code", "review")]
    return {
        "session": str(session),
        "messages": len(messages),
        "welcome_first": bool(kinds) and kinds[0] == "welcome",
        "reports_in_order": reports,
        "between": [m.strip().splitlines()[0][:100] for m, k in zip(messages, kinds) if k == "other"],
        "first_person": len(first_person),
        "first_person_lines": lines(FIRST_PERSON)[:8],
        "settled": lines(SETTLED)[:5],
        "dashes": len(lines(DASH)),
        "semicolons": sum(p.count(";") for p in prose),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("target", help="a session .jsonl, a project directory, or its ~/.claude/projects folder")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = check(newest_session(Path(args.target).expanduser()))
    if args.json:
        print(json.dumps(result, indent=2))
        return
    print(f"session: {result['session']}")
    print(f"messages shown: {result['messages']}")
    print(f"welcome first: {'yes' if result['welcome_first'] else 'no'}")
    print(f"reports, in order: {', '.join(result['reports_in_order']) or 'none'}")
    print(f"messages between reports: {len(result['between'])}")
    for line in result["between"][:12]:
        print(f"  - {line}")
    print(f"first-person sentences: {result['first_person']}")
    for line in result["first_person_lines"]:
        print(f"  - {line}")
    print(f"'settled': {len(result['settled'])}   dashes: {result['dashes']}   semicolons: {result['semicolons']}")


if __name__ == "__main__":
    main()
