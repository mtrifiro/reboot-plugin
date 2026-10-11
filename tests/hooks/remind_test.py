"""Tests for `hooks-handlers/remind.sh`: its output is the JSON Claude
Code reads, so it must parse for every event it answers. The reminder
quotes wrong and right sentences, and an unescaped quote once made the
whole output unreadable, so the guidance never reached a session."""

import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HOOK = os.path.join(ROOT, "hooks-handlers/remind.sh")


def run(event, cwd, prompt="add a feature"):
    payload = json.dumps({"hook_event_name": event, "prompt": prompt, "cwd": cwd})
    out = subprocess.run(["sh", HOOK], input=payload, capture_output=True, text=True, cwd=cwd, timeout=30)
    return out.stdout


class RemindTest(unittest.TestCase):
    def test_output_parses_in_a_project(self):
        with tempfile.TemporaryDirectory() as project:
            open(os.path.join(project, ".rbtrc"), "w").close()
            for event in ("SessionStart", "UserPromptSubmit"):
                with self.subTest(event=event):
                    text = run(event, project)
                    self.assertTrue(text.strip(), "no output in a Reboot project")
                    context = json.dumps(json.loads(text))
                    self.assertIn("first person", context)
                    self.assertIn('Not \\"I', context)

    def test_a_prompt_naming_reboot_gets_it_outside_a_project(self):
        with tempfile.TemporaryDirectory() as empty:
            json.loads(run("UserPromptSubmit", empty, prompt="Build a reboot app for a hotel"))

    def test_silent_elsewhere(self):
        with tempfile.TemporaryDirectory() as empty:
            self.assertEqual(run("UserPromptSubmit", empty, prompt="fix the build").strip(), "")


if __name__ == "__main__":
    quiet = "-q" in sys.argv
    unittest.main(argv=[a for a in sys.argv if a != "-q"], verbosity=0 if quiet else 1)
