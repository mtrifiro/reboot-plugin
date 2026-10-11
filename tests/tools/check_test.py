#!/usr/bin/env python3
"""Tests for `tools/check.py`'s selector, path to checks: skill text
picks the CLI and symbol checks and the eval cases that load the skill
(python's through build, which reads its references), never the
template tests; a template file picks the template tests, shellcheck
and the smoke, and no eval; a hook, a shim, a tool, a test file, a mod
and an eval case each pick their own; a path no row matches runs the
shell and unit stages whole; lint runs whole on any change. Every
token in PATHS names a check, every test file under tests/ is a check,
and every check is reachable from some path. The smoke builds only
the template a change lies in, all three for a shared file; with
--changed, a stage the changes leave empty is skipped with a line
saying so; --skip and --template narrow a run; checks run fail-first
(the changes' checks, last run's failures, then shortest first); the
history keeps each check's times, and a check past twice its median
warns; the unit pool keeps the serial checks out.

    python3 tests/tools/check_test.py
"""

import contextlib
import importlib.util
import io
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
spec = importlib.util.spec_from_file_location("check", ROOT / "tools" / "check.py")
check = importlib.util.module_from_spec(spec)
sys.modules["check"] = check
spec.loader.exec_module(check)

LINT = {c.name for c in check.CHECKS if c.stage == "lint"}
UNIT = {c.name for c in check.CHECKS if c.stage == "unit"}
CASES = {
    "route-mcp": [r'"skill"\s*:\s*"(?:[\w-]+:)?app"', r'"skill"\s*:\s*"(?:[\w-]+:)?mcp-ui"'],
    "design-roles": [r'"skill"\s*:\s*"(?:[\w-]+:)?build"'],
    "workflow-recorded": [r'"skill"\s*:\s*"(?:[\w-]+:)?(?:build|feature)"'],
}


def pick(*paths):
    return check.select(list(paths), CASES)


class SelectTest(unittest.TestCase):
    def test_nothing_changed_selects_nothing(self) -> None:
        sel = pick()
        self.assertEqual(sel.checks, set())
        self.assertEqual(sel.cases, set())

    def test_skill_text_picks_lint_cli_symbols_and_its_cases(self) -> None:
        sel = pick("skills/build/SKILL.md")
        self.assertEqual(sel.checks, LINT | {"check-cli", "check-symbols"})
        self.assertEqual(sel.cases, {"design-roles", "workflow-recorded"})

    def test_feature_skill_is_covered_by_the_case_that_loads_it(self) -> None:
        self.assertEqual(pick("skills/feature/SKILL.md").cases, {"workflow-recorded"})

    def test_python_references_are_covered_through_build(self) -> None:
        sel = pick("skills/python/references/api-methods.md")
        self.assertEqual(sel.cases, {"design-roles", "workflow-recorded"})

    def test_a_skill_no_case_loads_names_none(self) -> None:
        self.assertEqual(pick("skills/deploy/SKILL.md").cases, set())

    def test_template_file_picks_template_checks_and_no_eval(self) -> None:
        sel = pick("skills/build/templates/web-app/scripts/test.sh")
        self.assertIn("shellcheck", sel.checks)
        self.assertIn("templates-smoke", sel.checks)
        self.assertIn("templates/test_sh", sel.checks)
        self.assertIn("pytest:test_sh", sel.checks)
        self.assertNotIn("hooks/orphans", sel.checks)
        self.assertEqual(sel.cases, set())

    def test_hook_picks_hook_tests_and_shellcheck(self) -> None:
        sel = pick("hooks/auto-approve.sh")
        self.assertEqual(sel.checks - LINT, set(check.GROUPS["hook-tests"]) | {"shellcheck"})

    def test_schema_guard_picks_its_test_with_node(self) -> None:
        sel = pick("hooks/schema-guard/schema.test.ts")
        self.assertEqual(sel.checks - LINT,
                         {"hooks/schema_guard", "schema-guard-node", "shellcheck"})

    def test_reminder_reaches_every_eval_case(self) -> None:
        self.assertEqual(pick("hooks-handlers/remind.sh").cases, set(CASES))

    def test_shim_picks_shim_tests_and_shellcheck(self) -> None:
        sel = pick("bin/rbt")
        self.assertTrue(set(check.GROUPS["shim-tests"]) <= sel.checks)
        self.assertIn("shellcheck", sel.checks)
        self.assertNotIn("templates/copy", sel.checks)

    def test_tool_picks_its_own_test(self) -> None:
        self.assertEqual(pick("tools/findings.py").checks - LINT, {"tools/findings"})

    def test_test_file_runs_itself_in_every_stage_it_has(self) -> None:
        self.assertEqual(pick("tests/templates/test_sh_test.py").checks - LINT,
                         {"templates/test_sh", "pytest:test_sh"})

    def test_mod_picks_mods(self) -> None:
        self.assertEqual(pick("mods/reboot-progress/index.ts").checks - LINT, {"mods"})

    def test_eval_case_picks_itself_and_the_runner_test(self) -> None:
        sel = pick("evals/route-mcp/prompt.md")
        self.assertEqual(sel.checks - LINT, {"tools/run_evals"})
        self.assertEqual(sel.cases, {"route-mcp"})

    def test_unmapped_path_runs_shell_and_unit_whole(self) -> None:
        sel = pick("somewhere/new.txt")
        self.assertEqual(sel.unmapped, ["somewhere/new.txt"])
        self.assertEqual(sel.checks, LINT | UNIT | {"shellcheck"})

    def test_text_only_paths_run_lint_only(self) -> None:
        self.assertEqual(pick("findings/x/y.md", "README.md", "docs/a.md").checks, LINT)


