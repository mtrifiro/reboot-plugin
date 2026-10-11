"""Tests for the plugin's `orphans.sh` SessionStart hook and the
`lib/own.sh` ownership records it reads.

Every case runs against real processes: `sleep`s renamed with
`exec -a` to look like a Reboot dev process, detached so that their
parent is pid 1, the way a dev process is left when the session that
started it exits. Ownership records go to a temporary directory.

Upstream, this lives in `tests/reboot/plugin/hooks/` beside the other
hook tests, with `ORPHANS_SH` and `OWN_SH` set by Bazel.
"""

import json
import os
import re
import shutil
import subprocess
import tempfile
import time
import unittest
from typing import List, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
HOOK_SCRIPT = os.path.abspath(
    os.environ.get("ORPHANS_SH", os.path.join(ROOT, "hooks-handlers/orphans.sh"))
)
OWN_SCRIPT = os.path.abspath(
    os.environ.get("OWN_SH", os.path.join(ROOT, "lib/own.sh"))
)

SENTINEL = "[reboot-plugin-orphans]"


def lstart(pid: int) -> str:
    return subprocess.run(
        ["ps", "-o", "lstart=", "-p", str(pid)],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.rstrip("\n")


def alive(pid: int) -> bool:
    return subprocess.run(
        ["ps", "-p", str(pid)], capture_output=True
    ).returncode == 0


class OrphansTest(unittest.TestCase):

    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp()
        # A Reboot project, and a directory that is not one.
        self.project = os.path.join(self.tmp, "app")
        os.makedirs(os.path.join(self.project, "backend/src"))
        open(os.path.join(self.project, ".rbtrc"), "w").close()
        self.elsewhere = os.path.join(self.tmp, "other")
        os.makedirs(os.path.join(self.elsewhere, "backend/src"))
        self.owners = os.path.join(self.tmp, "owners")
        os.makedirs(self.owners)
        self.pids: List[int] = []

    def tearDown(self) -> None:
        for pid in self.pids:
            subprocess.run(["kill", "-9", str(pid)], capture_output=True)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def detached(
        self, script: str, cwd: Optional[str] = None, child: bool = False
    ) -> List[int]:
        """Run `script` (bash) in the background of a subshell that
        exits at once, so it is reparented to pid 1. The script writes
        the pid it wants tracked to `$PIDS` and, with `child`, its
        child's to `$PIDS.child`. Returns them, parent first."""
        out = os.path.join(self.tmp, f"pids.{len(self.pids)}.{time.time()}")
        subprocess.run(
            ["bash", "-c", f"( {script} ) >/dev/null 2>&1 &"],
            cwd=cwd or self.project,
            env={**os.environ, "PIDS": out},
            check=True,
        )
        files = [out, out + ".child"] if child else [out]
        for _ in range(100):
            pids = []
            for path in files:
                if os.path.exists(path):
                    with open(path) as f:
                        pids += [int(word) for word in f.read().split()]
            if len(pids) == len(files):
                break
            time.sleep(0.05)
        else:
            raise AssertionError("detached process never started")
        self.pids.extend(pids)
        # Wait for the reparent to pid 1, and for `exec -a` to land.
        time.sleep(0.3)
        return pids

    def app(self, cwd: Optional[str] = None) -> int:
        """A detached process that looks like an app's `main.py`."""
        where = cwd or self.project
        (pid,) = self.detached(
            f'exec -a "python {where}/backend/src/main.py" sleep 600 & echo $! >"$PIDS"',
            cwd=where,
        )
        return pid

    def record(self, pid: int, owner: int, owner_started: str, session: str) -> str:
        path = os.path.join(self.owners, str(pid))
        with open(path, "w") as f:
            f.write(
                f"pid={pid}\nstarted={lstart(pid)}\nowner={owner}\n"
                f"owner_started={owner_started}\nsession={session}\n"
                f"kind=app\ncwd={self.project}\n"
            )
        return path

    def run_hook(self, min_age: int) -> Optional[str]:
        result = subprocess.run(
            ["sh", HOOK_SCRIPT],
            input="{}",
            capture_output=True,
            text=True,
            timeout=30,
            env={
                **os.environ,
                "REBOOT_ORPHAN_MIN_AGE": str(min_age),
                "REBOOT_OWNERS_DIR": self.owners,
            },
        )
        if result.returncode != 0:
            raise AssertionError(f"hook exited {result.returncode}: {result.stderr}")
        if not result.stdout.strip():
            return None
        context = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
        self.assertTrue(context.startswith(SENTINEL))
        return context

    def line_for(self, context: Optional[str], pid: int) -> Optional[str]:
        """The report line whose pid list holds `pid`, if any."""
        for line in (context or "").splitlines():
            listed = re.search(r"pids ([0-9 ]+),", line)
            if listed and str(pid) in listed.group(1).split():
                return line
        return None

    def test_old_orphan_without_a_record_is_reported(self) -> None:
        pid = self.app()
        line = self.line_for(self.run_hook(min_age=0), pid)
        self.assertIsNotNone(line)
        assert line is not None
        self.assertIn(self.project, line)
        self.assertIn("(app)", line)
        self.assertIn("no record of its session", line)

    def test_dashboards_pyright_child_is_reported(self) -> None:
        (pid,) = self.detached(
            'exec -a "node /x/node_modules/pyright/dist/langserver.index.js" sleep 600 & '
            'echo $! >"$PIDS"'
        )
        line = self.line_for(self.run_hook(min_age=0), pid)
        self.assertIsNotNone(line)
        assert line is not None
        self.assertIn("(dashboard pyright)", line)

    def test_young_orphan_without_a_record_is_left_alone(self) -> None:
        pid = self.app()
        self.assertIsNone(self.line_for(self.run_hook(min_age=3600), pid))

    def test_main_py_outside_a_reboot_project_is_ignored(self) -> None:
        pid = self.app(cwd=self.elsewhere)
        self.assertIsNone(self.line_for(self.run_hook(min_age=0), pid))

    def test_record_whose_owner_exited_is_reported_at_once(self) -> None:
        (owner,) = self.detached('sleep 600 & echo $! >"$PIDS"')
        owner_started = lstart(owner)
        pid = self.app()
        self.record(pid, owner, owner_started, "dead-session-id")
        subprocess.run(["kill", "-9", str(owner)], check=True)
        time.sleep(0.2)
        line = self.line_for(self.run_hook(min_age=3600), pid)
        self.assertIsNotNone(line)
        self.assertIn("session dead-session-id has exited", line or "")

    def test_record_whose_owner_lives_is_left_alone(self) -> None:
        # A detached process (`nohup`, `&`) of a live session: its
        # parent is pid 1, but its owner still runs.
        (owner,) = self.detached('sleep 600 & echo $! >"$PIDS"')
        pid = self.app()
        self.record(pid, owner, lstart(owner), "live-session-id")
        self.assertIsNone(self.line_for(self.run_hook(min_age=0), pid))

    def test_owner_pid_reused_by_another_process_counts_as_exited(self) -> None:
        (owner,) = self.detached('sleep 600 & echo $! >"$PIDS"')
        pid = self.app()
        self.record(pid, owner, "Thu Jan  1 00:00:00 1970", "old-session-id")
        line = self.line_for(self.run_hook(min_age=3600), pid)
        self.assertIn("session old-session-id has exited", line or "")

    def test_stale_record_is_deleted(self) -> None:
        (pid,) = self.detached('sleep 600 & echo $! >"$PIDS"')
        path = self.record(pid, os.getpid(), lstart(os.getpid()), "s")
        subprocess.run(["kill", "-9", str(pid)], check=True)
        time.sleep(0.2)
        self.run_hook(min_age=3600)
        self.assertFalse(os.path.exists(path))

    def test_whole_group_is_reported_top_first(self) -> None:
        # A shell left by the agent's Bash tool, running the app.
        script = (
            f'bash -c \'exec -a "python {self.project}/backend/src/main.py" sleep 600 & '
            f'echo $! >"$PIDS.child"; wait\' & echo $! >"$PIDS"'
        )
        shell, child = self.detached(script, child=True)
        line = self.line_for(self.run_hook(min_age=0), shell)
        self.assertIsNotNone(line)
        self.assertIn(f"pids {shell} {child},", line or "")
        # Reported once, as part of its group, not again on its own.
        context = self.run_hook(min_age=0) or ""
        self.assertEqual(context.count(f" {child}"), 1)

    def test_process_under_a_live_non_launcher_is_left_alone(self) -> None:
        # A tmux server (or a terminal's login shell) still holds it.
        script = (
            f'exec -a tmux bash -c \'exec -a "python {self.project}/backend/src/main.py" '
            f'sleep 600 & echo $! >"$PIDS.child"; wait\' & echo $! >"$PIDS"'
        )
        tmux, child = self.detached(script, child=True)
        self.assertIsNone(self.line_for(self.run_hook(min_age=0), child))
        self.assertIsNone(self.line_for(self.run_hook(min_age=0), tmux))

    def test_silent_with_nothing_to_report(self) -> None:
        result = subprocess.run(
            ["sh", HOOK_SCRIPT],
            input="{}",
            capture_output=True,
            text=True,
            env={**os.environ, "REBOOT_ORPHAN_MIN_AGE": "99999999", "REBOOT_OWNERS_DIR": self.owners},
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")


class OwnTest(unittest.TestCase):

    def setUp(self) -> None:
        self.owners = tempfile.mkdtemp()
        self.proc = subprocess.Popen(["sleep", "600"])

    def tearDown(self) -> None:
        self.proc.kill()
        self.proc.wait()
        shutil.rmtree(self.owners, ignore_errors=True)

    def own(self, *args: str, claude_pid: Optional[int] = None) -> Optional[dict]:
        env = {**os.environ, "REBOOT_OWNERS_DIR": self.owners}
        env.pop("CLAUDE_PID", None)
        env["CLAUDE_CODE_SESSION_ID"] = "the-session"
        if claude_pid is not None:
            env["CLAUDE_PID"] = str(claude_pid)
        result = subprocess.run(
            ["sh", OWN_SCRIPT, str(self.proc.pid), *args],
            env=env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")
        path = os.path.join(self.owners, str(self.proc.pid))
        if not os.path.exists(path):
            return None
        with open(path) as f:
            return dict(line.split("=", 1) for line in f.read().splitlines())

    def test_records_long_running_commands(self) -> None:
        me = os.getpid()
        for args, kind in [
            (("uv", "run", "rbt", "dev", "run", "--no-chaos"), "app"),
            (("uv", "run", "--project", "x", "rbt", "dashboard"), "dashboard"),
            (("uv", "run", "rbt", "dashboard", "--port=9872"), "dashboard"),
            (("rbt", "dev", "run"), "app"),
            (("npm", "run", "dev"), "frontend"),
            (("cloudflared", "tunnel", "--url", "http://localhost:9991"), "tunnel"),
            (("mcpjam-inspector", "--url", "http://localhost:9991/mcp"), "MCPJam"),
        ]:
            with self.subTest(args=args):
                record = self.own(*args, claude_pid=me)
                self.assertIsNotNone(record)
                assert record is not None
                self.assertEqual(record["kind"], kind)
                self.assertEqual(record["pid"], str(self.proc.pid))
                self.assertEqual(record["started"], lstart(self.proc.pid))
                self.assertEqual(record["owner"], str(me))
                self.assertEqual(record["owner_started"], lstart(me))
                self.assertEqual(record["session"], "the-session")
                os.remove(os.path.join(self.owners, str(self.proc.pid)))

    def test_ignores_short_commands(self) -> None:
        for args in [
            ("uv", "sync"),
            ("uv", "run", "rbt", "generate"),
            ("uv", "run", "pytest"),
            ("rbt", "dev", "expunge", "--yes"),
            ("npm", "install"),
            ("npm", "run", "build"),
            ("cloudflared", "--version"),
        ]:
            with self.subTest(args=args):
                self.assertIsNone(self.own(*args, claude_pid=os.getpid()))

    def test_records_nothing_outside_claude_code(self) -> None:
        self.assertIsNone(self.own("uv", "run", "rbt", "dev", "run"))


if __name__ == "__main__":
    unittest.main()
