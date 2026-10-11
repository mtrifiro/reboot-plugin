"""Fails a scenario before its first step runs when its feature file
says something reboot.bdd reads as something else, and names the line
and the fix; a sibling of `step_order.py`, on different hooks.

- A `Rule:` with no `Scenario:` under it is read by people and the
  dashboard but tested by nothing, so a rule already written down can
  stay green while false. The feature's first scenario fails naming
  the rule, unless the feature is tagged `@wip` (still being written).
- A `does`, `spawns` or `attempts` step with its `with` clauses after
  the actor matches no step: the clauses go before `on`.
- A quoted saved value in a property clause (`scope_id="<order id>"`)
  is the literal text, not the value; recall it bare (`scope_id=<order
  id>`). Quotes are right only in the state-id position (`of "<id>"`).
- A backtick inside a quoted clause value splits the clause, and the
  step matches nothing; assert with `containing` on a part without it.

`conftest.py` imports both hooks."""

import re
from pathlib import Path

import pytest

ACTION_WITH_AFTER_ACTOR = re.compile(
    r'^"[^"]*" (?:does|spawns|attempts) (?:a|an) `\w+` on `[\w.]+`(?: of "[^"]*")? with '
)
QUOTED_RECALL_IN_CLAUSE = re.compile(r'`[^`]*[:=]\s*"<[^<>"]+>"[^`]*`')
QUOTED_VALUE = re.compile(r'[:=]\s*"([^"]*)"')
RULE = re.compile(r"^\s*Rule:\s*(.*)$")
SCENARIO = re.compile(r"^\s*(?:Scenario|Example|Scenario Outline|Scenario Template):")
FEATURE = re.compile(r"^\s*Feature:")


def rules_without_scenarios(text: str) -> list[tuple[int, str]]:
    """(line, name) of every Rule with no Scenario before the next Rule;
    [] when the feature itself is tagged @wip."""
    lines = text.split("\n")
    tags_before_feature: list[str] = []
    for line in lines:
        if FEATURE.match(line):
            break
        if line.strip().startswith("@"):
            tags_before_feature += line.split()
    if "@wip" in tags_before_feature:
        return []
    out: list[tuple[int, str]] = []
    current: tuple[int, str] | None = None
    seen_scenario = False
    for number, line in enumerate(lines, 1):
        if RULE.match(line):
            if current and not seen_scenario:
                out.append(current)
            current = (number, RULE.match(line).group(1).strip())  # type: ignore[union-attr]
            seen_scenario = False
        elif SCENARIO.match(line):
            seen_scenario = True
    if current and not seen_scenario:
        out.append(current)
    return out


def step_problems(step) -> list[str]:  # type: ignore[no-untyped-def]
    """What is wrong with one step's text, as reboot.bdd would read it."""
    name = step.name
    problems = []
    if ACTION_WITH_AFTER_ACTOR.match(name):
        problems.append(
            "the `with` clauses go before the actor: "
            '"<user>" does a `method` with `x=1` on `Type` of "<id>"'
        )
    if QUOTED_RECALL_IN_CLAUSE.search(name):
        problems.append(
            'a quoted `<name>` in a clause is the literal text, not the saved value: '
            "write `field=<name>` to recall it (quotes only in `of \"<id>\"`)"
        )
    for value in QUOTED_VALUE.findall(name):
        if "`" in value:
            problems.append(
                "a backtick inside a quoted value splits the clause and the step matches "
                "nothing: assert with `containing` on a part of the value without it"
            )
            break
    return problems


def pytest_collection_modifyitems(session, config, items) -> None:  # type: ignore[no-untyped-def]
    """Rules with no scenario, per feature, to be reported by that
    feature's first scenario."""
    pending: dict[str, list[tuple[int, str]]] = {}
    for item in items:
        scenario = getattr(getattr(item, "obj", None), "__scenario__", None)
        if scenario is None:
            continue
        feature = scenario.feature
        key = feature.filename
        if key in pending:
            continue
        try:
            text = Path(feature.filename).read_text(encoding="utf-8")
        except OSError:
            continue
        pending[key] = rules_without_scenarios(text)
    config._feature_lint_rules = {k: v for k, v in pending.items() if v}  # type: ignore[attr-defined]


def pytest_runtest_setup(item) -> None:  # type: ignore[no-untyped-def]
    scenario = getattr(getattr(item, "obj", None), "__scenario__", None)
    if scenario is None:
        return
    feature = scenario.feature
    rules = getattr(item.config, "_feature_lint_rules", {}).pop(feature.filename, None)
    if rules:
        listed = "; ".join(f"line {line}: {name}" for line, name in rules)
        pytest.fail(
            f"{feature.rel_filename}: a Rule with no Scenario under it is tested by nothing "
            f"and stays green while false ({listed}). Put at least one Scenario under each "
            "Rule, or tag the feature @wip while it is being written.",
            pytrace=False,
        )
    for step in scenario.steps:
        for problem in step_problems(step):
            pytest.fail(
                f'{feature.rel_filename}:{step.line_number}: "{step.keyword} {step.name}": {problem}.',
                pytrace=False,
            )
