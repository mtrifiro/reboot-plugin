---
title: Specify Behavior in Feature Files
impact: MEDIUM
impactDescription: Feature files are the application's specification and its test suite at once; a suite written any other way is neither reviewable by the developer nor shown by the dashboard
tags: testing, bdd, gherkin, feature, scenario, rule, pytest-bdd, reboot.bdd, wip, blocked, custom-steps, world
summary: "The built-in steps' exact spelling (who calls, `creates` / `does`, saved values, `eventually`, aborts, tasks), `@wip` / `@blocked`, feature / rule / scenario shape, custom steps, mocks."
step: tests
applies: [mcp-ui, web-app, backend-only]
always: false
verified: 1.6.0
docs: ""
---

# Specify Behavior in Feature Files

## When you are here

You are writing the application's tests. They are Gherkin `.feature`
files run by `reboot.bdd`, which ships built-in steps for every call an
application takes; one file is read by the developer (as the
specification), by `pytest` (through the `Reboot()` harness), and by
the dashboard's Features page. Write scenarios in the built-in steps'
spelling below and a custom step only for what they cannot say. The
browser steps are [`testing-web-app.md`](testing-web-app.md); crash
tests stay on the harness ([`testing-failure-recovery.md`](testing-failure-recovery.md));
the workflow that agrees scenarios with the developer is the
[`feature` skill](../../feature/SKILL.md). The
[`reboot-bank-pydantic`](https://github.com/reboot-dev/reboot-bank-pydantic)
example's `tests/` is the reference for every pattern here.

## Do this

### Layout and the test module

```
pytest.ini                     # testpaths: tests; pythonpath: backend/src backend/api api
tests/
├── opening_accounts.feature   # One feature per capability.
├── transfers.feature
├── full_bank_test.py          # One module per application setup.
├── interest_test.py
├── web_test.py                # The scenarios that drive the web app.
└── opening_accounts.recordings/   # Made by running; git-ignored.
```

Name a `.feature` for the activity (`transfers.feature`), not a state
type. A test module is one application configuration: an `application`
fixture and a `scenarios(...)` call naming the features that run
against it.

```python
import pytest
from account_servicer import AccountServicer
from bank_servicer import BankServicer
from reboot.aio.applications import Application
from reboot.aio.auth.oauth import OAuth
from reboot.bdd import scenarios


@pytest.fixture
def application() -> Application:
    return Application(
        servicers=[AccountServicer, BankServicer],
        # Only for an app with `oauth=`: the harness is neither
        # `rbt dev run` nor `rbt serve`, so it needs the explicit
        # empty list (testing-web-app.md has the browser variant).
        oauth=OAuth(provider=..., allowed_origins=[]),
    )


scenarios('deposits.feature', 'withdrawals.feature')
```

Nothing imports the built-in steps: `reboot[dev]` registers them as a
pytest plugin ([`testing-project-setup.md`](testing-project-setup.md)).
`Given the "proxy" application is up` runs what a `proxy_application`
fixture returns. Run with `uv run pytest`, one file
(`uv run pytest tests/full_bank_test.py`), one scenario
(`-k "transfer between two"`), or by tag (`-m wip`, `-m "not wip"`).

### Feature, rule, scenario

```gherkin
Feature: Customers can transfer money between accounts
  A customer moves money from one of their accounts to another
  account of the bank in one step.

  Background:
    Given the application is up

  Rule: A transfer moves exactly the amount from one account to the other
    Neither account sees any other change.

    Scenario: A transfer between two customers' accounts
      Given "anonymous" is an unauthenticated user
      And "anonymous" creates a `Bank` via `create`
      And the resulting state id is saved as "bank id"
      When "anonymous" does a `sign_up` with `customer_id="test@reboot.dev"` on `Bank` of "<bank id>"
      And "anonymous" does an `open_account` with `initial_deposit=1000.0` on `Customer` of "test@reboot.dev"
      And the resulting `account_id` is saved as "first account id"
      And "anonymous" does a `sign_up` with `customer_id="test2@reboot.dev"` on `Bank` of "<bank id>"
      And "anonymous" does an `open_account` with `initial_deposit=0.0` on `Customer` of "test2@reboot.dev"
      And the resulting `account_id` is saved as "second account id"
      And "anonymous" does a `transfer` with `from_account_id=<first account id>` and `to_account_id=<second account id>` and `amount=250.0` on `Bank` of "<bank id>"
      Then as "anonymous", `balance` on the `Account` for "<first account id>" has `amount=750.0`
      And as "anonymous", `balance` on the `Account` for "<second account id>" has `amount=250.0`
```

- A **feature** is one thing a user can do, named as a sentence about
  the activity, with a paragraph saying what it is for.
- A **rule** is a business invariant someone would want verified
  (money is conserved, a balance never goes below zero), stated once
  in its name and description. A scenario that only shows what an
  operation does sits at the top level with no rule around it.
- A **scenario** is one concrete example, named for the situation,
  never restating the rule. A `Scenario Outline` with `Examples`
  shows one rule at several values.
- The **background** holds what every scenario starts from; keep a
  user out of it when only some scenarios use them.
- Tests of Reboot's own mechanisms (a spawned task runs, a schedule
  fires) belong in Reboot's suite, not the app's.

