#!/usr/bin/env python3
"""Tests for a project's scripts/accent.py: the list marks the current
palette, a switch rewrites the stylesheet's :root and both dark blocks,
the favicon and the placeholder page, an unknown name changes nothing,
and switching back gives the scaffold's files byte for byte.

    python3 tests/templates/accent_test.py
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
TEMPLATES = ROOT / "skills" / "build" / "templates"
COPY = TEMPLATES / "copy.sh"
PALETTES = {p["name"]: p for p in json.loads((TEMPLATES / "palettes.json").read_text())["palettes"]}
VIOLET = {v for scheme in ("light", "dark") for k, v in PALETTES["violet"][scheme].items()
          if k not in ("on-accent", "on-deep", "bg-glow")}


class AccentTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.dest = Path(self.tmp.name) / "proj"
        env = {**os.environ, "REBOOT_ACCENT": "violet", "REBOOT_PORTS": "9955 9855 5355"}
        r = subprocess.run(["sh", str(COPY), "both", str(self.dest), "todo-list", "todo_list",
                            "Todo List"], capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, 0, r.stderr)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def accent(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, "scripts/accent.py", *args], cwd=self.dest,
                              capture_output=True, text=True)

    def files(self) -> dict:
        return {rel: (self.dest / rel).read_text() for rel in (
            "frontend/styles.css", "frontend/web/index.html", "scripts/placeholder.py")}

    def test_list_marks_the_current_palette(self) -> None:
        r = self.accent()
        self.assertEqual(r.returncode, 0, r.stderr)
        lines = r.stdout.splitlines()
        self.assertEqual([line.split()[-5] for line in lines], list(PALETTES))
        self.assertEqual([line for line in lines if line.startswith("*")],
                         [line for line in lines if " violet " in line])

    def test_switch_rewrites_every_scheme_block_and_the_favicon(self) -> None:
        r = self.accent("teal")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Accent: teal", r.stdout)
        teal = PALETTES["teal"]
        files = self.files()
        css = files["frontend/styles.css"]
        for name, value in teal["light"].items():
            self.assertEqual(css.count(f"--{name}: {value}"), 1, f"light --{name}")
        for name, value in teal["dark"].items():
            self.assertEqual(css.count(f"--{name}: {value}"), 2, f"both dark blocks' --{name}")
        self.assertIn(f"fill='%23{teal['light']['accent'][1:]}'", files["frontend/web/index.html"])
        self.assertIn(f"--accent: {teal['dark']['accent']}", files["scripts/placeholder.py"])
        for rel, text in files.items():
            for value in VIOLET:
                self.assertNotIn(value, text, f"{value} left in {rel}")
        self.assertIn("* teal", self.accent().stdout)

    def test_unknown_name_changes_nothing(self) -> None:
        before = self.files()
        r = self.accent("green")
        self.assertEqual(r.returncode, 2)
        self.assertIn("no palette 'green'", r.stderr)
        self.assertEqual(self.files(), before)

    def test_round_trip(self) -> None:
        before = self.files()
        for name in PALETTES:
            self.assertEqual(self.accent(name).returncode, 0, name)
        self.assertEqual(self.accent("violet").returncode, 0)
        self.assertEqual(self.files(), before)


if __name__ == "__main__":
    unittest.main()