class TemplatesTest(unittest.TestCase):
    def test_a_change_in_one_template_smokes_that_one(self) -> None:
        self.assertEqual(pick("skills/build/templates/web-app/web/src/App.tsx").templates, {"web-app"})
        self.assertEqual(pick("skills/build/templates/both/AGENTS.md",
                              "skills/build/templates/mcp-ui/pyproject.toml").templates,
                         {"both", "mcp-ui"})

    def test_a_shared_file_smokes_all_three(self) -> None:
        for path in ("skills/build/templates/copy.sh", "skills/build/templates/README.md",
                     "VERSION", "bin/rbt", "tools/templates-smoke.sh"):
            self.assertEqual(pick(path).templates, set(check.TEMPLATES), path)

    def test_no_smoke_no_templates(self) -> None:
        self.assertEqual(pick("skills/build/SKILL.md").templates, set())

    def test_the_smoke_command_names_the_templates(self) -> None:
        smoke = check.BY_NAME["templates-smoke"]
        self.assertEqual(check.command_for(smoke, None), smoke.cmd)
        self.assertEqual(check.command_for(smoke, {"both", "web-app"}), smoke.cmd + ["web-app", "both"])
        self.assertEqual(check.history_key(smoke, {"web-app"}), "templates-smoke[web-app]")
        self.assertEqual(check.history_key(smoke, None), "templates-smoke")