### Who calls

```gherkin
Given "alice" is an authenticated user
And "admin" has the bearer token "secret-admin-token"
And "bob" is an unauthenticated user
When "alice" does a `deposit` with `amount=50` on `Account` of "alice"
Then as "alice", `balance` on the `Account` for "alice" has `balance=50`
```

`is an authenticated user` mints a test token through the path a real
sign-in takes, so the app's `User` for them is auto-constructed.
`has the bearer token` names a raw token the app's own `TokenVerifier`
accepts. A call starts with the user; a read starts with `as "alice",`.
A single unauthenticated caller is `"anonymous"`.
`Given as "alice", a shared context` makes every later call share one
context, like one client session; each must then name the same user.

### Calls, results, saved values

```gherkin
Given "alice" creates an `Account` via `open` with `initial_balance=100`
And the resulting state id is saved as "account id"
When "alice" does a `deposit` with `amount=50` on `Account` of "<account id>"
Then the result has `updated_balance=150`
And the resulting `account_id` is saved as "alice account id"
```

- **`creates`** calls a factory. Leave the id out and save the one it
  makes; give one (`` creates an `Account` of "alice" via `open` ``)
  only when the id means something to the app (a user id, a singleton
  the code refers to, a natural key).
- **`does`** calls a writer, transaction or workflow; the article
  follows English. Request properties follow the method:
  `` with `a=1` and `b="x"` ``.
- **A call does one thing; its result is saved on the next line**:
  `the resulting `field` is saved as "..."`, `the resulting state id`,
  `the resulting task id`. `the result has ...` asserts on the last
  response.
- **A saved name** is quoted and may have spaces; it is said back
  bare as `<name>`: in a state id (`of "<account id>"`), a user id, a
  token, or a property value (`amount=<balance>`). Outline columns are
  said the same way, so a save may not reuse a column's name.
- **Values are JSON** with JSON5 leniencies:
  `owner={name: "Frank", tags: ["vip"]}`. A dotted path nests when
  calling (`owner.name="Frank"`) and reaches into the response when
  asserting (`balances[0].account_id=<ann account id>`,
  `owners["main"].name="Heidi"`).

### Reads, assertions, waiting

```gherkin
Then as "alice", `balance` on the `Account` for "<account id>" has `amount=100.0`
And as "alice", `balances` on the `Customer` for "ann" has `balances` of length `1` and `balances[0].balance=25.0`
And as "anonymous", `all_customer_ids` on the `Bank` for "<bank id>" has `customer_ids` containing `"alice"`
And as "alice", `has_at_least` with `amount=50` on the `Account` for "<account id>" has `enough=true`
Then as "anonymous", `balance` on the `Account` for "<account id>" eventually has `amount=1.0` within 10 seconds
```

