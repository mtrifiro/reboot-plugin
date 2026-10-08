#!/usr/bin/env python3
"""Check that every Markdown file starts with YAML front matter.

Each category of file keeps its own schema, checked in full by its own
tool; this checks only that the block exists and carries the keys every
file of its category needs. Files with no category schema use the
document schema in tools/README.md ("Front matter").

Usage:
    tools/lint-frontmatter.py      # exit 1 on any problem
"""

from __future__ import annotations

import fnmatch
import sys
from pathlib import Path

from reflib import FRONT_DOORS, ROOT, parse_frontmatter

SKIP_DIRS = {".git", "node_modules", ".gstack", "dist", "__pycache__"}
SKIP_PREFIXES = ("evals/results/", "plugins/")  # plugins/reboot links to the repo root

# Files that deliberately have no front matter.
EXEMPT = (
    # GitHub renders front matter as a table on a directory's landing page.
    "README.md",
    "*/README.md",
    # Copied verbatim into every new project (copy.sh): the user's file.
    "skills/build/templates/*/FINDINGS.md",
    "skills/build/templates/*/AGENTS.md",
    "skills/build/templates/*/CLAUDE.md",
)

# (glob, required keys, checked in full by)
CATEGORIES = (
    ("skills/*/SKILL.md", ("name", "description"), "the plugin host"),
    ("skills/_template.md", ("title", "summary"), "lint-references.py"),
    ("skills/*/references/_*.md", None, None),  # documents: fall through
    ("skills/*/references/*.md", ("summary",), "lint-references.py"),
    ("findings/*/*.md", ("id",), "findings.py"),
    ("evals/*/prompt.md", (), "claude plugin eval"),
    ("evals/*/graders/*.md", ("type",), "claude plugin eval"),
)

DOC_KEYS = ("title", "summary", "kind", "audience")
KINDS = ("migration", "index", "report", "backlog")
AUDIENCES = ("agent", "maintainer")


def markdown_files() -> list[Path]:
    out = []
    for path in sorted(ROOT.rglob("*.md")):
        rel = path.relative_to(ROOT)
        if SKIP_DIRS.intersection(rel.parts[:-1]):
            continue
        if rel.as_posix().startswith(SKIP_PREFIXES):
            continue
        out.append(path)
    return out


def check(path: Path) -> list[str]:
    rel = path.relative_to(ROOT).as_posix()
    if any(fnmatch.fnmatchcase(rel, pat) for pat in EXEMPT):
        return []
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n") or text.find("\n---", 4) < 0:
        return [f"{rel}: missing front matter"]
    fm = parse_frontmatter(text)

    for pattern, keys, _owner in CATEGORIES:
        if fnmatch.fnmatchcase(rel, pattern):
            if keys is None:
                break
            return [f"{rel}: missing key '{k}'" for k in keys if fm.get(k) in (None, "", [])]

    problems = [f"{rel}: missing key '{k}'" for k in DOC_KEYS if fm.get(k) in (None, "", [])]
    kind, audience = fm.get("kind"), fm.get("audience")
    if kind and kind not in KINDS:
        problems.append(f"{rel}: kind '{kind}' is not one of {', '.join(KINDS)}")
    if audience and audience not in AUDIENCES:
        problems.append(f"{rel}: audience '{audience}' is not one of {', '.join(AUDIENCES)}")
    in_migrations = rel.startswith("skills/upgrade/migrations/")
    if kind == "migration":
        if not in_migrations:
            problems.append(f"{rel}: a migration must live under skills/upgrade/migrations/")
        applies = fm.get("applies")
        if not isinstance(applies, list) or not applies:
            problems.append(f"{rel}: missing key 'applies'")
        else:
            problems += [
                f"{rel}: applies '{a}' is not one of {', '.join(FRONT_DOORS)}"
                for a in applies if a not in FRONT_DOORS
            ]
    elif in_migrations:
        problems.append(f"{rel}: a file in skills/upgrade/migrations/ must have kind: migration")
    return problems


def main() -> int:
    files = markdown_files()
    problems = [p for f in files for p in check(f)]
    for p in problems:
        print(p)
    print(f"{len(files)} Markdown files; {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