class MainTest(unittest.TestCase):
    """main() with the changed paths stubbed and nothing really run."""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.ran = []
        stubs = {
            "changed_paths": lambda base: list(self.paths),
            "run_check": lambda c, templates=None: (self.ran.append((c.name, templates)) or ("ok", "", 0.0)),
            "HISTORY": self.tmp / "history.json",
        }
        self.saved = {k: getattr(check, k) for k in stubs}
        for k, v in stubs.items():
            setattr(check, k, v)
        self.paths = []

    def tearDown(self) -> None:
        for k, v in self.saved.items():
            setattr(check, k, v)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def main(self, *argv) -> tuple:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = check.main(list(argv))
        return rc, out.getvalue()

    def test_changed_honors_stage_and_skips_with_a_line(self) -> None:
        self.paths = ["skills/build/SKILL.md"]
        rc, out = self.main("--changed", "BASE", "--stage", "integration")
        self.assertEqual(rc, 0)
        self.assertEqual({n for n, _ in self.ran}, {"check-cli", "check-symbols"})
        self.paths = ["findings/x/y.md"]
        self.ran.clear()
        rc, out = self.main("--changed", "BASE", "--stage", "integration")
        self.assertEqual((rc, self.ran), (0, []))
        self.assertIn("== integration: skipped, the changed paths select none of its checks", out)

    def test_changed_smokes_only_the_changed_template(self) -> None:
        self.paths = ["skills/build/templates/mcp-ui/frontend/src/App.tsx"]
        self.main("--changed", "BASE", "--stage", "integration", "--only", "templates-smoke")
        self.assertEqual(self.ran, [("templates-smoke", {"mcp-ui"})])

    def test_template_flag_outside_the_change_skips_the_smoke(self) -> None:
        self.paths = ["skills/build/templates/mcp-ui/frontend/src/App.tsx"]
        rc, out = self.main("--changed", "BASE", "--only", "templates-smoke", "--template", "web-app")
        self.assertEqual((rc, self.ran), (0, []))
        self.assertIn("skipped", out)
        rc, out = self.main("--changed", "BASE", "--only", "templates-smoke", "--template", "web-app",
                            "--dry-run")
        self.assertNotIn("would run", out)
        self.paths = ["skills/build/templates/copy.sh"]
        rc, out = self.main("--changed", "BASE", "--only", "templates-smoke", "--template", "web-app",
                            "--dry-run")
        self.assertIn("would run: templates-smoke web-app", out)
        self.assertEqual(self.ran, [])

    def test_skip_leaves_a_check_out(self) -> None:
        self.main("--stage", "integration", "--skip", "templates-smoke")
        names = {n for n, _ in self.ran}
        self.assertNotIn("templates-smoke", names)
        self.assertIn("check-cli", names)

    def test_a_run_is_recorded(self) -> None:
        self.main("--stage", "lint")
        hist = check.load_history()
        self.assertEqual(hist["gen-index"]["last"], "ok")
        self.assertEqual(len(hist["gen-index"]["times"]), 1)


class OrderTest(unittest.TestCase):
    def test_changed_then_failed_then_shortest(self) -> None:
        unit = [c for c in check.CHECKS if c.stage == "unit"]
        hist = {"tools/findings": {"last": "fail", "times": [0.2]},
                "hooks/remind": {"last": "ok", "times": [30.0]}}
        order = [c.name for c in check.fail_first(unit, {"hooks/orphans"}, hist)]
        self.assertEqual(order[:2], ["hooks/orphans", "tools/findings"])
        rest = order[2:]
        times = [check.median_time(hist, n) or check.BY_NAME[n].seconds for n in rest]
        self.assertEqual(times, sorted(times))
        self.assertEqual(rest[-1], "hooks/remind", "a recorded median beats the table")


