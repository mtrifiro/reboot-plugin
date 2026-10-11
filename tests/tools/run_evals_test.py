#!/usr/bin/env python3
"""Tests for `tools/run-evals.sh`'s flags, against a fake `claude` that
only records what it was asked to run: a selected case with a fixture
gets `--scaffold`, by `--case` glob or `--tag`; a selection with no
fixture does not; an explicit `--scaffold` or `--no-scaffold` is left
alone; the wrapper always gets `--trust-plugin` and a Sonnet judge.

    python3 tests/tools/run_evals_test.py
"""

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = ROOT / "tools" / "run-evals.sh"

FAKE_CLAUDE = '#!/bin/sh\nprintf "%s\\n" "$@" > "$CLAUDE_ARGS"\n'


class RunEvalsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        bindir = self.tmp / "bin"
        bindir.mkdir()
        fake = bindir / "claude"
        fake.write_text(FAKE_CLAUDE)
        fake.chmod(0o755)
        self.args_file = self.tmp / "args"
        self.env = dict(
            os.environ,
            PATH=f"{bindir}:{os.environ['PATH']}",
            CLAUDE_ARGS=str(self.args_file),
            TMPDIR=str(self.tmp),
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_with(self, *flags: str) -> list:
        subprocess.run(
            ["bash", str(SCRIPT), *flags],
            env=self.env,
            capture_output=True,
            text=True,
            check=True,
        )
        return self.args_file.read_text().split("\n")[:-1]

    def test_case_with_fixture_gets_scaffold(self) -> None:
        self.assertIn("--scaffold", self.run_with("--case", "workflow-recorded"))

    def test_case_glob_with_fixture_gets_scaffold(self) -> None:
        self.assertIn("--scaffold", self.run_with("--case=workflow-*"))

    def test_tag_with_fixture_gets_scaffold(self) -> None:
        self.assertIn("--scaffold", self.run_with("--tag", "workflow"))

    def test_every_case_gets_scaffold(self) -> None:
        self.assertIn("--scaffold", self.run_with("--runs", "1"))

    def test_case_without_fixture_gets_none(self) -> None:
        args = self.run_with("--case", "route-mcp")
        self.assertNotIn("--scaffold", args)

    def test_tag_without_fixture_gets_none(self) -> None:
        args = self.run_with("--tag", "routing")
        self.assertNotIn("--scaffold", args)

    def test_explicit_no_scaffold_is_kept(self) -> None:
        args = self.run_with("--case", "workflow-recorded", "--no-scaffold")
        self.assertNotIn("--scaffold", args)
        self.assertIn("--no-scaffold", args)

    def test_explicit_scaffold_is_not_doubled(self) -> None:
        args = self.run_with("--scaffold", "--tag", "workflow")
        self.assertEqual(args.count("--scaffold"), 1)

    def test_trust_and_judge_defaults(self) -> None:
        args = self.run_with("--case", "route-mcp")
        self.assertEqual(args[:3], ["plugin", "eval", "."])
        self.assertIn("--trust-plugin", args)
        self.assertEqual(args[args.index("--judge-model") + 1], "sonnet")


if __name__ == "__main__":
    unittest.main()
