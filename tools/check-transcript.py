#!/usr/bin/env python3
"""The shape of a real build session, read from its Claude Code transcript.

    tools/check-transcript.py <session.jsonl>
    tools/check-transcript.py <project dir>     # its newest session
    tools/check-transcript.py <...> --json

A build speaks in reports and is quiet between them (the build skill,
"How the build talks"): the welcome, one at each milestone (the app has
a domain model, a feature spec, has been built, is being tested with the
full feature suite), and the review at the handoff. The planning-only evals squeeze a build into one
message, so they cannot see that rhythm; a real session can. This reads
every message the build showed the user and reports:

- whether the first message is the welcome;
- which milestone reports and the review appear, and in order;
- the messages between reports that are none of the allowed lines (the
  scope questions, the brief after them, a question only the user
  can answer, a long-step notice), with their opening words;
- reports missing their frame: a `#` title, the rules around them, the evidence so far, and
  the closing note naming the file under `design/reports/`;
- lines in the first person, "settled", "actor" (a domain object to the user), em or en dashes, semicolons.

Exit 0 always: it is a report, not a gate.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

WELCOME = re.compile(r"\bWelcome to Reboot\b")
MILESTONES = [
    ("domain-model", re.compile(r"\bThe app has a (proposed )?domain model\b")),
    ("feature-spec", re.compile(r"\bThe app has a feature spec\b")),
    ("built", re.compile(r"\bThe app has been built\b")),
    ("full-suite", re.compile(r"\bThe app is being tested with the full feature suite\b")),
]
SCOPE_LINE = re.compile(r"\bA proposed model is being built\. Objects include\b")
REVIEW = re.compile(r"\b(first prototype is running|for your review)\b", re.I)
FIRST_PERSON = re.compile(r"(?:^|[.!?]\s+|\n)\s*(I|I'll|I'm|I've|I'd|We|We'll|We're|Let me|Let's)\b")
ACTOR = re.compile(r"\bactors?\b", re.I)
SETTLED = re.compile(r"\bsettled\b", re.I)
DASH = re.compile(r"[—–]")
FRAMED = [re.compile(r"^# ", re.M), re.compile(r"^-{3,}\s*$", re.M),
          re.compile(r"Evidence so far", re.I), re.compile(r"design/reports/")]
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
    for name, rx in MILESTONES:
        if rx.search(text):
            return name
    if SCOPE_LINE.search(text):
        return "brief"
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
    reports = [k for k in kinds if k in ("welcome", "brief", "review") or k in dict(MILESTONES)]
    return {
        "session": str(session),
        "messages": len(messages),
        "welcome_first": bool(kinds) and kinds[0] == "welcome",
        "reports_in_order": reports,
        "unframed": [k for m, k in zip(messages, kinds)
                     if k in ("brief", "review") or k in dict(MILESTONES)
                     if not all(rx.search(m) for rx in FRAMED)],
        "between": [m.strip().splitlines()[0][:100] for m, k in zip(messages, kinds) if k == "other"],
        "first_person": len(first_person),
        "first_person_lines": lines(FIRST_PERSON)[:8],
        "settled": lines(SETTLED)[:5],
        "actor": lines(ACTOR)[:5],
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
    print(f"reports missing their frame: {', '.join(result['unframed']) or 'none'}")
    print(f"messages between reports: {len(result['between'])}")
    for line in result["between"][:12]:
        print(f"  - {line}")
    print(f"first-person sentences: {result['first_person']}")
    for line in result["first_person_lines"]:
        print(f"  - {line}")
    print(f"'settled': {len(result['settled'])}   'actor': {len(result['actor'])}   dashes: {result['dashes']}   semicolons: {result['semicolons']}")


if __name__ == "__main__":
    main()
