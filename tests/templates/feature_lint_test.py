#!/usr/bin/env python3
"""Tests for the templates' tests/feature_lint.py: a Rule with no
Scenario fails the feature's first scenario (not under @wip); a call
step with its `with` clauses after the actor, a quoted saved value in
a clause and a backtick inside a quoted value each fail before the
first step runs, naming the line and the fix; a clean feature runs.

Each case runs pytest on a scratch project with catch-all pytest-bdd
steps. It needs pytest and pytest-bdd in the Python that runs it;
without, it skips:

    python3 tests/templates/feature_lint_test.py
    bin/uv run --no-project --with pytest --with pytest-bdd python tests/templates/feature_lint_test.py
"""

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
LINT = ROOT / "skills" / "build" / "templates" / "web-app" / "tests" / "feature_lint.py"

try:
    import pytest  # noqa: F401
    import pytest_bdd  # noqa: F401

    HAS_PYTEST_BDD = True
except ImportError:
    HAS_PYTEST_BDD = False

STEPS = '''
from pytest_bdd import given, parsers, scenarios, then, when

scenarios("orders.feature")


@given(parsers.re(r".*"))
def _given():
    pass


@when(parsers.re(r".*"))
def _when():
    pass


@then(parsers.re(r".*"))
def _then():
    pass
'''

CLEAN = '''Feature: Orders
  Rule: An order is sent once
    Scenario: Sending
      Given "carlos" is an authenticated user
      When "carlos" does a `send` with `item="soup"` on `Order` of "<order id>"
      Then as "carlos", `get` on the `Order` for "<order id>" has `sent=true`
'''


@unittest.skipUnless(HAS_PYTEST_BDD, "pytest-bdd isn't installed for this Python")
class FeatureLintTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp()
        tests = Path(self.tmp) / "tests"
        tests.mkdir()
        shutil.copy(LINT, tests / "feature_lint.py")
        (Path(self.tmp) / "pytest.ini").write_text("[pytest]\ntestpaths = tests\n")
        (tests / "conftest.py").write_text(
            "import sys, os\n"
            "sys.path.insert(0, os.path.dirname(__file__))\n"
            "from feature_lint import pytest_collection_modifyitems, pytest_runtest_setup  # noqa\n"
        )
        (tests / "orders_test.py").write_text(STEPS)
        self.feature = tests / "orders.feature"

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_pytest(self, feature: str) -> subprocess.CompletedProcess:
        self.feature.write_text(feature)
        return subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests"],
            cwd=self.tmp, capture_output=True, text=True,
        )

    def test_a_clean_feature_runs(self) -> None:
        r = self.run_pytest(CLEAN)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("1 passed", r.stdout)

    def test_a_rule_with_no_scenario_fails_the_first_scenario(self) -> None:
        r = self.run_pytest(CLEAN + "\n  Rule: A sent order cannot be changed\n")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("a Rule with no Scenario under it", r.stdout)
        self.assertIn("A sent order cannot be changed", r.stdout)
        self.assertIn("tag the feature @wip", r.stdout)

    def test_a_wip_feature_may_have_an_empty_rule(self) -> None:
        r = self.run_pytest("@wip\n" + CLEAN + "\n  Rule: A sent order cannot be changed\n")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_with_clauses_after_the_actor(self) -> None:
        bad = CLEAN.replace(
            'When "carlos" does a `send` with `item="soup"` on `Order` of "<order id>"',
            'When "carlos" does a `send` on `Order` of "<order id>" with `item="soup"`')
        r = self.run_pytest(bad)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("orders.feature:5", r.stdout)
        self.assertIn("the `with` clauses go before the actor", r.stdout)

    def test_a_quoted_saved_value_in_a_clause(self) -> None:
        bad = CLEAN.replace('`item="soup"`', '`scope="<order id>"`')
        r = self.run_pytest(bad)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("is the literal text, not the saved value", r.stdout)

    def test_a_backtick_inside_a_quoted_value(self) -> None:
        bad = CLEAN.replace("`sent=true`", '`title="`rbt generate` dies"`')
        r = self.run_pytest(bad)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("a backtick inside a quoted value", r.stdout)
        self.assertIn("containing", r.stdout)


if __name__ == "__main__":
    unittest.main()
