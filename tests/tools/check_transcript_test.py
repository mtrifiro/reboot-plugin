"""Tests for tools/check-transcript.py: the shape of a real build session."""

import importlib.util
import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
spec = importlib.util.spec_from_file_location("check_transcript", os.path.join(ROOT, "tools/check-transcript.py"))
ct = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ct)


def session(*texts):
    f = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False)
    for t in texts:
        f.write(json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": t}]}}) + "\n")
    f.close()
    return ct.Path(f.name)


class CheckTranscriptTest(unittest.TestCase):
    def test_three_reports_and_quiet(self):
        r = ct.check(session(
            "**Welcome to Reboot.** A Reboot app is built from your domain's objects.",
            "Which parts does the first version cover?",
            "A proposed model is being built. Objects include rooms and stays.",
            "The app has a proposed domain model.\n\n| Object | What it can do | Who |",
            "The app has a feature spec. Each rule and its scenarios follow.",
            "The app has been built. Each method has its code.",
            "The app is being tested with the full feature suite.",
            "The first prototype is running, for your review.",
        ))
        self.assertTrue(r["welcome_first"])
        self.assertEqual(r["reports_in_order"], ["welcome", "domain-model", "feature-spec", "built", "full-suite", "review"])
        self.assertEqual(r["between"], [])
        self.assertEqual(r["first_person"], 0)

    def test_commentary_first_person_and_settled_are_counted(self):
        r = ct.check(session(
            "Now the API step references, read together.",
            "I'll build the rooms next. The design is settled — rooms first.",
        ))
        self.assertFalse(r["welcome_first"])
        self.assertEqual(len(r["between"]), 2)
        self.assertEqual(r["first_person"], 1)
        self.assertEqual(len(r["settled"]), 1)
        self.assertEqual(r["dashes"], 1)

    def test_code_is_ignored(self):
        r = ct.check(session("Welcome to Reboot. `I; settled — x`"))
        self.assertEqual((r["first_person"], r["dashes"], r["semicolons"]), (0, 0, 0))


if __name__ == "__main__":
    quiet = "-q" in sys.argv
    unittest.main(argv=[a for a in sys.argv if a != "-q"], verbosity=0 if quiet else 1)
