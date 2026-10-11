#!/usr/bin/env python3
"""Tests for `tools/check.py`'s selector, path to checks: skill text
picks the CLI and symbol checks and the eval cases that load the skill
(python's through build, which reads its references), never the
template tests; a template file picks the template tests, shellcheck
and the smoke, and no eval; a hook, a shim, a tool, a test file, a mod
and an eval case each pick their own; a path no row matches runs the
shell and unit stages whole; lint runs whole on any change. Every
token in PATHS names a check, every test file under tests/ is a check,
and every check is reachable from some path.

    python3 tests/tools/check_test.py
"""

import importlib.util
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
