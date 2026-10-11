#!/usr/bin/env python3
"""Tests for `hooks-handlers/session-start.sh`: the PATH line goes into
the env file once, however often SessionStart fires, and nothing is
written without an env file; in a Reboot project with
scripts/placeholder.py it runs `placeholder.py serve`, without waiting
on it or failing for it.

    python3 tests/hooks/session_start_test.py
"""

import os
import subprocess
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
HOOK = os.path.join(ROOT, "hooks-handlers/session-start.sh")


class SessionStartTest(unittest.TestCase):
    def run_hook(self, **env: str) -> subprocess.CompletedProcess:
        environment = {k: v for k, v in os.environ.items()
                       if k not in ("CLAUDE_ENV_FILE", "CLAUDE_PLUGIN_ROOT", "CLAUDE_PROJECT_DIR")}
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

    def test_a_reboot_project_gets_its_placeholder_served(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = os.path.join(tmp, "app")
            os.makedirs(os.path.join(project, "scripts"))
            log = os.path.join(project, "scripts", "placeholder.log")
            with open(os.path.join(project, "scripts", "placeholder.py"), "w") as f:
                f.write("import sys\nopen(%r, 'a').write(' '.join(sys.argv[1:]) + '\\n')\n"
                        "print('hidden')\nsys.exit(3)\n" % log)
            r = self.run_hook(CLAUDE_PROJECT_DIR=project)
            self.assertEqual((r.returncode, r.stdout), (0, ""), "no .rbtrc, no call")
            time.sleep(0.5)
            self.assertFalse(os.path.exists(log))
            open(os.path.join(project, ".rbtrc"), "w").close()
            env_file = os.path.join(tmp, "env")
            r = self.run_hook(CLAUDE_PROJECT_DIR=project, CLAUDE_ENV_FILE=env_file,
                              CLAUDE_PLUGIN_ROOT="/opt/plugin")
            self.assertEqual((r.returncode, r.stdout, r.stderr), (0, "", ""))
            deadline = time.time() + 5
            while not os.path.exists(log) and time.time() < deadline:
                time.sleep(0.05)
            with open(log) as f:
                self.assertEqual(f.read(), "serve\n")
            with open(env_file) as f:
                self.assertIn("/opt/plugin/bin", f.read(), "the PATH line still written")


if __name__ == "__main__":
    unittest.main()
