"""Tests for `hooks-handlers/reports.sh`: a build report saved under
`design/reports/` that the chat has not shown is sent now. It runs after
every Write and Bash call, so it must stay silent otherwise and its
output must parse."""

import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HOOK = os.path.join(ROOT, "hooks-handlers/reports.sh")
TITLE = "Reboot Design · The Brief"


def line(kind, *blocks):
    return json.dumps({"type": kind, "message": {"content": list(blocks)}}, ensure_ascii=False, separators=(",", ":"))


class ReportsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        os.makedirs(os.path.join(self.tmp.name, "design/reports"))
        with open(os.path.join(self.tmp.name, "design/reports/1-brief.md"), "w") as f:
            f.write(f"# {TITLE}\n\nThis brief restates...\n")

    def run_hook(self, tool_input, *lines, tool="Bash"):
        transcript = os.path.join(self.tmp.name, "t.jsonl")
        with open(transcript, "w") as f:
            f.writelines(l + "\n" for l in lines)
        payload = json.dumps({"hook_event_name": "PostToolUse", "session_id": "s", "cwd": self.tmp.name,
                              "transcript_path": transcript, "tool_name": tool, "tool_input": tool_input},
                             ensure_ascii=False)
        r = subprocess.run(["sh", HOOK], input=payload, capture_output=True, text=True, timeout=10)
        self.assertEqual((r.returncode, r.stderr), (0, ""))
        return json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"] if r.stdout else None

    def test_a_saved_report_the_chat_has_not_shown(self):
        skill = line("user", {"type": "text", "text": f"> # {TITLE}"})
        context = self.run_hook({"command": "cat > design/reports/1-brief.md <<'EOF'"}, skill)
        self.assertIn("`design/reports/1-brief.md` is saved", context)
        path = os.path.join(self.tmp.name, "design/reports/1-brief.md")
        self.assertIsNotNone(self.run_hook({"file_path": path, "content": "x"}, skill, tool="Write"))

    def test_silent_once_shown_and_elsewhere(self):
        shown = line("assistant", {"type": "text", "text": f"---\n# {TITLE}\nThis brief"})
        self.assertIsNone(self.run_hook({"command": "cat > design/reports/1-brief.md"}, shown))
        self.assertIsNone(self.run_hook({"command": "ls design"}))
        self.assertIsNone(self.run_hook({"command": "cat > design/reports/9-none.md"}))


if __name__ == "__main__":
    quiet = "-q" in sys.argv
    unittest.main(argv=[a for a in sys.argv if a != "-q"], verbosity=0 if quiet else 1)
