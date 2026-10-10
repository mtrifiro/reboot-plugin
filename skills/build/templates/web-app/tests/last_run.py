"""Records the last test run's results in `tests/.last-run.json`, as
evidence for the Reboot Flywheel's Prove stage: the pull request body
and the release record (`scripts/deploy.sh`) say which scenarios passed
at which revision (`build/references/evidence.md`). Imported by
`conftest.py`; git-ignored.

    {"when": "...", "revision": "abc1234", "dirty": false, "full": true,
     "passed": 12, "failed": 0, "wip": 2, "blocked": 1}

`full` is false when the run was narrowed (a path, `-k`, `-m`): a
partial run is not evidence for a release. `wip` counts scenarios
tagged `@wip` that ran (they pass or fail like any other); `blocked`
counts `@blocked` ones, which are skipped with their reason."""

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

PATH = Path(__file__).resolve().parent / ".last-run.json"


def _git(*args: str) -> str:
    try:
        return subprocess.run(
            ["git", *args], cwd=PATH.parent, capture_output=True, text=True
        ).stdout.strip()
    except OSError:
        return ""


def pytest_terminal_summary(terminalreporter, exitstatus, config) -> None:  # type: ignore[no-untyped-def]
    stats = terminalreporter.stats
    calls = [
        r
        for key in ("passed", "failed")
        for r in stats.get(key, [])
        if getattr(r, "when", "") == "call"
    ]
    failed = sum(1 for r in calls if r.outcome == "failed") + len(stats.get("error", []))
    skipped = stats.get("skipped", [])
    args = list(config.invocation_params.args)
    narrowed = any(not a.startswith("-") for a in args) or any(
        a in ("-k", "-m") or a.startswith(("-k=", "-m=")) for a in args
    )
    record = {
        "when": datetime.now().astimezone().isoformat(timespec="seconds"),
        "revision": _git("rev-parse", "--short", "HEAD"),
        "dirty": bool(_git("status", "--porcelain", "--", "api", "backend", "tests", "web", "frontend")),
        "full": not narrowed,
        "passed": sum(1 for r in calls if r.outcome == "passed"),
        "failed": failed,
        "wip": sum(1 for r in calls if "wip" in r.keywords),
        "blocked": sum(1 for r in skipped if "blocked" in r.keywords),
    }
    partial = PATH.with_suffix(".json.partial")
    partial.write_text(json.dumps(record, indent=2) + "\n")
    os.replace(partial, PATH)
