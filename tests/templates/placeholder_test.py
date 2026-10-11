#!/usr/bin/env python3
"""Tests for the templates' scripts/placeholder.py, the not-running page:
`serve` answers every request on a free port with a 503 naming the app
and the command that starts it, and does nothing a second time or on a
held port; `stop` frees the port and removes the record, and ends a
waiting watcher; `watch` serves once the watched pid has exited and
the port has freed; REBOOT_NO_PLACEHOLDER=1 and CI turn it off; a web
app's port is the Vite port, an MCP UI's the backend's in `.rbtrc`.

    python3 tests/templates/placeholder_test.py
"""

import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = ROOT / "skills" / "build" / "templates" / "web-app" / "scripts" / "placeholder.py"


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def until(check, seconds: float = 10) -> bool:
    deadline = time.time() + seconds
    while time.time() < deadline:
        if check():
            return True
        time.sleep(0.1)
    return check()


class PlaceholderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp()
        self.project = Path(os.path.realpath(self.tmp)) / "todo-list"
        (self.project / "scripts").mkdir(parents=True)
        shutil.copy(SCRIPT, self.project / "scripts" / "placeholder.py")
        self.port = free_port()
        self.backend_port = free_port()
        (self.project / ".rbtrc").write_text(
            "dev run --application-name=todo-list\ndev run --port=%d\n" % self.backend_port)
        self.web_app()
        self.held: list = []

    def tearDown(self) -> None:
        self.run_script("stop")
        for thing in self.held:
            if isinstance(thing, socket.socket):
                thing.close()
            else:
                thing.kill()
                thing.wait()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def web_app(self) -> None:
        (self.project / "web").mkdir(exist_ok=True)
        (self.project / "web" / "vite.config.ts").write_text(
            "export default defineConfig({\n  server: {\n    host: true,\n"
            "    port: %d,\n    strictPort: true,\n  },\n});\n" % self.port)

    def run_script(self, *args: str, **env: str) -> subprocess.CompletedProcess:
        clean = {k: v for k, v in os.environ.items() if k not in ("CI", "REBOOT_NO_PLACEHOLDER")}
        return subprocess.run([sys.executable, str(self.project / "scripts" / "placeholder.py"), *args],
                              cwd=self.project, env={**clean, **env}, capture_output=True, text=True,
                              timeout=30)

    def record(self):
        try:
            return json.loads((self.project / ".reboot" / "placeholder.json").read_text())
        except (OSError, ValueError):
            return None

    def get(self, port: int, method: str = "GET"):
        request = urllib.request.Request("http://127.0.0.1:%d/some/route" % port, method=method)
        try:
            urllib.request.urlopen(request, timeout=5)
        except urllib.error.HTTPError as error:
            with error:
                return error.code, error.read().decode()
        except OSError:
            return None, ""
        return 200, ""

    def port_is_free(self, port: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            return sock.connect_ex(("127.0.0.1", port)) != 0

    def hold(self, port: int) -> socket.socket:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("127.0.0.1", port))
        sock.listen(1)
        self.held.append(sock)
        return sock

    def test_serve_answers_503_with_the_name_and_the_command(self) -> None:
        r = self.run_script("serve")
        self.assertEqual((r.returncode, r.stdout, r.stderr), (0, "", ""))
        code, body = self.get(self.port)
        self.assertEqual(code, 503)
        self.assertIn("todo-list", body)
        self.assertIn("This app is not running.", body)
        self.assertIn("uv run rbt dev run", body)
        self.assertIn("npm run dev", body)
        self.assertIn('http-equiv="refresh" content="3"', body)
        self.assertIn("prefers-color-scheme: dark", body)
        for dash in ("—", "–"):
            self.assertNotIn(dash, body)
        self.assertEqual(self.get(self.port, "HEAD")[0], 503)
        self.assertEqual(self.get(self.port, "POST")[0], 503)
        self.assertEqual(self.record()["port"], self.port)
        self.assertIn("serving on port %d" % self.port, self.run_script("status").stdout)

    def test_a_second_serve_does_nothing(self) -> None:
        self.run_script("serve")
        first = self.record()
        self.assertIsNotNone(first)
        r = self.run_script("serve")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(self.record(), first)
        self.assertEqual(self.get(self.port)[0], 503)

    def test_serve_on_a_held_port_does_nothing(self) -> None:
        self.hold(self.port)
        r = self.run_script("serve")
        self.assertEqual((r.returncode, r.stdout, r.stderr), (0, "", ""))
        self.assertIsNone(self.record())

    def test_stop_frees_the_port_and_removes_the_record(self) -> None:
        self.run_script("serve")
        self.assertEqual(self.get(self.port)[0], 503)
        r = self.run_script("stop")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(self.port_is_free(self.port))
        self.assertIsNone(self.record())
        self.assertEqual(self.run_script("stop").returncode, 0, "nothing running is fine")
        self.assertIn("not running", self.run_script("status").stdout)

    def test_watch_serves_after_the_pid_exits_and_the_port_frees(self) -> None:
        app = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(1.5)"])
        held = self.hold(self.port)
        r = self.run_script("watch", "--pid", str(app.pid), "--for", "60")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.record()["watching"], app.pid)
        self.assertIn("waiting for pid %d" % app.pid, self.run_script("status").stdout)
        app.wait()
        time.sleep(3)
        self.assertEqual(self.record()["watching"], app.pid, "still waiting: the port is held")
        held.close()
        self.assertTrue(until(lambda: self.get(self.port)[0] == 503), "serves once the port frees")
        self.assertNotIn("watching", self.record())

    def test_stop_ends_a_waiting_watcher(self) -> None:
        app = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
        self.held.append(app)
        self.run_script("watch", "--pid", str(app.pid))
        watcher = self.record()["pid"]
        self.run_script("stop")
        self.assertIsNone(self.record())
        self.assertTrue(until(lambda: subprocess.run(
            ["ps", "-o", "command=", "-p", str(watcher)], capture_output=True, text=True
        ).stdout.find("placeholder.py") < 0, 5))

    def test_off_with_reboot_no_placeholder_and_ci(self) -> None:
        for env in ({"REBOOT_NO_PLACEHOLDER": "1"}, {"CI": "true"}):
            for args in (("serve",), ("status",), ("stop",), ("watch", "--pid", "1")):
                r = self.run_script(*args, **env)
                self.assertEqual((r.returncode, r.stdout), (0, ""), (env, args))
            self.assertIsNone(self.record())
            self.assertTrue(self.port_is_free(self.port))

    def test_the_port_each_layout_visits(self) -> None:
        self.assertIn("(port %d)" % self.port, self.run_script("status").stdout, "web app: Vite's")
        (self.project / "frontend").mkdir()
        self.assertIn("(port %d)" % self.backend_port, self.run_script("status").stdout,
                      "MCP UI or both: the backend's")
        (self.project / ".rbtrc").write_text("dev run --application-name=todo-list\n")
        self.assertIn("(port 9991)", self.run_script("status").stdout, "the default")


if __name__ == "__main__":
    unittest.main()
