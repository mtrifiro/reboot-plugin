#!/usr/bin/env python3
"""The Prove evidence for a pull request, as one Markdown comment: the
model diff (from the accepted design when the project has a committed
`design/accepted.json`, else from the base revision given), the
servicers without an authorizer, and the last test run
(`tests/.last-run.json`, which `uv run pytest` writes).

    scripts/prove_comment.py <base>      # .github/workflows/prove.yml posts the output

It reports; it never fails the workflow. The suite and the type check
are the steps before it.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MARK = "<!-- prove -->"


def run(*args: str) -> str:
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True).stdout


def main() -> int:
    base = sys.argv[1] if len(sys.argv) > 1 else "HEAD~1"
    sha = run("git", "rev-parse", "--short", "HEAD").strip()
    accepted = run("git", "log", "-1", "--format=%H", "--", "design/accepted.json").strip()
    if accepted:
        diff = run(sys.executable, "scripts/model_diff.py", "--head")
        measured = "from the accepted design"
    else:
        diff = run(sys.executable, "scripts/model_diff.py", base, "--head")
        measured = f"from `{base}`"
    lines = [MARK, f"## Prove: `{sha}`", "", f"_Model diff {measured}._", "", diff.rstrip(), "",
             "### Scenarios", ""]
    last = ROOT / "tests" / ".last-run.json"
    if not last.is_file():
        lines.append("No run recorded: the suite did not finish on this commit.")
    else:
        r = json.loads(last.read_text())
        where = "the full suite" if r.get("full") else "a partial run"
        lines.append(
            f"{r.get('passed', 0)} passed, {r.get('failed', 0)} failed, {r.get('wip', 0)} @wip, "
            f"{r.get('blocked', 0)} @blocked ({where} at {r.get('revision', '?')})."
        )
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
