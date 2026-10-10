#!/usr/bin/env python3
"""Tests for the templates' scripts/test.sh, tests/last_run.py and
.githooks/pre-push together: `changed` runs the modules of the feature
files that changed and nothing when none did; a run records the tree it
ran on and whether it was full; the suite's pid is in
tests/.suite-running while it runs and gone after; and a push to main
passes only for the tree the last full run passed on.

Each case runs pytest on a scratch git repository. It needs pytest in
the Python that runs it; without, it skips:

    python3 tests/templates/test_sh_test.py
    bin/uv run --no-project --with pytest python tests/templates/test_sh_test.py
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
TEMPLATE = ROOT / "skills" / "build" / "templates" / "web-app"

try:
    import pytest  # noqa: F401

    HAS_PYTEST = True
except ImportError:
    HAS_PYTEST = False


@unittest.skipUnless(HAS_PYTEST, "pytest isn't installed for this Python")
class TestShTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp()
        self.project = Path(self.tmp)
        (self.project / "scripts").mkdir()
        (self.project / "tests").mkdir()
        (self.project / ".githooks").mkdir()
        shutil.copy(TEMPLATE / "scripts" / "test.sh", self.project / "scripts" / "test.sh")
        shutil.copy(TEMPLATE / "tests" / "last_run.py", self.project / "tests" / "last_run.py")
        shutil.copy(TEMPLATE / ".githooks" / "pre-push", self.project / ".githooks" / "pre-push")
        (self.project / "pytest.ini").write_text("[pytest]\ntestpaths = tests\n")
        (self.project / ".gitignore").write_text(
            "tests/.last-run.json\ntests/.suite-running\n__pycache__/\n.pytest_cache/\n")
        (self.project / "tests" / "conftest.py").write_text(
            "import sys, os\n"
            "sys.path.insert(0, os.path.dirname(__file__))\n"
            "from last_run import pytest_sessionstart, pytest_terminal_summary, pytest_unconfigure  # noqa\n"
        )
        (self.project / "tests" / "orders.feature").write_text("Feature: Orders\n")
        (self.project / "tests" / "orders_test.py").write_text(
            "import json, os\n"
            "# scenarios('orders.feature')\n"
            "def test_running_sentinel_names_this_pytest():\n"
            "    record = json.load(open(os.path.join(os.path.dirname(__file__), '.suite-running')))\n"
            "    assert record['pid'] == os.getpid()\n"
        )
        (self.project / "tests" / "kitchen.feature").write_text("Feature: Kitchen\n")
        (self.project / "tests" / "kitchen_test.py").write_text(
            "# scenarios('kitchen.feature')\ndef test_kitchen():\n    pass\n")
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.email", "t@example.com")
        self.git("config", "user.name", "t")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "scaffold")
        self.env = {**os.environ, "PYTEST": f"{sys.executable} -m pytest -q -p no:cacheprovider"}

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def git(self, *args: str) -> str:
        return subprocess.run(["git", *args], cwd=self.project, capture_output=True,
                              text=True, check=True).stdout.strip()

    def test_sh(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(["sh", "scripts/test.sh", *args], cwd=self.project,
                              env=self.env, capture_output=True, text=True)

    def record(self) -> dict:
        return json.loads((self.project / "tests" / ".last-run.json").read_text())

    def test_changed_runs_nothing_when_no_feature_changed(self) -> None:
        r = self.test_sh("changed")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("nothing to run", r.stdout)
        self.assertFalse((self.project / "tests" / ".last-run.json").exists())

    def test_changed_runs_the_modules_of_the_changed_features(self) -> None:
        (self.project / "tests" / "orders.feature").write_text("Feature: Orders\n  Scenario: one\n")
        r = self.test_sh("changed")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("1 passed", r.stdout)
        self.assertNotIn("test_kitchen", r.stdout)
        self.assertFalse(self.record()["full"], "a narrowed run is not full")

    def test_changed_refuses_a_feature_no_module_runs(self) -> None:
        (self.project / "tests" / "stray.feature").write_text("Feature: Stray\n")
        r = self.test_sh("changed")
        self.assertEqual(r.returncode, 1)
        self.assertIn("stray.feature", r.stderr)

    def test_full_records_the_tree_and_the_sentinel_goes(self) -> None:
        r = self.test_sh("full")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("2 passed", r.stdout)
        record = self.record()
        self.assertTrue(record["full"])
        self.assertEqual(record["tree"], self.git("rev-parse", "HEAD^{tree}"))
        self.assertFalse((self.project / "tests" / ".suite-running").exists())

    def test_pre_push_passes_the_tested_tree_and_refuses_another(self) -> None:
        self.test_sh("full")
        sha = self.git("rev-parse", "HEAD")
        push = f"refs/heads/main {sha} refs/heads/main {'0' * 40}\n"
        r = self.hook(push)
        self.assertEqual(r.returncode, 0, r.stderr)
        (self.project / "tests" / "kitchen.feature").write_text("Feature: Kitchen\n  Rule: new\n")
        self.git("commit", "-qam", "a rule")
        sha2 = self.git("rev-parse", "HEAD")
        r = self.hook(f"refs/heads/main {sha2} refs/heads/main {sha}\n")
        self.assertEqual(r.returncode, 1)
        self.assertIn("not the one the last full run passed on", r.stderr)
        r = self.hook(f"refs/heads/feature {sha2} refs/heads/feature {sha}\n")
        self.assertEqual(r.returncode, 0, "a branch is not gated")

    def test_pre_push_refuses_a_partial_or_failed_run(self) -> None:
        (self.project / "tests" / "orders.feature").write_text("Feature: Orders\n  Scenario: one\n")
        r = self.test_sh("changed")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.git("commit", "-qam", "scenario")
        sha = self.git("rev-parse", "HEAD")
        r = self.hook(f"refs/heads/main {sha} refs/heads/main {'0' * 40}\n")
        self.assertEqual(r.returncode, 1)
        self.assertIn("partial", r.stderr)

    def hook(self, stdin: str) -> subprocess.CompletedProcess:
        return subprocess.run(["sh", ".githooks/pre-push", "origin", "git@example.com:x.git"],
                              cwd=self.project, input=stdin, capture_output=True, text=True)


if __name__ == "__main__":
    unittest.main()
