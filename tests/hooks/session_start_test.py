#!/usr/bin/env python3
"""Tests for `hooks-handlers/session-start.sh`: the PATH line goes into
the env file once, however often SessionStart fires, and nothing is
written without an env file.

    python3 tests/hooks/session_start_test.py
"""

import os
import subprocess
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
HOOK = os.path.join(ROOT, "hooks-handlers/session-start.sh")


class SessionStartTest(unittest.TestCase):
    def run_hook(self, **env: str) -> subprocess.CompletedProcess:
        environment = {k: v for k, v in os.environ.items()
                       if k not in ("CLAUDE_ENV_FILE", "CLAUDE_PLUGIN_ROOT")}
        environment.update(env)
        return subprocess.run(["bash", HOOK], input="{}", env=environment,
                              capture_output=True, text=True)

    def test_the_path_line_is_written_once(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env_file = os.path.join(tmp, "env")
            with open(env_file, "w") as f:
                f.write("export OTHER=1\n")
            for _ in range(3):
                r = self.run_hook(CLAUDE_ENV_FILE=env_file, CLAUDE_PLUGIN_ROOT="/opt/plugin")
                self.assertEqual(r.returncode, 0, r.stderr)
            with open(env_file) as f:
                lines = f.read().splitlines()
            self.assertEqual(lines, ["export OTHER=1", 'export PATH="/opt/plugin/bin:$PATH"'])

    def test_a_new_env_file_and_none(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env_file = os.path.join(tmp, "env")
            r = self.run_hook(CLAUDE_ENV_FILE=env_file, CLAUDE_PLUGIN_ROOT="/opt/plugin")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertTrue(os.path.exists(env_file))
        r = self.run_hook(CLAUDE_PLUGIN_ROOT="/opt/plugin")
        self.assertEqual((r.returncode, r.stdout), (0, ""))


if __name__ == "__main__":
    unittest.main()
