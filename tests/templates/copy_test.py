#!/usr/bin/env python3
"""Tests for skills/build/templates/copy.sh: a plain copy, the refusal,
and `--merge` (the build flow's Step 2: keep the project's files,
replace the dashboard's stubs).

    python3 tests/templates/copy_test.py
"""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
COPY = ROOT / "skills" / "build" / "templates" / "copy.sh"


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["sh", str(COPY), *args], capture_output=True, text=True)


class CopyTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.dest = Path(self.tmp.name) / "proj"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_plain_copy_fills_placeholders_and_renames(self) -> None:
        r = run("web-app", str(self.dest), "todo-list", "todo_list", "Todo List")
        self.assertEqual(r.returncode, 0, r.stderr)
        api = self.dest / "api" / "todo_list" / "v1" / "todo_list.py"
        self.assertTrue(api.is_file(), "the API file is renamed")
        self.assertIn('name = "todo-list"', (self.dest / "pyproject.toml").read_text())
        self.assertIn("--application-name=todo-list", (self.dest / ".rbtrc").read_text())
        leftovers = subprocess.run(
            ["grep", "-rl", r"__project__\|__app__\|__Title__\|__Initial__", str(self.dest)],
            capture_output=True, text=True).stdout
        self.assertEqual(leftovers, "", "no placeholder survives")
        junk = [p for p in self.dest.rglob("*") if p.name in (
            "__pycache__", ".mypy_cache", ".pytest_cache", ".reboot", ".last-run.json")]
        self.assertEqual(junk, [], "build and test leftovers in the template are not copied")

    def test_refuses_a_project_without_merge(self) -> None:
        self.dest.mkdir()
        (self.dest / ".rbtrc").write_text("generate api/\n")
        r = run("web-app", str(self.dest), "todo-list", "todo_list", "Todo List")
        self.assertEqual(r.returncode, 1)
        self.assertIn("already has an .rbtrc", r.stderr)
        self.assertEqual(os.listdir(self.dest), [".rbtrc"], "nothing was written")

    def test_merge_keeps_the_project_and_replaces_the_stubs(self) -> None:
        # Step 1 and the dashboard skill have been here.
        api_dir = self.dest / "api" / "todo_list" / "v1"
        api_dir.mkdir(parents=True)
        (api_dir / "todo_list.py").write_text("# the real API\n")
        (self.dest / ".rbtrc").write_text("generate api/\n")
        (self.dest / "pyproject.toml").write_text('[project]\nname = "stub"\n')
        (self.dest / ".python-version").write_text("3.12\n")
        (self.dest / "CLAUDE.md").write_text("# my notes\n")

        r = run("--merge", "web-app", str(self.dest), "todo-list", "todo_list", "Todo List")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual((api_dir / "todo_list.py").read_text(), "# the real API\n",
                         "Step 1's API file is kept, not the sample")
        self.assertEqual((self.dest / "CLAUDE.md").read_text(), "# my notes\n")
        self.assertIn("--application-name=todo-list", (self.dest / ".rbtrc").read_text(),
                      "the stub .rbtrc is replaced by the template's")
        self.assertIn('name = "todo-list"', (self.dest / "pyproject.toml").read_text())
        self.assertIn("kept api/todo_list/v1/todo_list.py", r.stdout)
        self.assertIn("kept CLAUDE.md", r.stdout)
        self.assertIn("replaced .rbtrc", r.stdout)
        self.assertTrue((self.dest / "backend" / "src" / "main.py").is_file(),
                        "the rest of the template arrives")
        self.assertFalse(list(self.dest.rglob("*__app__*")), "no placeholder path survives")
        leftovers = subprocess.run(
            ["grep", "-rl", r"__project__\|__app__\|__Title__\|__Initial__", str(self.dest)],
            capture_output=True, text=True).stdout
        self.assertEqual(leftovers, "", "no placeholder survives")


if __name__ == "__main__":
    unittest.main()
