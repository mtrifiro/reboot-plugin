#!/usr/bin/env python3
"""Tests for the templates' tests/run_progress.py, the recorder the
Reboot band reads: a run that finishes, one stopped with Ctrl-C, by a
hang-up, or by a terminate signal (through Reboot's cleanup hooks, here
a stand-in with the same contract), and one killed outright, which the
band, not the recorder, notices.

Each case runs pytest on a scratch project of two modules whose tests
sleep, so a run can be stopped mid-way. It needs pytest in the Python
that runs it; without, it skips:

    python3 tests/templates/run_progress_test.py
    bin/uv run --no-project --with pytest python tests/templates/run_progress_test.py
"""

import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
RECORDER = ROOT / "skills" / "build" / "templates" / "web-app" / "tests" / "run_progress.py"

try:
    import pytest  # noqa: F401

    HAS_PYTEST = True
except ImportError:
    HAS_PYTEST = False


@unittest.skipUnless(HAS_PYTEST, "pytest isn't installed for this Python")
class RunProgressTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp()
        self.project = Path(self.tmp)
        tests = self.project / "tests"
        tests.mkdir()
        shutil.copy(RECORDER, tests / "run_progress.py")
        (self.project / "pytest.ini").write_text("[pytest]\ntestpaths = tests\n")
        (tests / "conftest.py").write_text(
            "import sys, os\n"
            "sys.path.insert(0, os.path.dirname(__file__))\n"
            "from run_progress import *  # noqa: F401,F403\n"
        )
        # The first module is quick; the second sleeps long enough to stop.
        (tests / "a_test.py").write_text("def test_one():\n    pass\n")
        (tests / "b_test.py").write_text(
            "import time\n\n"
            "def test_slow():\n    time.sleep(30)\n"
        )
        self.file = self.project / ".reboot" / "test-run.json"

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def start(self) -> subprocess.Popen:
        env = {k: v for k, v in os.environ.items() if k != "REBOOT_TEST_RUN"}
        return subprocess.Popen(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"],
            cwd=self.project,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def run_file(self) -> dict:
        return json.loads(self.file.read_text())

    def wait_for_running(self, name: str) -> None:
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            if self.file.exists():
                modules = {m["name"]: m["status"] for m in self.run_file()["modules"]}
                if modules.get(name) == "running":
                    return
            time.sleep(0.1)
        self.fail(f"{name} never started running")

    def with_reboot_cleanup_hooks(self) -> None:
        """A stand-in for `reboot.aio.signals`: cleanups run on SIGTERM,
        then the default handler and the signal again, as Reboot's do."""
        package = self.project / "tests" / "reboot" / "aio"
        package.mkdir(parents=True)
        (package.parent / "__init__.py").write_text("")
        (package / "__init__.py").write_text("")
        (package / "signals.py").write_text(
            "import os, signal\n"
            "_cleanups = []\n"
            "def _handler(signum, frame):\n"
            "    for cleanup in _cleanups:\n"
            "        cleanup()\n"
            "    signal.signal(signum, signal.SIG_DFL)\n"
            "    os.kill(os.getpid(), signum)\n"
            "def install_cleanup(signums, handler):\n"
            "    for signum in signums:\n"
            "        if signal.signal(signum, _handler) not in (signal.SIG_DFL, signal.SIG_IGN, _handler):\n"
            "            raise RuntimeError('Custom signal handlers are not (yet) supported')\n"
            "    _cleanups.append(handler)\n"
        )

    def stop(self, sig: int) -> dict:
        process = self.start()
        self.wait_for_running("b_test")
        process.send_signal(sig)
        process.wait(timeout=30)
        return self.run_file()

    def test_a_finished_run(self) -> None:
        (self.project / "tests" / "b_test.py").write_text("def test_quick():\n    pass\n")
        process = self.start()
        process.wait(timeout=60)
        run = self.run_file()
        self.assertIsNotNone(run["finished_at"])
        self.assertNotIn("stopped", run)
        self.assertEqual([m["status"] for m in run["modules"]], ["passed", "passed"])

    def test_ctrl_c_stops_the_run_and_its_module(self) -> None:
        run = self.stop(signal.SIGINT)
        self.assertIsNotNone(run["finished_at"])
        self.assertTrue(run["stopped"])
        self.assertEqual([m["status"] for m in run["modules"]], ["passed", "stopped"])

    def test_a_hang_up_stops_it_too(self) -> None:
        run = self.stop(signal.SIGHUP)
        self.assertIsNotNone(run["finished_at"])
        self.assertTrue(run["stopped"])
        self.assertEqual([m["status"] for m in run["modules"]], ["passed", "stopped"])

    def test_a_terminate_signal_through_reboots_cleanup_hooks(self) -> None:
        self.with_reboot_cleanup_hooks()
        run = self.stop(signal.SIGTERM)
        self.assertTrue(run["stopped"])
        self.assertEqual([m["status"] for m in run["modules"]], ["passed", "stopped"])

    def test_without_reboot_a_terminate_signal_is_left_to_the_band(self) -> None:
        # No SIGTERM handler of our own: Reboot's harness refuses one.
        run = self.stop(signal.SIGTERM)
        self.assertIsNone(run["finished_at"])

    def test_a_hard_kill_leaves_it_running_for_the_band_to_notice(self) -> None:
        run = self.stop(signal.SIGKILL)
        self.assertIsNone(run["finished_at"])
        self.assertEqual([m["status"] for m in run["modules"]], ["passed", "running"])


if __name__ == "__main__":
    unittest.main()
