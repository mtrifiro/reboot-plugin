"""Fails a scenario at once, before its first step runs, when it takes an
action after its checks, and says how to fix it.

Gherkin reads `And` and `But` as the keyword above them, so an action
written as `And "carlos" does ...` under a `Then` is looked up as a
check. No check matches it, and pytest-bdd stops at that step with
"Step definition is not found", after running the steps above it. This
hook looks every step up first and names the cause instead.

A scenario is set-up, then actions, then checks. An action that must
follow a check goes above the first `Then`, or starts a scenario of its
own (`feature` skill, Step 2)."""

import copy

import pytest
from pytest_bdd.parser import Feature, Scenario
from pytest_bdd.scenario import get_step_function


def pytest_bdd_before_scenario(
    request: pytest.FixtureRequest, feature: Feature, scenario: Scenario
) -> None:
    for step in scenario.steps:
        # Steps typed as checks: a Then, and an And or But under one.
        if step.type != "then":
            continue
        if get_step_function(request=request, step=step) is not None:
            continue
        # Would it run as an action?
        action = copy.copy(step)
        action.type = "when"
        if get_step_function(request=request, step=action) is None:
            continue  # not found as anything: pytest-bdd's own error says so
        pytest.fail(
            f"{feature.rel_filename}:{step.line_number}: "
            f'"{step.keyword} {step.name}" is an action, but under a Then '
            "it is read as a check, and no check matches it. A scenario is "
            "set-up, then actions, then checks: move this action above the "
            "first Then, or split the scenario in two.",
            pytrace=False,
        )
