"""Records how far a test run is in `.reboot/test-run.json` at the
project root, rewritten as each module starts and ends and at a test's
first failure, for the Reboot band above Claude Code's prompt to show
how far the run is and when it should end. A run stopped before its end
(Ctrl-C, or a terminate or hang-up signal: a timeout, a closed terminal,
an agent stopping a background run) is written as stopped, its running
module too; a terminate signal only in a Reboot project, through
Reboot's cleanup hooks. A hard kill can't be caught; the band notices that one
itself once the run is gone from the process list. Imported by `conftest.py`;
the file's shape is in the python skill's
`references/testing-project-setup.md` ("Test-run progress").

A runner that records the run itself, such as a suite script running
one module per pytest, sets `REBOOT_TEST_RUN=external`, and this leaves
the file alone."""

import json
import os
import signal
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
_skipped_ids: set[str] = set()
# The handlers a stop signal had before ours, to hand it back to.
_previous: dict[int, object] = {}
# Pytest's exit status for a run stopped by Ctrl-C.
_INTERRUPTED = 2


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


def _end_current(stopped: bool = False) -> None:
    global _current
    if _run is None or _current is None:
        return
    index, began = _current
    entry = _run["modules"][index]
    entry["status"] = "stopped" if stopped else "failed" if entry["failed"] else "passed"
    entry["seconds"] = round(time.monotonic() - began, 1)
    _current = None


def _end_run(stopped: bool) -> None:
    """The run ends: finished, or stopped with its running module."""
    if _run is None or _run["finished_at"] is not None:
        return
    _end_current(stopped)
    _run["finished_at"] = _now()
    if stopped:
        _run["stopped"] = True
    _write()


def _on_stop_signal(signum: int, frame) -> None:
    """Records the stop, then lets the signal do what it would have."""
    try:
        _end_run(stopped=True)
    finally:
        signal.signal(signum, _previous.pop(signum, signal.SIG_DFL))  # type: ignore[arg-type]
        os.kill(os.getpid(), signum)


def _catch_stop_signals() -> None:
    """A terminate signal through Reboot's own cleanup hooks: its test
    harness refuses to start beside any other SIGTERM handler. A hang-up,
    which Reboot leaves alone, with ours, unless the run ignores it
    (`nohup`)."""
    try:
        from reboot.aio.signals import install_cleanup

        install_cleanup([signal.SIGTERM], lambda: _end_run(stopped=True))
    except Exception:
        pass  # Not a Reboot project, or no signals here: Ctrl-C still counts.
    signum = getattr(signal, "SIGHUP", None)
    if signum is None or signal.getsignal(signum) is signal.SIG_IGN:
        return
    try:
        _previous[signum] = signal.signal(signum, _on_stop_signal)
    except ValueError:  # not the main thread
        pass


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
    _catch_stop_signals()


def pytest_runtest_logstart(nodeid: str, location) -> None:
    """A module starts running as its first test starts; the one before ends."""
    global _current
    if _run is None:
        return
    index = _index.get(_module(nodeid))
    if index is None or (_current is not None and _current[0] == index):
        return
    _end_current()
    _run["modules"][index].update(status="running", passed=0, failed=0, skipped=0, started_at=_now())
    _current = (index, time.monotonic())
    _write()


def pytest_runtest_logreport(report) -> None:
    """Counts each test once: passed, failed or skipped; a failure is written at once."""
    if _run is None or _current is None:
        return
    entry = _run["modules"][_current[0]]
    if report.failed and report.nodeid not in _failed_ids:
        _failed_ids.add(report.nodeid)
        entry["failed"] += 1
        _write()
    elif report.skipped and report.nodeid not in _skipped_ids:
        _skipped_ids.add(report.nodeid)
        entry["skipped"] += 1
    elif report.when == "call" and report.passed:
        entry["passed"] += 1


def pytest_sessionfinish(session, exitstatus) -> None:
    """The last module ends and the run with it; modules never reached
    stay pending. Ctrl-C stops the run and its running module."""
    _end_run(stopped=int(exitstatus) == _INTERRUPTED)
