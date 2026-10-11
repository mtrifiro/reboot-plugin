#!/usr/bin/env python3
"""Lines the API lost since a commit, less the ones the developer approved.

    scripts/api_removals.py <base>            # base..working tree
    scripts/api_removals.py <base> --head     # base..HEAD, committed (deploy.sh)

A deployed app's API only grows: a line removed from `api/` since the
commit production runs (a method, a field, a reworded description) needs
an expunge and a restore, which `scripts/deploy.sh` never does. Reboot
allows a few changes a line diff cannot tell apart from breaking ones (an
`mcp=` option, a field's `description=`;
`python/references/api-schema-evolution.md`). Each such removal ships
only when `deploy/api-exceptions.md` names it, file and exact line:

    - file: api/bank/v1/bank.py
      removed: `description="The balance, in cents.",`
      why: a field's description may change (api-schema-evolution.md)

A method's `description=` never may: Reboot refuses it at boot.

Exit 0 when every removed line is approved (each approval covers one
removed line), 1 otherwise, printing what is left. An approval that
matches nothing has shipped, or was never needed: it is printed as a
note to delete.
"""

import collections
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXCEPTIONS = ROOT / "deploy" / "api-exceptions.md"


def removed_lines(base: str, head: bool) -> list[tuple[str, str]]:
    """Every line removed from `api/`, as (file, line stripped)."""
    spec = [f"{base}..HEAD"] if head else [base]
    diff = subprocess.run(
        ["git", "diff", *spec, "--", "api/"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    removed: list[tuple[str, str]] = []
    path = ""
    for line in diff.splitlines():
        if line.startswith("--- "):
            path = line[len("--- a/") :] if line.startswith("--- a/") else ""
        elif line.startswith("-") and not line.startswith("---"):
            removed.append((path, line[1:].strip()))
    return removed


def approvals() -> list[tuple[str, str]]:
    """(file, line) for each `- file:` / `removed:` pair in the exceptions file,
    outside its `<!-- -->` comments (the example is one)."""
    if not EXCEPTIONS.is_file():
        return []
    found: list[tuple[str, str]] = []
    path = ""
    text = re.sub(r"<!--.*?-->", "", EXCEPTIONS.read_text(), flags=re.S)
    for line in text.splitlines():
        m = re.match(r"\s*-\s*file:\s*(\S+)", line)
        if m:
            path = m.group(1)
            continue
        m = re.match(r"\s*removed:\s*`(.*)`", line)
        if m and path:
            found.append((path, m.group(1).strip()))
            path = ""
    return found


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 1:
        print(__doc__, file=sys.stderr)
        return 2
    base, head = args[0], "--head" in sys.argv

    left = collections.Counter(removed_lines(base, head))
    unused: list[tuple[str, str]] = []
    used: list[tuple[str, str]] = []
    for approval in approvals():
        if left[approval] > 0:
            left[approval] -= 1
            used.append(approval)
        else:
            unused.append(approval)

    for path, line in used:
        print(f"approved in deploy/api-exceptions.md: {path}: {line}")
    for path, line in unused:
        print(
            "note: deploy/api-exceptions.md approves a removal not in this diff "
            f"(shipped, or never needed; delete it): {path}: {line}"
        )
    leftover = [(p, l) for (p, l), n in left.items() for _ in range(n)]
    if leftover:
        for path, line in leftover[:20]:
            print(f"-{line}    ({path})")
        print(
            f"the API lost or changed lines since {base} (above), and "
            "deploy/api-exceptions.md approves none of them: that needs an "
            "expunge and a restore, or an approval if Reboot allows the "
            "change (python/references/api-schema-evolution.md)."
        )
        return 1
    print(f"additive since {base}" + (f", with {len(used)} approved" if used else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
