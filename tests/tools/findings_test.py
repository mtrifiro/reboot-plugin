#!/usr/bin/env python3
"""Tests for `tools/findings.py`'s `resolved_by` and `mechanism` checks,
against a temporary repo: a heading inside a code fence does not count;
a skills/ path needs a section, a template or mechanism path does not;
a mechanism section names a .md heading, a Python def or class, a shell
function, or an eval case's grader; a missing file or section fails; the
`mechanism` field takes only its enum; the real corpus has no errors.

    python3 tests/tools/findings_test.py
"""

import importlib.util
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
spec = importlib.util.spec_from_file_location("findings", ROOT / "tools" / "findings.py")
findings = importlib.util.module_from_spec(spec)
spec.loader.exec_module(findings)

FILES = {
    "skills/python/references/rpc-refs.md":
        "# Refs\n\n## Calling\n\n```markdown\n## Fenced heading\n```\n\n~~~\n# Also fenced\n~~~\n",
    "skills/build/templates/README.md": "# Templates\n\n## Copy\n",
    "skills/build/templates/web-app/scripts/test.sh": "#!/bin/sh\n",
    "tools/budget.py": "def measure():\n    pass\n\nclass Report:\n    pass\n",
    "hooks/auto-approve.sh": "#!/usr/bin/env bash\nflag_ok() {\n  :\n}\nfunction args_ok {\n  :\n}\n",
    "bin/rbt": "#!/usr/bin/env bash\nrefuse() {\n  :\n}\n",
    "lib/notes.md": "# Notes\n\n## Patches\n",
    "evals/workflow-recorded/graders/follows-the-record.md": "PASS if ...\n",
}


def item(resolved_by: str, **extra) -> dict:
    base = {"id": "x-01", "project": "x", "source": "s", "reboot_version": "1.6.0",
            "severity": "red", "target": "plugin", "names": [], "tags": [],
            "cluster": "A", "still_applies": "yes", "status": "Resolved",
            "resolved_by": resolved_by}
    base.update(extra)
    return base


class ResolvedByTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        for rel, text in FILES.items():
            path = self.tmp / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        self.saved = findings.ROOT, findings.SKILLS
        findings.ROOT, findings.SKILLS = self.tmp, self.tmp / "skills"

    def tearDown(self) -> None:
        findings.ROOT, findings.SKILLS = self.saved
        shutil.rmtree(self.tmp, ignore_errors=True)

    def ok(self, ref: str) -> None:
        self.assertEqual(findings.validate(item(ref)), [], ref)

    def fails(self, ref: str, words: str) -> None:
        errors = findings.validate(item(ref))
        self.assertEqual(len(errors), 1, (ref, errors))
        self.assertIn(words, errors[0])

    def test_skills_heading(self) -> None:
        self.ok("python/references/rpc-refs.md § Calling")
        self.ok("python/references/rpc-refs.md § calling")

    def test_heading_inside_a_fence_does_not_count(self) -> None:
        self.fails("python/references/rpc-refs.md § Fenced heading", "missing section")
        self.fails("python/references/rpc-refs.md § Also fenced", "missing section")

    def test_skills_prose_needs_a_section(self) -> None:
        self.fails("python/references/rpc-refs.md", "names no section")

    def test_templates_need_no_section(self) -> None:
        self.ok("build/templates/web-app/scripts/test.sh")
        self.ok("build/templates/README.md § Copy")

    def test_mechanism_paths(self) -> None:
        self.ok("tools/budget.py")
        self.ok("tools/budget.py § measure")
        self.ok("tools/budget.py § Report")
        self.ok("hooks/auto-approve.sh § flag_ok")
        self.ok("hooks/auto-approve.sh § args_ok")
        self.ok("bin/rbt § refuse")
        self.ok("lib/notes.md § Patches")
        self.ok("evals/workflow-recorded")
        self.ok("evals/workflow-recorded § follows-the-record")

    def test_missing_mechanism_section(self) -> None:
        self.fails("tools/budget.py § words", "missing section")
        self.fails("hooks/auto-approve.sh § is_in_plugin", "missing section")
        self.fails("evals/workflow-recorded § asks-again", "missing section")

    def test_missing_file(self) -> None:
        self.fails("tools/nothing.py", "missing file")
        self.fails("python/references/nothing.md § Calling", "missing file")
        self.fails("evals/no-such-case", "missing file")
        self.fails("tools", "missing file")

    def test_several_entries(self) -> None:
        self.ok("python/references/rpc-refs.md § Calling; tools/budget.py § measure")
        self.fails("python/references/rpc-refs.md § Calling; tools/x.py", "missing file")

    def test_mechanism_enum(self) -> None:
        for m in ("row", "template", "check", "hook", "shim", "tool", "prose", "eval", ""):
            self.assertEqual(findings.validate(item("tools/budget.py", mechanism=m)), [], m)
        errors = findings.validate(item("tools/budget.py", mechanism="docs"))
        self.assertEqual(len(errors), 1)
        self.assertIn("mechanism='docs'", errors[0])


class CorpusTest(unittest.TestCase):
    def test_corpus_is_clean(self) -> None:
        result = subprocess.run([sys.executable, str(ROOT / "tools" / "findings.py"), "--check"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