A `Then ... has` asserts with `path=value`, `path` containing `value`
(substring, list element or map key), and `path` of length `n`, joined
by `and` or commas. A `Given` / `When ... has` **saves** instead:
`` has `owner.name` saved as "owner name" ``. Readers are read only
this way: `does` and `attempts` refuse a reader, `has` refuses a
writer. Waiting for a task, schedule or workflow is `eventually has
... within N seconds`, a reactive read with a bound, never a sleep.

### Attempts, aborts, tasks

```gherkin
When "alice" attempts a `withdraw` with `amount=50` on `Account` of "<account id>"
Then the attempt aborts with `OverdraftError` with `amount=20`
Then as "anonymous", `balance` on the `Account` for "ghost" aborts with `StateNotConstructed`
When "anonymous" spawns a `deposit` with `amount=15` on `Account` of "<account id>"
And the resulting task id is saved as "first"
Then "anonymous" awaits the `deposit` task "<first>" on `Account` within 30 seconds
And the result has `updated_balance=15`
```

`attempts` makes a call that may abort; a reader's abort is asserted on
the read itself. An uncaught non-Reboot error (a `ValueError`, an index
out of range) aborts with `Unknown`; prefer declaring an error and
asserting that. `spawns` runs a call as a task; a task id a response
carries is saved and awaited the same way.

### Tags: `@wip` and `@blocked`

- **`@wip`** marks the feature, rule or scenario being worked on. It
  runs as usual; the dashboard marks it green and filters by it. Put
  it on a new feature, move it down to rules and scenarios as they are
  added, take it off with the developer's agreement.
- **`@blocked`** marks a scenario the app cannot pass yet, or one that
  needs a person first. The paragraph under its `Scenario:` line says
  why; the scenario is skipped with that reason and marked red.

`rbt dashboard` (the [`dashboard` skill](../../dashboard/SKILL.md))
shows each feature with its rules, scenarios, the methods it exercises,
the methods no feature exercises, these marks, and browser recordings.
Point the developer there to review scenarios.

### Custom steps are plain Reboot code

```python
from bank.v1.account_rbt import Account
from reboot.bdd import parsers, then, when
from reboot.bdd.fixtures import World


@when(
    parsers.parse(
        '"{user}" does {count:d} deposits of {amount:d} on `Account` of '
        '"<{name}>"'
    )
)
async def _makes_deposits(
    world: World,
    user: str,
    name: str,
    count: int,
    amount: int,
) -> None:
    context = world.context(user)
    for _ in range(count):
        await Account.ref(str(world.saved[name])).deposit(
            context,
            amount=amount,
        )
```

- Get the context from `world.context(user)`, spelled the way the
  built-in steps spell callers; use `rbt.create_external_context()`
  only to leave the scenario's identity on purpose.
- Read saved values from `world.saved[name]`; save with
  `world.save('name', value)` (a fixture may too). A recall resolves
  when its step starts, so order steps after the save is certain.
- Deriving one value from another (a substring of a saved id) is a
  custom step: read `world.saved`, compute, `world.save(...)`.
- A step may be `async def`; `reboot.bdd`'s decorators run it on the
  harness loop.

Mocked externals assert through one-line custom steps:

```python
@pytest.fixture(autouse=True)
def send_email() -> Iterator[mock.AsyncMock]:
    with mock.patch('account_servicer.send_email') as mocked:
        yield mocked


@then('the welcome email was sent')
def _the_welcome_email_was_sent(send_email: mock.AsyncMock) -> None:
    # Reboot re-runs methods twice in development mode to validate
    # that they are idempotent, so the email sends twice.
    assert send_email.call_count == 2
```

