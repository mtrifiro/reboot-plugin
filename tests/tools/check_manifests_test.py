#!/usr/bin/env python3
"""Tests for `tools/check-manifests.py`'s marketplace entry checks,
against a temporary repo: a local entry must match its plugin.json's
name and version, and an entry with no version fails; the root plugin
carries no version in its entry or its plugin.json; the Codex
marketplace shares the Claude one's name, each local path holds a
.codex-plugin/plugin.json with the entry's name, and every plugin it
lists is in the Claude marketplace; the real repo passes.

    python3 tests/tools/check_manifests_test.py
"""

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
spec = importlib.util.spec_from_file_location("check_manifests",
                                              ROOT / "tools" / "check-manifests.py")
cm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cm)


class ManifestsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.write(".claude-plugin/plugin.json", {"name": "reboot"})
        self.write(".codex-plugin/plugin.json", {"name": "reboot", "version": "1.6.0"})
        self.write("mods/band/.claude-plugin/plugin.json", {"name": "band", "version": "0.3.4"})
        (self.tmp / "plugins").mkdir()
        (self.tmp / "plugins" / "reboot").symlink_to("..")
        self.saved = cm.ROOT
        cm.ROOT = self.tmp

    def tearDown(self) -> None:
        cm.ROOT = self.saved
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write(self, rel: str, doc: dict) -> None:
        path = self.tmp / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(doc))

    @staticmethod
    def market(*extra: dict, band: dict | None = None) -> dict:
        entry = {"name": "band", "source": "./mods/band", "version": "0.3.4"}
        entry.update(band or {})
        return {"name": "mp", "plugins": [{"name": "reboot", "source": "./"}, entry, *extra]}

    @staticmethod
    def codex(**entry) -> dict:
        base = {"name": "reboot", "source": {"source": "local", "path": "./plugins/reboot"}}
        base.update(entry)
        return {"name": "mp", "plugins": [base]}

    def test_good_marketplace_passes(self) -> None:
        self.assertEqual(cm.claude_entry_problems(self.market()), [])
        self.assertEqual(cm.codex_marketplace_problems(self.codex(), self.market()), [])

    def test_entry_without_version_fails(self) -> None:
        market = self.market()
        del market["plugins"][1]["version"]
        problems = cm.claude_entry_problems(market)
        self.assertEqual(len(problems), 1)
        self.assertIn("band has no version", problems[0])

    def test_version_mismatch_fails(self) -> None:
        problems = cm.claude_entry_problems(self.market(band={"version": "0.3.3"}))
        self.assertEqual(len(problems), 1)
        self.assertIn("band is 0.3.3", problems[0])

    def test_name_mismatch_fails(self) -> None:
        self.write("mods/band/.claude-plugin/plugin.json", {"name": "other", "version": "0.3.4"})
        problems = cm.claude_entry_problems(self.market())
        self.assertEqual(len(problems), 1)
        self.assertIn("names 'other'", problems[0])

    def test_missing_plugin_json_fails(self) -> None:
        problems = cm.claude_entry_problems(self.market(band={"source": "./mods/gone"}))
        self.assertEqual(len(problems), 1)
        self.assertIn("has no mods/gone/.claude-plugin/plugin.json", problems[0])

    def test_root_plugin_must_have_no_version(self) -> None:
        market = self.market()
        market["plugins"][0]["version"] = "1.6.0"
        self.write(".claude-plugin/plugin.json", {"name": "reboot", "version": "1.6.0"})
        problems = cm.claude_entry_problems(market)
        self.assertEqual(len(problems), 2)
        self.assertTrue(all("has a version" in p for p in problems))

    def test_remote_entries_are_skipped(self) -> None:
        remote = {"name": "x", "source": {"source": "github", "repo": "a/b"}}
        self.assertEqual(cm.claude_entry_problems(self.market(remote)), [])

    def test_codex_name_and_listing(self) -> None:
        codex = self.codex(name="other")
        codex["name"] = "elsewhere"
        problems = cm.codex_marketplace_problems(codex, self.market())
        self.assertEqual(len(problems), 3, problems)
        self.assertIn("name 'elsewhere'", problems[0])
        self.assertIn("other is not in .claude-plugin/marketplace.json", problems[1])
        self.assertIn("names 'reboot'", problems[2])

    def test_codex_path_without_manifest(self) -> None:
        codex = self.codex(source={"source": "local", "path": "./mods/band"})
        problems = cm.codex_marketplace_problems(codex, self.market())
        self.assertEqual(len(problems), 1)
        self.assertIn("has no mods/band/.codex-plugin/plugin.json", problems[0])

    def test_repo_passes(self) -> None:
        result = subprocess.run([sys.executable, str(ROOT / "tools" / "check-manifests.py")],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
