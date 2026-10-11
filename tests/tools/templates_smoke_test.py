"""Tests for tools/templates-smoke.sh's leftover handling: a run cut off
before its scenario servers stop leaves them running from a deleted
folder, and the next run (or --reap) stops them."""

import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SMOKE = os.path.join(ROOT, "tools/templates-smoke.sh")


def fake_server(folder):
    """A process whose command line names `folder`, like a scenario's backend."""
    argv0 = os.path.join(folder, "web-app/.venv/bin/python")
    return subprocess.Popen(["bash", "-c", f'exec -a "{argv0}" sleep 60'], start_new_session=True)


def gone(proc, deadline=10.0):
    end = time.time() + deadline
    while time.time() < end:
        if proc.poll() is not None:
            return True
        time.sleep(0.1)
    return False


class TemplatesSmokeTest(unittest.TestCase):
    def setUp(self):
        self.base = tempfile.mkdtemp()
        self.procs = []

    def tearDown(self):
        for p in self.procs:
            if p.poll() is None:
                p.kill()
                p.wait()
        shutil.rmtree(self.base, ignore_errors=True)

    def start(self, folder):
        p = fake_server(folder)
        self.procs.append(p)
        time.sleep(0.3)  # let exec -a take effect
        return p

    def test_reap_stops_a_leftover_whose_folder_is_gone(self):
        dead = os.path.join(self.base, "templates-smoke.DEAD01")
        os.makedirs(dead)
        leftover = self.start(dead)
        shutil.rmtree(dead)
        out = subprocess.run(["bash", SMOKE, "--reap"], capture_output=True, text=True, timeout=30)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertTrue(gone(leftover), "the leftover server is still running")
        self.assertIn("stopping leftovers", out.stdout)

    def test_reap_leaves_a_live_run_alone(self):
        live = os.path.join(self.base, "templates-smoke.LIVE01")
        os.makedirs(live)
        running = self.start(live)
        subprocess.run(["bash", SMOKE, "--reap"], capture_output=True, text=True, timeout=30)
        self.assertIsNone(running.poll(), "a run whose folder exists was stopped")

    def test_a_process_that_only_mentions_a_folder_is_left_alone(self):
        dead = os.path.join(self.base, "templates-smoke.MENT01")
        mention = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)", f"{dead}/web-app/.venv/bin/python"],
                                   start_new_session=True)
        self.procs.append(mention)
        time.sleep(0.3)
        subprocess.run(["bash", SMOKE, "--reap"], capture_output=True, text=True, timeout=30)
        self.assertIsNone(mention.poll(), "a process that only names the path in its arguments was stopped")


if __name__ == "__main__":
    quiet = "-q" in sys.argv
    unittest.main(argv=[a for a in sys.argv if a != "-q"], verbosity=0 if quiet else 1)
