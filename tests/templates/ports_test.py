#!/usr/bin/env python3
"""Tests for the ports copy.sh gives a project: a set of its own from
the project name, the next free set when one is held, the ones a merge
keeps, and every file that names a port rewritten together.

    python3 tests/templates/ports_test.py
"""

import os
import socket
import subprocess
import tempfile
import unittest
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
COPY = ROOT / "skills" / "build" / "templates" / "copy.sh"


def run(*args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    clean = {k: v for k, v in os.environ.items() if k != "REBOOT_PORTS"}
    return subprocess.run(["sh", str(COPY), *args], capture_output=True, text=True,
                          env={**clean, **(env or {})})


def ports_of(project: str) -> tuple[int, int, int]:
    r = run("--ports", project)
    assert r.returncode == 0, r.stderr
    b, d, v = (int(x) for x in r.stdout.split())
    return b, d, v


class PortsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.dest = Path(self.tmp.name) / "proj"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_a_set_of_the_projects_own_in_each_range(self) -> None:
        b, d, v = ports_of("todo-list")
        self.assertEqual((b, d, v), ports_of("todo-list"), "the same project gets the same set")
        self.assertTrue(9900 <= b < 9980 and 9800 <= d < 9880 and 5300 <= v < 5380, (b, d, v))
        self.assertEqual((b - 9900, d - 9800, v - 5300), ((b - 9900),) * 3, "one offset for the three")
        self.assertNotEqual(ports_of("todo-list"), ports_of("inventory"), "two projects, two sets")

    def test_a_held_port_moves_the_whole_set_on(self) -> None:
        start = zlib.crc32(b"todo-list") % 80
        b, d, v = ports_of("todo-list")
        if b - 9900 != start:
            self.skipTest("the first candidate is already held on this machine")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as held:
            held.bind(("127.0.0.1", b))
            held.listen(1)
            b2, d2, v2 = ports_of("todo-list")
        self.assertNotEqual(b2, b)
        self.assertEqual((b2 - 9900, d2 - 9800, v2 - 5300), ((b2 - 9900),) * 3)

    def test_every_file_that_names_a_port_is_rewritten(self) -> None:
        r = run("web-app", str(self.dest), "todo-list", "todo_list", "Todo List",
                env={"REBOOT_PORTS": "9955 9855 5355"})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Ports: backend 9955, dashboard 9855, Vite 5355", r.stdout)
        rbtrc = (self.dest / ".rbtrc").read_text()
        self.assertIn("dev run --port=9955", rbtrc)
        self.assertIn("dev run --dashboard-port=9855", rbtrc)
        self.assertIn("dashboard --port=9855", rbtrc)
        self.assertIn("localhost:9955", (self.dest / "web" / ".env.development").read_text())
        self.assertIn("port: 5355", (self.dest / "web" / "vite.config.ts").read_text())
        self.assertIn("localhost:5355", (self.dest / "scripts" / "screenshots.py").read_text())
        for leftover in ("9991", "9871", "5273"):
            for path in (".rbtrc", "web/.env.development", "web/vite.config.ts", "scripts/screenshots.py"):
                self.assertNotIn(leftover, (self.dest / path).read_text(), f"{leftover} left in {path}")

    def test_both_template_env_and_envoy_vite_port(self) -> None:
        r = run("both", str(self.dest), "todo-list", "todo_list", "Todo List",
                env={"REBOOT_PORTS": "9955 9855 5355"})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("localhost:9955", (self.dest / "frontend" / "web" / ".env.development").read_text())
        self.assertIn("--frontend-host=http://localhost:5355", (self.dest / ".rbtrc").read_text())
        self.assertIn('"5355"', (self.dest / "frontend" / "vite.config.ts").read_text())
        self.assertIn("localhost:9955/__/frontend/web", (self.dest / "scripts" / "screenshots.py").read_text())

    def test_merge_keeps_the_ports_the_project_chose(self) -> None:
        self.dest.mkdir()
        (self.dest / ".rbtrc").write_text("generate api/\ndev run --port=9933\ndashboard --port=9833\n")
        (self.dest / "pyproject.toml").write_text('[project]\nname = "stub"\n')
        r = run("--merge", "web-app", str(self.dest), "todo-list", "todo_list", "Todo List")
        self.assertEqual(r.returncode, 0, r.stderr)
        rbtrc = (self.dest / ".rbtrc").read_text()
        self.assertIn("dev run --port=9933", rbtrc)
        self.assertIn("dev run --dashboard-port=9833", rbtrc)
        self.assertIn("dashboard --port=9833", rbtrc)
        self.assertIn("localhost:9933", (self.dest / "web" / ".env.development").read_text())
        self.assertIn("Vite 53", r.stdout, "the Vite port is still chosen")


if __name__ == "__main__":
    unittest.main()