Model and dependency stand-ins are autouse fixtures, and a module's
scenarios share them, so each stand-in gets its own test module.

## Never

- **`scope_id="<northwind id>"`** — inside quotes a `<name>` is the
  literal text, which reaches the servicer as an id nobody created
  and aborts two steps later. Recall bare: `scope_id=<northwind id>`
  (the state-id position, `of "<id>"`, is the one quoted form).
- **`@then('mentioned "{text}"')` without `parsers.parse(...)`** —
  registers nothing; the scenario later fails "Step definition is not
  found".
- **`eventually has` under `Given` or `When`** — it asserts; put it
  under `Then` (a later `Given` may follow).
- **A `Rule:` with no `Scenario:` under it** — read by the developer
  and the dashboard, run by nothing; it stays green while false.
- **Asserting a remembered constant** (a flat price) — assert what
  the API returns, the way the UI computes it.
- **A scenario counting every call to a stand-in** ("asked 9 times in
  all") — one unrelated change breaks dozens. Count by kind.
- **A stand-in that answers from a counter or a popped list** —
  `at_least_once` runs its callable twice under effect validation and
  keeps the **second** result. Derive the answer from the input; a
  billed or non-deterministic call takes
  `at_least_once(..., effect_validation=EffectValidation.DISABLED)`.
- **Subclassing a servicer to weaken its authorizer** — declare who
  calls with `is an authenticated user`.
- **`World.call` / `World.request` in a custom step** — built-in
  internals; call the generated clients.

## Limits

- **`eventually has` does not wait for an actor to exist.** On one a
  workflow has not created yet, it aborts at once with
  `StateNotConstructed` (reboot-crm, 1.6.0). Write a custom step that
  reads in a loop and treats `StateNotConstructed` as "not yet".
- **No arithmetic or substrings over saved values** in built-in steps;
  use a custom step.
- **`<name>` substitution does not run in custom steps.**
- **The dashboard marks and filters only `@wip` and `@blocked`**; a
  suite's own tags (`@critical`) are invisible there though `-m`
  selects them. To review a tier, add `@wip` beside it, check
  `-m "wip and not critical"` collects nothing, and remove it after.
- **Effect validation runs writer and transaction bodies twice in
  tests**, so a mock called from one sees `call_count == 2`.

## Scales as

- Application bring-up dominates: 26 scenarios took 3.5 minutes,
  mostly starting applications (client-portal, 1.6.0). A browser
  scenario costs about 7× a backend one
  ([`testing-web-app.md`](testing-web-app.md)).

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `Step definition is not found:` | No step matches: a custom step without `parsers.parse`, a typo, or a `When`-only step after `Then` | Wrap in `parsers.parse`; match the built-in spelling and keyword |
| `Almost: a Given or When 'has' saves what it reads now; 'eventually has' asserts, under a Then` | `eventually has` under `Given`/`When` | Move it under `Then` |
| `Almost: a Given or When 'has' saves, e.g. `path` saved as `name`` | An assertion under `Given`/`When` | Assert under `Then` |
| `Almost: say a saved value as <name>, not $name` | `$name` / `${name}` spelling | `<name>` |
| `Almost: each clause goes in backticks` | A `with` / `has` clause without backticks | `` `amount=50` `` |
| `Nothing saved as "...";` | Recall before the save, or a misspelled name | Check the list of saved names it prints |
| `` `OAuth` requires `allowed_origins=[...]` to be set explicitly in production `` | `oauth=` in the fixture without `allowed_origins` | `OAuth(..., allowed_origins=[])` |
| `StateNotConstructed` (from `eventually has`) | The actor does not exist yet | Custom polling step (Limits) |

## See also

- [`testing-web-app.md`](testing-web-app.md) — browser steps and markup
- [`../../feature/SKILL.md`](../../feature/SKILL.md) — agreeing scenarios with the developer
- [`testing-failure-recovery.md`](testing-failure-recovery.md) — the harness-only crash tests