class HistoryTest(unittest.TestCase):
    def test_times_are_kept_and_capped(self) -> None:
        hist = {}
        for i in range(check.KEEP + 5):
            check.record(hist, "x", "ok", float(i))
        self.assertEqual(len(hist["x"]["times"]), check.KEEP)
        self.assertEqual(hist["x"]["times"][-1], float(check.KEEP + 4))
        check.record(hist, "x", "skip", 0.0)
        self.assertEqual(hist["x"]["last"], "skip")
        self.assertEqual(len(hist["x"]["times"]), check.KEEP, "a skip has no time")

    def test_twice_the_median_warns(self) -> None:
        hist = {"x": {"times": [4.0, 5.0, 6.0]}}
        self.assertIsNone(check.slow_warning(hist, "x", 9.0))
        self.assertIn("2.2x its median of 5.0s", check.slow_warning(hist, "x", 11.0))
        self.assertIsNone(check.slow_warning({"x": {"times": [0.1, 0.1, 0.1]}}, "x", 0.5),
                          "a small check is not slow on noise")
        self.assertIsNone(check.slow_warning({"x": {"times": [1.0, 1.0]}}, "x", 9.0), "too few runs")

    def test_a_broken_file_reads_as_empty(self) -> None:
        tmp = Path(tempfile.mkdtemp())
        try:
            (tmp / "h.json").write_text("{not json")
            self.assertEqual(check.load_history(tmp / "h.json"), {})
            check.save_history({"x": {"last": "ok"}}, tmp / "sub" / "h.json")
            self.assertEqual(check.load_history(tmp / "sub" / "h.json"), {"x": {"last": "ok"}})
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class PoolTest(unittest.TestCase):
    def test_serial_checks_run_after_the_pool(self) -> None:
        unit = [c for c in check.CHECKS if c.stage == "unit"]
        serial = {c.name for c in unit if c.serial}
        self.assertTrue({"templates/placeholder", "templates/ports"} <= serial)
        ran = []
        saved = check.run_check
        check.run_check = lambda c, templates=None: (ran.append(c.name) or ("ok", "", 0.0))
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                failed = check.run_stage(unit, 4, False, {})
        finally:
            check.run_check = saved
        self.assertEqual(failed, [])
        self.assertEqual(set(ran[-len(serial):]), serial)

    def test_failure_output_comes_after_the_lines(self) -> None:
        checks = [check.BY_NAME["tools/check"], check.BY_NAME["tools/findings"]]
        saved = check.run_check
        check.run_check = lambda c, templates=None: (
            ("fail", "boom\n", 0.0) if c.name == "tools/check" else ("ok", "quiet\n", 0.0))
        out = io.StringIO()
        try:
            with contextlib.redirect_stdout(out):
                failed = check.run_stage(checks, 2, False, {})
        finally:
            check.run_check = saved
        self.assertEqual(failed, ["tools/check"])
        text = out.getvalue()
        self.assertNotIn("quiet", text)
        self.assertGreater(text.index("--- tools/check output ---"), text.index("tools/findings"))
        self.assertIn("boom", text)


class TableTest(unittest.TestCase):
    def test_every_token_names_a_check_or_group(self) -> None:
        for glob, tokens in check.PATHS:
            for tok in tokens:
                ok = (tok in check.BY_NAME or tok in ("@self", "evals", "evals:all")
                      or tok[1:] in check.GROUPS)
                self.assertTrue(ok, f"{glob}: {tok}")

    def test_every_test_file_is_a_check(self) -> None:
        files = {str(p.relative_to(ROOT)) for p in ROOT.glob("tests/*/*_test.py")}
        self.assertEqual(files - {c.file for c in check.CHECKS}, set())

    def test_every_check_is_reachable_from_a_path(self) -> None:
        probes = ["skills/build/SKILL.md", "skills/build/templates/web-app/x.py",
                  "skills/build/templates/AGENTS.md", "hooks/schema-guard.sh", "mods/m/x",
                  "tools/style-check.py", "VERSION", "lib/own.sh"]
        probes += [str(p.relative_to(ROOT)) for p in ROOT.glob("tests/*/*_test.py")]
        reached = pick(*probes).checks
        self.assertEqual(set(check.BY_NAME) - reached, set())

    def test_stages_are_known_and_in_order(self) -> None:
        for c in check.CHECKS:
            self.assertIn(c.stage, check.STAGE_NAMES, c.name)
        order = [check.STAGE_NAMES.index(c.stage) for c in check.CHECKS]
        self.assertEqual(order, sorted(order))


class EvalCasesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_reads_the_skill_graders_only(self) -> None:
        graders = self.tmp / "evals" / "c1" / "graders"
        graders.mkdir(parents=True)
        (graders / "loads-app.md").write_text(
            "---\ntype: tool_used\ntool: Skill\ninput_match: '\"skill\"\\s*:\\s*\"app\"'\n---\n")
        (graders / "asks.md").write_text(
            "---\ntype: tool_used\ntool: AskUserQuestion\ninput_match: 'x'\n---\n")
        (self.tmp / "evals" / "results").mkdir()
        cases = check.eval_cases(self.tmp)
        self.assertEqual(cases, {"c1": ['"skill"\\s*:\\s*"app"']})
        self.assertEqual(check.cases_for_skill("app", cases), ["c1"])

    def test_real_cases_cover_the_front_door_skills(self) -> None:
        cases = check.eval_cases()
        for skill in ("app", "build", "web-app", "mcp-ui", "feature"):
            self.assertTrue(check.cases_for_skill(skill, cases), skill)


if __name__ == "__main__":
    unittest.main()
