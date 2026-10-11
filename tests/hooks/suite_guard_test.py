#!/usr/bin/env python3
"""Tests for `hooks/suite-guard.sh`: while a project's suite runs
(`tests/.suite-running` names a live pid) it denies regenerating,
restarting, expunging and code edits, from Claude Code's tools and
Codex's `apply_patch`; it is silent for other files, a dead pid, no
sentinel, and outside a project.

    python3 tests/hooks/suite_guard_test.py
"""

import json
import os
import shutil
import subprocess
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
HOOK = os.path.join(ROOT, "hooks/suite-guard.sh")


class SuiteGuardTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp()
        self.project = os.path.join(self.tmp, "app")
        os.makedirs(os.path.join(self.project, "tests"))
        os.makedirs(os.path.join(self.project, "backend", "src"))
        with open(os.path.join(self.project, ".rbtrc"), "w") as f:
            f.write("generate api/\n")

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def running(self, pid: int | None = None) -> None:
        with open(os.path.join(self.project, "tests", ".suite-running"), "w") as f:
            json.dump({"pid": pid or os.getpid()}, f)

    def run_hook(self, tool: str, tool_input: dict, cwd: str | None = None) -> dict | None:
        payload = {"hook_event_name": "PreToolUse", "tool_name": tool,
                   "tool_input": tool_input, "cwd": cwd or self.project}
        r = subprocess.run(["sh", HOOK], input=json.dumps(payload), capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout) if r.stdout.strip() else None

    def assertDenied(self, out: dict | None, *words: str) -> None:
        self.assertIsNotNone(out, "expected a deny")
        decision = out["hookSpecificOutput"]
        self.assertEqual(decision["permissionDecision"], "deny")
        for word in words:
            self.assertIn(word, decision["permissionDecisionReason"])

    def test_denies_generate_and_dev_run_while_the_suite_runs(self) -> None:
        self.running()
        for command in ("uv run rbt generate", "rbt dev run", "cd web && npm run dev",
                        "uv run rbt dev expunge --yes"):
            self.assertDenied(self.run_hook("Bash", {"command": command}), str(os.getpid()),
                              "Method not found!")

    def test_allows_other_commands(self) -> None:
        self.running()
        self.assertIsNone(self.run_hook("Bash", {"command": "uv run pytest tests/a_test.py"}))
        self.assertIsNone(self.run_hook("Bash", {"command": "git status"}))

    def test_denies_a_code_edit_and_allows_a_doc_edit(self) -> None:
        self.running()
        edit = {"file_path": os.path.join(self.project, "backend", "src", "main.py"),
                "old_string": "a", "new_string": "b"}
        self.assertDenied(self.run_hook("Edit", edit), "backend/src/main.py")
        self.assertDenied(self.run_hook("Write", {"file_path": "api/hotel/v1/hotel.py", "content": ""}),
                          "api/hotel/v1/hotel.py")
        self.assertIsNone(self.run_hook("Edit", {"file_path": os.path.join(self.project, "README.md")}))
        self.assertIsNone(self.run_hook("Edit", {"file_path": os.path.join(self.project, "tests", "a.feature")}))

    def test_denies_a_codex_patch(self) -> None:
        self.running()
        patch = "*** Begin Patch\n*** Update File: backend/src/main.py\n@@\n-a\n+b\n*** End Patch\n"
        self.assertDenied(self.run_hook("apply_patch", {"input": patch}), "backend/src/main.py")

    def test_silent_when_the_pid_is_dead_or_there_is_no_run(self) -> None:
        self.running(pid=2 ** 22 - 1)
        self.assertIsNone(self.run_hook("Bash", {"command": "uv run rbt generate"}))
        os.remove(os.path.join(self.project, "tests", ".suite-running"))
        self.assertIsNone(self.run_hook("Bash", {"command": "uv run rbt generate"}))

    def test_silent_outside_a_project(self) -> None:
        self.running()
        self.assertIsNone(self.run_hook("Bash", {"command": "uv run rbt generate"}, cwd=self.tmp))
        self.assertIsNone(self.run_hook("Edit", {"file_path": os.path.join(self.tmp, "backend", "x.py")},
                                        cwd=self.tmp))


if __name__ == "__main__":
    unittest.main()
