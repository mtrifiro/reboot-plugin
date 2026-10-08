"""Records how far a test run is in `.reboot/test-run.json` at the
project root, rewritten as each module starts and ends and at a test's
first failure, for the Reboot band above Claude Code's prompt to show
how far the run is and when it should end. Imported by `conftest.py`;
the file's shape is in the python skill's
`references/testing-project-setup.md` ("Test-run progress").

A runner that records the run itself, such as a suite script running
one module per pytest, sets `REBOOT_TEST_RUN=external`, and this leaves
the file alone."""

import json
import os
import time
from datetime import datetime
from pathlib import Path

ENABLED = os.environ.get("REBOOT_TEST_RUN") != "external"

# The run as the file records it, where it goes, and the module running:
# its index into the run's modules and when it started (monotonic).
_run: dict | None = None
_path: Path | None = None
_index: dict[str, int] = {}
_current: tuple[int, float] | None = None
_failed_ids: set[str] = set()


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _module(nodeid: str) -> str:
    return Path(nodeid.split("::")[0]).stem


def _write() -> None:
    # Whole or not at all: a reader never sees half a file.
    assert _path is not None
    _path.parent.mkdir(exist_ok=True)
    partial = _path.with_suffix(".json.partial")
    partial.write_text(json.dumps(_run, indent=2))
    os.replace(partial, _path)


def _end_current() -> None:
    global _current
    if _run is None or _current is None:
        return
    index, began = _current
    entry = _run["modules"][index]
    entry["status"] = "failed" if entry["failed"] else "passed"
    entry["seconds"] = round(time.monotonic() - began, 1)
    _current = None


def pytest_collection_finish(session) -> None:
    """Every module the run will run, pending, in the order it runs them."""
    global _run, _path, _index
    config = session.config
    # Not for a collection alone, nor for an xdist worker (its controller records).
    if not ENABLED or config.option.collectonly or hasattr(config, "workerinput"):
        return
    names = list(dict.fromkeys(_module(item.nodeid) for item in session.items))
    if not names:
        return
    _path = Path(config.rootpath) / ".reboot" / "test-run.json"
    _index = {name: i for i, name in enumerate(names)}
    _run = {
        "started_at": _now(),
        "finished_at": None,
        "modules": [{"name": name, "status": "pending"} for name in names],
    }
    _write()


def pytest_runtest_logstart(nodeid: str, location) -> None:
    """A module starts running as its first test starts; the one before ends."""
    global _current
    if _run is None:
        return
    index = _index.get(_module(nodeid))
    if index is None or (_current is not None and _current[0] == index):
        return
    _end_current()
    _run["modules"][index].update(status="running", passed=0, failed=0, started_at=_now())
    _current = (index, time.monotonic())
    _write()


def pytest_runtest_logreport(report) -> None:
    """Counts each test once; a failure is written at once."""
    if _run is None or _current is None:
        return
    entry = _run["modules"][_current[0]]
    if report.failed and report.nodeid not in _failed_ids:
        _failed_ids.add(report.nodeid)
        entry["failed"] += 1
        _write()
    elif report.when == "call" and report.passed:
        entry["passed"] += 1


def pytest_sessionfinish(session, exitstatus) -> None:
    """The last module ends and the run with it; modules never reached stay pending."""
    if _run is None:
        return
    _end_current()
    _run["finished_at"] = _now()
    _write()
