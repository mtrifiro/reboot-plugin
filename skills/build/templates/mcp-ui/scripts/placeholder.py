"""Hold the port the user visits while the app is down, with a page
saying so, and step aside the moment the app starts.

    python3 scripts/placeholder.py serve     # start it when the port is free
    python3 scripts/placeholder.py stop      # end it (and a waiting watcher)
    python3 scripts/placeholder.py watch --pid N [--for 600]
    python3 scripts/placeholder.py status

The port: a web app's (a `web/` and no `frontend/`) is the Vite port in
`web/vite.config.ts`; an MCP UI's, and both's, is the backend's, `dev
run --port=` in `.rbtrc` (9991 when it names none). Every request gets
a 503 and one small page: the app's name, that it is not running, the
command that starts it, and a reload every 3 s, so the tab becomes the
app when it comes up. `serve` does nothing when the port is held.
`watch` waits for pid N (the plugin's `rbt` shim passes `rbt dev run`'s)
to exit, then for the port to free, then serves. The record is
`.reboot/placeholder.json`. The plugin's `rbt` shim stops it before
`rbt dev run`, `npm run dev` before Vite (`predev`), and its
SessionStart hook serves it. Off when REBOOT_NO_PLACEHOLDER=1 or CI is
set. Standard library only; runs on the system python3 (3.9 and up).
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import signal
import socket
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Optional

SCRIPT = Path(__file__).resolve()
ROOT = SCRIPT.parent.parent
RECORD = ROOT / ".reboot" / "placeholder.json"


def disabled() -> bool:
    return os.environ.get("REBOOT_NO_PLACEHOLDER") == "1" or bool(os.environ.get("CI"))


def rbtrc() -> str:
    try:
        return (ROOT / ".rbtrc").read_text()
    except OSError:
        return ""


def is_web_app() -> bool:
    return (ROOT / "web").is_dir() and not (ROOT / "frontend").exists()


def visit_port() -> int:
    if is_web_app():
        try:
            config = (ROOT / "web" / "vite.config.ts").read_text()
        except OSError:
            config = ""
        found = re.search(r"^\s*port:\s*(\d+)", config, re.MULTILINE)
        return int(found.group(1)) if found else 5273
    found = re.search(r"^dev run --port=(\d+)", rbtrc(), re.MULTILINE)
    return int(found.group(1)) if found else 9991


def title() -> str:
    found = re.search(r"^dev run --application-name=(\S+)", rbtrc(), re.MULTILINE)
    return found.group(1) if found else ROOT.name


def port_free(port: int) -> bool:
    # Nothing answers on either stack, where the browser's localhost
    # goes. A connect, not a bind: the closed connections a server
    # leaves in TIME_WAIT for a while do not hold the port.
    for family, host in ((socket.AF_INET, "127.0.0.1"), (socket.AF_INET6, "::1")):
        try:
            sock = socket.socket(family, socket.SOCK_STREAM)
        except OSError:
            continue
        try:
            sock.settimeout(0.5)
            if sock.connect_ex((host, port)) == 0:
                return False
        except OSError:
            pass
        finally:
            sock.close()
    return True


def read_record() -> Optional[dict]:
    try:
        record = json.loads(RECORD.read_text())
        int(record["pid"])
        return record
    except (OSError, ValueError, KeyError, TypeError):
        return None


def write_record(record: dict) -> None:
    RECORD.parent.mkdir(parents=True, exist_ok=True)
    tmp = RECORD.with_name(RECORD.name + ".%d" % os.getpid())
    tmp.write_text(json.dumps(record) + "\n")
    os.replace(str(tmp), str(RECORD))


def remove_record_of(pid: int) -> None:
    record = read_record()
    if record is not None and int(record["pid"]) == pid:
        try:
            RECORD.unlink()
        except OSError:
            pass


def alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def is_placeholder(pid: int) -> bool:
    if pid <= 0 or not alive(pid):
        return False
    try:
        command = subprocess.run(["ps", "-o", "command=", "-p", str(pid)],
                                 capture_output=True, text=True).stdout
    except OSError:
        return False
    return "placeholder.py" in command


def detach(*args: str) -> subprocess.Popen:
    return subprocess.Popen(
        [sys.executable, str(SCRIPT), *args], cwd=str(ROOT), start_new_session=True,
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        close_fds=True)


# The page.

STYLE = """
:root { --bg: #f4f4f7; --panel: #ffffff; --ink: #1b1d26; --muted: #5c6070;
  --line: #dcdde5; --accent: #5b3fd6; --accent-tint: #ebe6fb; color-scheme: light; }
@media (prefers-color-scheme: dark) {
  :root { --bg: #14151c; --panel: #1d1f29; --ink: #ecebf4; --muted: #a0a3b3;
    --line: #2f3140; --accent: #b4a1ff; --accent-tint: #2a2448; color-scheme: dark; }
}
* { box-sizing: border-box; }
body { margin: 0; min-height: 100vh; display: grid; place-items: center; padding: 16px;
  background: var(--bg); color: var(--ink); font: 15px/1.5 ui-sans-serif, system-ui,
  -apple-system, "Segoe UI", sans-serif; }
main { max-width: 520px; width: 100%; background: var(--panel); border: 1px solid var(--line);
  border-radius: 8px; padding: 24px; }
h1 { font-size: 28px; font-weight: 500; letter-spacing: -0.02em; margin: 0 0 8px;
  line-height: 1.2; overflow-wrap: anywhere; }
p { margin: 0 0 12px; }
.muted { color: var(--muted); font-size: 13px; margin: 0; }
code { font: 13px ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  background: var(--accent-tint); color: var(--ink); border-radius: 6px; padding: 1px 6px; }
"""


def page() -> bytes:
    start = "Ask Claude to run it, or run <code>uv run rbt dev run</code>"
    if is_web_app():
        start += " and <code>npm run dev</code> in <code>web/</code>"
    name = html.escape(title())
    return ("""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="3">
<title>%s is not running</title><style>%s</style></head>
<body><main><h1>%s</h1><p>This app is not running.</p><p>%s.</p>
<p class="muted">This page reloads every few seconds and turns into the app once it starts.</p>
</main></body></html>
""" % (name, STYLE, name, start)).encode()


class Handler(BaseHTTPRequestHandler):
    body = b""

    def answer(self) -> None:
        self.send_response(503)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(self.body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Retry-After", "3")
        self.send_header("Connection", "close")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(self.body)
        self.close_connection = True

    def __getattr__(self, name: str):
        # Every method (do_GET, do_POST, do_HEAD, ...) gets the 503.
        if name.startswith("do_"):
            return self.answer
        raise AttributeError(name)

    def log_message(self, format: str, *args: object) -> None:
        pass


def run_server(port: int) -> int:
    Handler.body = page()
    servers = []
    for family, host in ((socket.AF_INET, "127.0.0.1"), (socket.AF_INET6, "::1")):
        server_class = type("Server", (ThreadingHTTPServer,),
                            {"address_family": family, "allow_reuse_address": True,
                             "daemon_threads": True})
        try:
            servers.append(server_class((host, port), Handler))
        except OSError:
            if family == socket.AF_INET:
                return 1
    write_record({"pid": os.getpid(), "port": port})
    for server in servers:
        threading.Thread(target=server.serve_forever, daemon=True).start()
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
    try:
        # A project deleted under it takes the page with it.
        while SCRIPT.exists():
            time.sleep(5)
    finally:
        remove_record_of(os.getpid())
    return 0


def wait_for_record(child: subprocess.Popen) -> None:
    # Back once the detached child has recorded itself, so a `stop`
    # straight after finds it.
    deadline = time.time() + 3
    while time.time() < deadline and child.poll() is None:
        record = read_record()
        if record is not None and int(record["pid"]) == child.pid:
            return
        time.sleep(0.02)


# The subcommands.

def serve(own_pid: int = 0) -> int:
    record = read_record()
    if record is not None and int(record["pid"]) != own_pid and is_placeholder(int(record["pid"])):
        return 0
    port = visit_port()
    if not port_free(port):
        return 0
    wait_for_record(detach("_server", "--port", str(port)))
    return 0


def stop() -> int:
    record = read_record()
    if record is None:
        return 0
    pid = int(record["pid"])
    port = int(record.get("port") or visit_port())
    if is_placeholder(pid):
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            pass
        # A server's port frees as it exits; a watcher holds none.
        server = "watching" not in record
        deadline = time.time() + 5
        while time.time() < deadline and (alive(pid) or (server and not port_free(port))):
            time.sleep(0.05)
        if alive(pid):
            try:
                os.kill(pid, signal.SIGKILL)
            except OSError:
                pass
    try:
        RECORD.unlink()
    except OSError:
        pass
    return 0


def watch(pid: int, seconds: float) -> int:
    write_record({"pid": os.getpid(), "port": visit_port(), "watching": pid})
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
    try:
        while alive(pid):
            time.sleep(1)
        deadline = time.time() + seconds
        while not port_free(visit_port()):
            if time.time() >= deadline:
                return 0
            time.sleep(2)
        record = read_record()
        if record is None or int(record["pid"]) != os.getpid():
            return 0  # stopped, or replaced by a newer watcher
        return serve(own_pid=os.getpid())
    finally:
        remove_record_of(os.getpid())


def status() -> int:
    record = read_record()
    port = visit_port()
    if record is not None and is_placeholder(int(record["pid"])):
        if "watching" in record:
            print("placeholder: waiting for pid %s to exit, then serving on port %s (pid %s)"
                  % (record["watching"], record.get("port", port), record["pid"]))
        else:
            print("placeholder: serving on port %s (pid %s)" % (record.get("port", port), record["pid"]))
    else:
        print("placeholder: not running (port %d)" % port)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("serve")
    sub.add_parser("stop")
    sub.add_parser("status")
    watcher = sub.add_parser("watch")
    watcher.add_argument("--pid", type=int, required=True)
    watcher.add_argument("--for", dest="seconds", type=float, default=600)
    watcher.add_argument("--attached", action="store_true", help=argparse.SUPPRESS)
    server = sub.add_parser("_server")
    server.add_argument("--port", type=int, required=True)
    args = parser.parse_args()
    if disabled():
        return 0
    if args.command == "serve":
        return serve()
    if args.command == "stop":
        return stop()
    if args.command == "status":
        return status()
    if args.command == "_server":
        return run_server(args.port)
    if not args.attached:
        wait_for_record(detach("watch", "--pid", str(args.pid), "--for", str(args.seconds),
                               "--attached"))
        return 0
    return watch(args.pid, args.seconds)


if __name__ == "__main__":
    sys.exit(main())
