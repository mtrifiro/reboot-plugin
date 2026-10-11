#!/usr/bin/env python3
"""Tests for `tools/lint-frontmatter.py`'s skips and exemptions: .git
and .gstack are skipped at the root only; build output (node_modules,
dist, .venv, the caches) only inside a template or a mod; README files
are exempt only at the listed paths; the real tree passes.

    python3 tests/tools/lint_frontmatter_test.py
"""

import fnmatch
import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))
spec = importlib.util.spec_from_file_location("lint_frontmatter", TOOLS / "lint-frontmatter.py")
lint = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lint)


def skipped(rel: str) -> bool:
    return lint.skipped(tuple(rel.split("/")))


def exempt(rel: str) -> bool:
    return any(fnmatch.fnmatchcase(rel, pat) for pat in lint.EXEMPT)


class SkipTest(unittest.TestCase):
    def test_root_only_dirs(self) -> None:
        self.assertTrue(skipped(".git/x.md"))
        self.assertTrue(skipped(".gstack/notes.md"))
        self.assertFalse(skipped("skills/.gstack/notes.md"))

    def test_build_output_in_templates_and_mods(self) -> None:
        self.assertTrue(skipped("skills/build/templates/web-app/.pytest_cache/README.md"))
        self.assertTrue(skipped("skills/build/templates/both/web/node_modules/a/README.md"))
        self.assertTrue(skipped("skills/build/templates/mcp-ui/.venv/lib/x.md"))
        self.assertTrue(skipped("mods/reboot-progress/node_modules/a/README.md"))
        self.assertTrue(skipped("mods/reboot-progress/dist/x.md"))

    def test_build_output_elsewhere_is_checked(self) -> None:
        self.assertFalse(skipped("node_modules/a/README.md"))
        self.assertFalse(skipped("skills/python/references/dist/x.md"))
        self.assertFalse(skipped("tools/__pycache__/x.md"))
        self.assertFalse(skipped("skills/build/templates/node_modules/x.md"))

    def test_source_files_are_not_skipped(self) -> None:
        self.assertFalse(skipped("skills/build/templates/web-app/AGENTS.md"))
        self.assertFalse(skipped("mods/reboot-progress/README.md"))


class ExemptTest(unittest.TestCase):
    def test_listed_readmes(self) -> None:
        for rel in ("README.md", "evals/README.md", "findings/README.md", "mods/README.md",
                    "tools/README.md", "skills/build/templates/README.md",
                    "skills/upgrade/migrations/README.md",
                    "skills/upgrade/migrations/next/README.md"):
            self.assertTrue(exempt(rel), rel)

    def test_other_readmes_are_checked(self) -> None:
        for rel in ("skills/python/README.md", "evals/route-mcp/README.md",
                    "mods/reboot-progress/README.md", "docs/README.md"):
            self.assertFalse(exempt(rel), rel)


class TreeTest(unittest.TestCase):
    def test_tree_passes(self) -> None:
        result = subprocess.run([sys.executable, str(TOOLS / "lint-frontmatter.py")],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout)


if __name__ == "__main__":
    unittest.main()
