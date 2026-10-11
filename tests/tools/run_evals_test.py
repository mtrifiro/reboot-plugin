#!/usr/bin/env python3
"""Tests for `tools/run-evals.sh`'s flags, against a fake `claude` that
only records what it was asked to run: a selected case with a fixture
gets `--scaffold`, by `--case` glob or `--tag`; a selection with no
fixture does not; an explicit `--scaffold` or `--no-scaffold` is left
alone; the wrapper always gets `--trust-plugin` and a Sonnet judge;
`--smoke` means one run, no ablation and a Haiku judge unless a flag
says otherwise; a case run cleanly is served from its cached result
the next time, until `--fresh`, a changed flag or a changed case file;
a selection that is partly cached runs the rest one case at a time;
each result prints every grader's votes per run.

    python3 tests/tools/run_evals_test.py
"""

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = ROOT / "tools" / "run-evals.sh"

FAKE_CLAUDE = '#!/bin/sh\nprintf "%s\\n" "$@" > "$CLAUDE_ARGS"\n'
# Also records each call and, when FAKE_RESULT names a JSON file, leaves
# it as this run's result, the way the runner writes one.
FAKE_CLAUDE_RESULT = (
    '#!/bin/sh\n'
    'printf "%s\\n" "$@" > "$CLAUDE_ARGS"\n'
    'echo "$*" >> "$CLAUDE_ARGS.calls"\n'
    'case="$(printf "%s\\n" "$@" | sed -n "/^--case$/{n;p;}" | tail -n 1)"\n'
    'dir="evals/results/$(date +%s%N)-$$"\n'
    'mkdir -p "$dir"\n'
    'sed "s/CASE/$case/" "$FAKE_RESULT" > "$dir/aggregate-result.json"\n'
)


def result_for(score_votes: list) -> dict:
    """An aggregate result for one case named CASE: one grader, per-run votes."""
    runs = [{"score": score, "error": None, "graders": [
        {"name": "g", "passed": sum(v) * 2 > len(v), "scored": True, "judgeVotes": v}]}
        for score, v in score_votes]
    return {"partial": False, "suite": {"judgeModel": "haiku", "ablation": "none"},
            "cases": [{"name": "CASE", "arms": {"with": runs},
                       "aggregates": {"score": sum(r["score"] for r in runs) / len(runs)}}]}


class RunEvalsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        bindir = self.tmp / "bin"
        bindir.mkdir()
        fake = bindir / "claude"
        fake.write_text(FAKE_CLAUDE)
        fake.chmod(0o755)
        self.args_file = self.tmp / "args"
        self.env = dict(
            os.environ,
            PATH=f"{bindir}:{os.environ['PATH']}",
            CLAUDE_ARGS=str(self.args_file),
            TMPDIR=str(self.tmp),
            EVALS_RESULTS_DIR=str(self.tmp / "results"),
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_with(self, *flags: str) -> list:
        subprocess.run(
            ["bash", str(SCRIPT), *flags],
            env=self.env,
            capture_output=True,
            text=True,
            check=True,
        )
        return self.args_file.read_text().split("\n")[:-1]

    def test_case_with_fixture_gets_scaffold(self) -> None:
        self.assertIn("--scaffold", self.run_with("--case", "workflow-recorded"))

    def test_case_glob_with_fixture_gets_scaffold(self) -> None:
        self.assertIn("--scaffold", self.run_with("--case=workflow-*"))

    def test_tag_with_fixture_gets_scaffold(self) -> None:
        self.assertIn("--scaffold", self.run_with("--tag", "workflow"))

    def test_every_case_gets_scaffold(self) -> None:
        self.assertIn("--scaffold", self.run_with("--runs", "1"))

    def test_case_without_fixture_gets_none(self) -> None:
        args = self.run_with("--case", "route-mcp")
        self.assertNotIn("--scaffold", args)

    def test_tag_without_fixture_gets_none(self) -> None:
        args = self.run_with("--tag", "routing")
        self.assertNotIn("--scaffold", args)

    def test_explicit_no_scaffold_is_kept(self) -> None:
        args = self.run_with("--case", "workflow-recorded", "--no-scaffold")
        self.assertNotIn("--scaffold", args)
        self.assertIn("--no-scaffold", args)

    def test_explicit_scaffold_is_not_doubled(self) -> None:
        args = self.run_with("--scaffold", "--tag", "workflow")
        self.assertEqual(args.count("--scaffold"), 1)

    def test_trust_and_judge_defaults(self) -> None:
        args = self.run_with("--case", "route-mcp")
        self.assertEqual(args[:3], ["plugin", "eval", "."])
        self.assertIn("--trust-plugin", args)
        self.assertEqual(args[args.index("--judge-model") + 1], "sonnet")


class CacheTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        bindir = self.tmp / "bin"
        bindir.mkdir()
        fake = bindir / "claude"
        fake.write_text(FAKE_CLAUDE_RESULT)
        fake.chmod(0o755)
        self.args_file = self.tmp / "args"
        self.result = self.tmp / "result.json"
        self.result.write_text(json.dumps(result_for([(0.5, [True, False, False]), (1.0, [True, True, True])])))
        self.env = dict(
            os.environ,
            PATH=f"{bindir}:{os.environ['PATH']}",
            CLAUDE_ARGS=str(self.args_file),
            FAKE_RESULT=str(self.result),
            TMPDIR=str(self.tmp),
            EVALS_RESULTS_DIR=str(self.tmp / "results"),
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_with(self, *flags: str) -> tuple:
        """(the runner's calls, stdout)."""
        calls = Path(str(self.args_file) + ".calls")
        if calls.exists():
            calls.unlink()
        r = subprocess.run(["bash", str(SCRIPT), *flags], env=self.env, capture_output=True, text=True)
        self.assertIn(r.returncode, (0, 1), r.stderr)
        return (calls.read_text().splitlines() if calls.exists() else []), r.stdout

    def test_smoke_is_one_run_no_ablation_haiku(self) -> None:
        (call,), _ = self.run_with("--smoke", "--case", "route-mcp")
        self.assertIn("--runs 1", call)
        self.assertIn("--ablation none", call)
        self.assertIn("--judge-model haiku", call)
        self.assertNotIn("sonnet", call)
        self.assertNotIn("--smoke", call)
        (call,), _ = self.run_with("--smoke", "--runs", "2", "--judge-model", "sonnet", "--case", "route-mcp")
        self.assertIn("--runs 2", call)
        self.assertNotIn("--runs 1", call)
        self.assertNotIn("haiku", call)

    def test_a_second_run_is_served_from_the_cache(self) -> None:
        calls, out = self.run_with("--smoke", "--case", "route-mcp")
        self.assertEqual(len(calls), 1)
        self.assertIn("result: route-mcp score 0.75", out)
        calls, out = self.run_with("--smoke", "--case", "route-mcp")
        self.assertEqual(calls, [], "served from the cache")
        self.assertIn("cached: route-mcp score 0.75", out)
        calls, _ = self.run_with("--smoke", "--fresh", "--case", "route-mcp")
        self.assertEqual(len(calls), 1, "--fresh runs it")
        self.assertNotIn("--fresh", calls[0])
        calls, _ = self.run_with("--case", "route-mcp", "--runs", "1", "--ablation", "none")
        self.assertEqual(len(calls), 1, "another judge is another key")

    def test_a_partly_cached_selection_runs_the_rest_one_by_one(self) -> None:
        self.run_with("--smoke", "--case", "route-mcp")
        calls, out = self.run_with("--smoke", "--case", "route-*")
        self.assertIn("cached: route-mcp", out)
        cases = sorted(c.split("--case ")[1] for c in calls)
        self.assertNotIn("route-mcp", cases)
        self.assertGreater(len(cases), 0)
        for c in calls:
            self.assertNotIn("route-*", c)

    def test_a_failed_run_is_not_cached(self) -> None:
        bad = result_for([(0.0, [False])])
        bad["cases"][0]["arms"]["with"][0]["error"] = "timeout"
        self.result.write_text(json.dumps(bad))
        self.run_with("--smoke", "--case", "route-mcp")
        calls, _ = self.run_with("--smoke", "--case", "route-mcp")
        self.assertEqual(len(calls), 1)

    def test_the_spread_shows_each_graders_votes_per_run(self) -> None:
        _, out = self.run_with("--smoke", "--case", "route-mcp")
        self.assertIn("score per run 0.50 1.00", out)
        self.assertRegex(out, r"g\s+PFF PPP   4/6 votes, 1/2 runs")
        self.assertIn("differ by up to 0.50", out)


if __name__ == "__main__":
    unittest.main()
