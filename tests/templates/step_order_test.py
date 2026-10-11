#!/usr/bin/env python3
"""Tests for the templates' tests/step_order.py: a scenario that takes an
action after its Then fails before its first step runs, naming the line
and the fix; a scenario in order runs as before; a step that matches
nothing keeps pytest-bdd's own error.

Each case runs pytest on a scratch project with plain pytest-bdd steps.
It needs pytest and pytest-bdd in the Python that runs it; without, it
skips:

    python3 tests/templates/step_order_test.py
    bin/uv run --no-project --with pytest --with pytest-bdd python tests/templates/step_order_test.py
"""

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
CHECK = ROOT / "skills" / "build" / "templates" / "web-app" / "tests" / "step_order.py"

try:
    import pytest  # noqa: F401
    import pytest_bdd  # noqa: F401

    HAS_PYTEST_BDD = True
except ImportError:
    HAS_PYTEST_BDD = False

STEPS = '''
import os
from pytest_bdd import given, parsers, scenarios, then, when

scenarios("orders.feature")


@given("the kitchen is open")
def _open() -> None:
    pass


@when(parsers.parse('"{who}" orders'))
def _orders(who: str) -> None:
    # Leaves a mark, so a test can tell whether any action ran.
    open(os.environ["MARK"], "a").write(who + "\\n")


@then(parsers.parse('"{who}" is served'))
def _served(who: str) -> None:
    pass
'''


@unittest.skipUnless(HAS_PYTEST_BDD, "pytest-bdd isn't installed for this Python")
class StepOrderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp()
        self.project = Path(self.tmp)
        tests = self.project / "tests"
        tests.mkdir()
        shutil.copy(CHECK, tests / "step_order.py")
        (self.project / "pytest.ini").write_text("[pytest]\ntestpaths = tests\n")
        (tests / "conftest.py").write_text(
            "import sys, os\n"
            "sys.path.insert(0, os.path.dirname(__file__))\n"
            "from step_order import pytest_bdd_before_scenario  # noqa: F401\n"
        )
        (tests / "orders_test.py").write_text(STEPS)
        self.mark = self.project / "mark"

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp)

    def run_feature(self, scenario: str) -> subprocess.CompletedProcess[str]:
        (self.project / "tests" / "orders.feature").write_text(
            "Feature: Orders\n\n" + scenario
        )
        return subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"],
            cwd=self.project,
            capture_output=True,
            text=True,
            env={"MARK": str(self.mark), "PATH": "/usr/bin:/bin"},
        )

    def test_an_action_after_a_then_fails_first_and_says_why(self) -> None:
        result = self.run_feature(
            "  Scenario: Two orders\n"
            "    Given the kitchen is open\n"
            '    When "dani" orders\n'
            '    Then "dani" is served\n'
            '    And "carlos" orders\n'
            '    Then "carlos" is served\n'
        )
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("orders.feature:7", result.stdout)
        self.assertIn('"And "carlos" orders" is an action', result.stdout)
        self.assertIn("move this action above the first Then", result.stdout)
        # Nothing ran: the failure comes before the first step.
        self.assertFalse(self.mark.exists())

    def test_a_scenario_in_order_runs(self) -> None:
        result = self.run_feature(
            "  Scenario: Two orders\n"
            "    Given the kitchen is open\n"
            '    When "dani" orders\n'
            '    And "carlos" orders\n'
            '    Then "dani" is served\n'
            '    And "carlos" is served\n'
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(self.mark.read_text(), "dani\ncarlos\n")

    def test_a_step_matching_nothing_keeps_pytest_bdds_error(self) -> None:
        result = self.run_feature(
            "  Scenario: A typo\n"
            "    Given the kitchen is open\n"
            '    When "dani" orders\n'
            '    Then "dani" is sevred\n'
        )
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("Step definition is not found", result.stdout)
        self.assertNotIn("is an action", result.stdout)


if __name__ == "__main__":
    unittest.main()
