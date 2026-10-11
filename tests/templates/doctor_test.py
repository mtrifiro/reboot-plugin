#!/usr/bin/env python3
"""Tests for the templates' scripts/doctor.sh: silent and green on a
quiet project; names the allowlist variables in the shell and a test
run in progress.

    python3 tests/templates/doctor_test.py
"""

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DOCTOR = ROOT / "skills" / "build" / "templates" / "web-app" / "scripts" / "doctor.sh"


class DoctorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp()
        self.project = Path(self.tmp)
        (self.project / "scripts").mkdir()
        (self.project / "tests").mkdir()
        shutil.copy(DOCTOR, self.project / "scripts" / "doctor.sh")
        (self.project / ".rbtrc").write_text(
            "generate api/\ndev run --application-name=quiet-app\ndev run --port=9999\n")

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_doctor(self, **env: str) -> subprocess.CompletedProcess:
        clean = {k: v for k, v in os.environ.items() if k not in ("ALLOWED_EMAILS", "ALLOWED_EMAIL_DOMAINS")}
        return subprocess.run(["sh", "scripts/doctor.sh"], cwd=self.project,
                              env={**clean, **env}, capture_output=True, text=True)

    def test_nothing_found_on_a_quiet_project(self) -> None:
        r = self.run_doctor()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("nothing found", r.stdout)

    def test_names_the_allowlist_variables(self) -> None:
        r = self.run_doctor(ALLOWED_EMAILS="a@example.com")
        self.assertEqual(r.returncode, 1)
        self.assertIn("ALLOWED_EMAILS is set", r.stdout)
        self.assertIn("env -u ALLOWED_EMAILS", r.stdout)

    def test_names_a_test_run_in_progress(self) -> None:
        (self.project / "tests" / ".suite-running").write_text(json.dumps({"pid": os.getpid()}))
        r = self.run_doctor()
        self.assertEqual(r.returncode, 1)
        self.assertIn(f"a test run is in progress (pid {os.getpid()})", r.stdout)

    def test_ignores_a_dead_test_run(self) -> None:
        (self.project / "tests" / ".suite-running").write_text(json.dumps({"pid": 2 ** 22 - 1}))
        r = self.run_doctor()
        self.assertNotIn("in progress", r.stdout)


if __name__ == "__main__":
    unittest.main()
