"""Tests for `hooks-handlers/quiet.sh`: every Nth tool call of a Reboot
build repeats that the chat hears only reports. It runs after every
tool call of every session, so it must stay silent elsewhere and its
output must parse."""

import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HOOK = os.path.join(ROOT, "hooks-handlers/quiet.sh")


class QuietTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.n = 0

    def calls(self, cwd, times, transcript=""):
        self.n += 1
        out = []
        for _ in range(times):
            payload = json.dumps({"hook_event_name": "PostToolUse", "session_id": f"s{self.n}",
                                  "cwd": cwd, "transcript_path": transcript, "tool_name": "Bash"})
            r = subprocess.run(["sh", HOOK], input=payload, capture_output=True, text=True, timeout=10,
                               env={**os.environ, "TMPDIR": self.tmp.name, "QUIET_EVERY": "3"})
            self.assertEqual((r.returncode, r.stderr), (0, ""))
            out.append(r.stdout)
        return out

    def test_every_third_call_in_a_project(self):
        project = os.path.join(self.tmp.name, "hotel")
        os.makedirs(os.path.join(project, "backend"))
        open(os.path.join(project, ".rbtrc"), "w").close()
        out = self.calls(os.path.join(project, "backend"), 6)
        self.assertEqual([bool(o) for o in out], [False, False, True, False, False, True])
        context = json.loads(out[2])["hookSpecificOutput"]["additionalContext"]
        self.assertIn("reboot-now", context)

    def test_a_build_before_its_rbtrc(self):
        transcript = os.path.join(self.tmp.name, "t.jsonl")
        with open(transcript, "w") as f:
            f.write(json.dumps({"type": "assistant", "message": {"content": [
                {"type": "text", "text": "**Welcome to Reboot.** A Reboot app..."}]}}, separators=(",", ":")) + "\n")
        self.assertTrue(self.calls(self.tmp.name, 3, transcript)[2])
        with open(transcript, "w") as f:
            f.write('{"type":"assistant","message":{"content":[{"type":"text","text":"> **Welcome to Reboot.** A"}]}}\n')
        self.assertTrue(self.calls(self.tmp.name, 3, transcript)[2])

    def test_silent_elsewhere(self):
        transcript = os.path.join(self.tmp.name, "t.jsonl")
        with open(transcript, "w") as f:
            f.write(json.dumps({"type": "user", "message": {"content": "the Welcome to Reboot message"}}) + "\n")
        self.assertEqual(self.calls(self.tmp.name, 6, transcript), [""] * 6)


if __name__ == "__main__":
    quiet = "-q" in sys.argv
    unittest.main(argv=[a for a in sys.argv if a != "-q"], verbosity=0 if quiet else 1)
