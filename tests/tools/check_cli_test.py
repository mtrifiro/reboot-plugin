#!/usr/bin/env python3
"""Tests for `tools/check-cli.py`'s placeholder handling in inline
commands: a flag whose value is a placeholder keeps the flag, so it is
still checked against the CLI; a token that is only a placeholder is
dropped; a command with none is unchanged.

    python3 tests/tools/check_cli_test.py
"""

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
spec = importlib.util.spec_from_file_location("check_cli", ROOT / "tools" / "check-cli.py")
check_cli = importlib.util.module_from_spec(spec)
sys.modules["check_cli"] = check_cli  # dataclasses look the module up
spec.loader.exec_module(check_cli)
strip = check_cli.strip_placeholders


class StripPlaceholdersTest(unittest.TestCase):
    def test_flag_with_placeholder_value_keeps_the_flag(self) -> None:
        self.assertEqual(strip("dev run --application-name=<name>").split(),
                         ["dev", "run", "--application-name"])

    def test_spaced_and_ellipsis_values(self) -> None:
        self.assertEqual(strip("cloud up --name=<app name> --x=…").split(),
                         ["cloud", "up", "--name", "--x"])
        self.assertEqual(strip("inspect --admin-credential=...").split(),
                         ["inspect", "--admin-credential"])

    def test_placeholder_only_tokens_are_dropped(self) -> None:
        self.assertEqual(strip("generate <dir> --python=backend/api ...").split(),
                         ["generate", "--python=backend/api"])

    def test_plain_command_unchanged(self) -> None:
        self.assertEqual(strip("dev run --watch=main.py"), "dev run --watch=main.py")

    def test_bad_flag_behind_a_placeholder_is_still_found(self) -> None:
        # The flag survives stripping, so check() sees it.
        self.assertIn("--no-such-flag", strip("dev run --no-such-flag=<x>"))


if __name__ == "__main__":
    unittest.main()
