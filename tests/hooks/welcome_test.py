"""Tests for `hooks-handlers/welcome.sh`: when the app skill loads, the
next output is named as the welcome; a turn that ends on the welcome
goes on; tool calls are never refused. It runs after the app skill and at every Stop, so it must
stay silent elsewhere and its output must parse."""

import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HOOK = os.path.join(ROOT, "hooks-handlers/welcome.sh")

LAUNCHED = {"type": "user", "message": {"content": [{"type": "tool_result", "content": "Launching skill: reboot:app"}]}}
TYPED = {"type": "user", "message": {"content": "<command-message>reboot:app</command-message>\n<command-name>/reboot:app</command-name>"}}
THOUGHT = {"type": "assistant", "message": {"content": [{"type": "thinking", "thinking": "**Welcome to Reboot.** A"}]}}
WELCOME = {"type": "assistant", "message": {"content": [{"type": "text", "text": "**Welcome to Reboot.** A Reboot app"}]}}
TOOL = {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Skill", "input": {}}]}}


class WelcomeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.n = 0

    def run_hook(self, event, *lines, cwd=None, **extra):
        self.n += 1
        transcript = os.path.join(self.tmp.name, f"t{self.n}.jsonl")
        with open(transcript, "w") as f:
            f.writelines(json.dumps(l, separators=(",", ":")) + "\n" for l in lines)
        payload = json.dumps({"hook_event_name": event, "session_id": f"s{self.n}", "cwd": cwd or self.tmp.name,
                              "transcript_path": transcript, "tool_name": "Bash", **extra})
        r = subprocess.run(["sh", HOOK], input=payload, capture_output=True, text=True, timeout=10,
                           env={**os.environ, "TMPDIR": self.tmp.name})
        self.assertEqual((r.returncode, r.stderr), (0, ""))
        return json.loads(r.stdout) if r.stdout else None

    def test_tool_calls_are_never_refused(self):
        # A tool hook can't see its own response's text, so it never gates.
        for launch in (LAUNCHED, TYPED):
            self.assertIsNone(self.run_hook("PreToolUse", launch, THOUGHT))
            self.assertIsNone(self.run_hook("PreToolUse", launch, WELCOME))

    def test_a_turn_that_ends_on_the_welcome_goes_on(self):
        self.assertEqual(self.run_hook("Stop", LAUNCHED, WELCOME)["decision"], "block")
        self.assertIsNone(self.run_hook("Stop", LAUNCHED, WELCOME, stop_hook_active=True))
        self.assertIsNone(self.run_hook("Stop", LAUNCHED, WELCOME, TOOL))

    def test_the_app_skill_loading_names_the_next_output(self):
        out = self.run_hook("PostToolUse", tool_name="Skill", tool_input={"skill": "reboot:app"})
        self.assertIn("next output is the app skill", out["hookSpecificOutput"]["additionalContext"])
        self.assertIsNone(self.run_hook("PostToolUse", tool_name="Skill", tool_input={"skill": "reboot:build"}))

    def test_silent_elsewhere(self):
        self.assertIsNone(self.run_hook("Stop", WELCOME))
        project = os.path.join(self.tmp.name, "hotel")
        os.makedirs(project)
        open(os.path.join(project, ".rbtrc"), "w").close()
        self.assertIsNone(self.run_hook("Stop", LAUNCHED, WELCOME, cwd=project))
        plugin = os.path.join(self.tmp.name, "plugin")
        os.makedirs(os.path.join(plugin, "skills/app"))
        os.makedirs(os.path.join(plugin, "hooks-handlers"))
        open(os.path.join(plugin, "skills/app/SKILL.md"), "w").close()
        self.assertIsNone(self.run_hook("Stop", LAUNCHED, WELCOME, cwd=plugin))
        self.assertIsNone(self.run_hook("PostToolUse", cwd=project, tool_name="Skill", tool_input={"skill": "reboot:app"}))


if __name__ == "__main__":
    quiet = "-q" in sys.argv
    unittest.main(argv=[a for a in sys.argv if a != "-q"], verbosity=0 if quiet else 1)
