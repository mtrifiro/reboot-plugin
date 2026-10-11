#!/usr/bin/env python3
"""Tests for the templates' scripts/deploy.sh flags: `--first` with
`--frontend-only` is refused before anything runs, in each template.

    python3 tests/templates/deploy_test.py
"""

import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
TEMPLATES = ROOT / "skills" / "build" / "templates"


class DeployFlagsTest(unittest.TestCase):
    def test_first_does_not_combine_with_frontend_only(self) -> None:
        for template in ("mcp-ui", "web-app", "both"):
            for args in (["--first", "--frontend-only"], ["--frontend-only", "--first"]):
                with self.subTest(template=template, args=args):
                    r = subprocess.run(["bash", str(TEMPLATES / template / "scripts" / "deploy.sh"), *args],
                                       capture_output=True, text=True, timeout=30)
                    self.assertEqual(r.returncode, 2)
                    self.assertIn("does not combine with --frontend-only", r.stderr)
                    self.assertEqual(r.stdout, "")


if __name__ == "__main__":
    unittest.main()
