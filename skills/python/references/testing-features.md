---
title: Specify Behavior in Feature Files
impact: MEDIUM
impactDescription: Feature files are the application's specification and its test suite at once; a suite written any other way is neither reviewable by the developer nor shown by the dashboard
tags: testing, bdd, gherkin, feature, scenario, rule, pytest-bdd, reboot.bdd, wip, blocked, custom-steps, world, race, red-first
summary: "Built-in steps match their exact spelling; who calls, `creates` / `does`, saved values, `eventually`, aborts, `@wip`, custom steps."
step: tests
applies: [mcp-ui, web-app, backend-only]
always: false
verified: 1.6.0
docs: ""
---

# Specify Behavior in Feature Files

## When you are here

Tests are Gherkin `.feature` files run by `reboot.bdd`, whose built-in
steps cover every call; each file is the developer's spec, the `pytest`
suite (via the `Reboot()` harness) and the dashboard's Features page.
Custom steps only for what built-ins can't say. Browser steps:
[`testing-web-app.md`](testing-web-app.md); crash tests (harness only):
[`testing-failure-recovery.md`](testing-failure-recovery.md); agreeing
scenarios: [`feature` skill](../../feature/SKILL.md). Every pattern here
is in [`reboot-bank-pydantic`](https://github.com/reboot-dev/reboot-bank-pydantic)
`tests/`.

## Do this

### Layout and the test module

```
pytest.ini                     # testpaths: tests; pythonpath: backend/src backend/api api
tests/
├── opening_accounts.feature   # One feature per capability.
├── full_bank_test.py          # One module per application setup.
├── interest_test.py
├── web_test.py                # The scenarios that drive the web app.
└── opening_accounts.recordings/   # Made by running; git-ignored.
```

Name a `.feature` for the activity, not a state type. A test module is
one application configuration: an `application` fixture plus
`scenarios(...)` naming its features.

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
        # Only if the app has `oauth=`; the harness needs the explicit
        # empty list (browser variant: testing-web-app.md).
        oauth=OAuth(provider=..., allowed_origins=[]),
    )


scenarios('deposits.feature', 'withdrawals.feature')
```

- `reboot[dev]` registers the built-in steps as a pytest plugin; don't
  import them ([`testing-project-setup.md`](testing-project-setup.md)).
- `Given the "proxy" application is up` runs a `proxy_application`
  fixture's return.
- Run `uv run pytest`, or narrow: `uv run pytest tests/full_bank_test.py`,
  `-k "transfer between two"`, `-m wip`, `-m "not wip"`.

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

- **Feature**: one thing a user can do, named as a sentence, with a
  purpose paragraph.
- **Rule**: a business invariant (money is conserved, a balance never
  goes below zero), stated once in name and description. A scenario
  that only shows an operation sits at top level.
- **Scenario**: one concrete example named for the situation, never
  restating the rule; `Scenario Outline` + `Examples` for several values.
- **Background**: what every scenario starts from; no user only some
  scenarios use.
- Don't test Reboot's own mechanisms (a task runs, a schedule fires).

### Who calls

```gherkin
Given "alice" is an authenticated user
And "admin" has the bearer token "secret-admin-token"
And "bob" is an unauthenticated user
```

- `is an authenticated user` mints a token via the real sign-in path,
  auto-constructing the app's `User`.
- `has the bearer token`: a raw token the app's `TokenVerifier` accepts.
- Calls start with the user; reads with `as "alice",`. A lone
  unauthenticated caller is `"anonymous"`.
- `Given as "alice", a shared context`: later calls share one context
  (one client session) and must name the same user.

### Calls, results, saved values

The transfer scenario above shows the shapes:

- **`creates`** calls a factory. Omit the id and save the generated one;
  give one (`` creates an `Account` of "alice" via `open` ``) only when
  it means something (a user id, a singleton the code names, a natural
  key).
- **`does`** calls a writer, transaction or workflow (article follows
  English); properties: `` with `a=1` and `b="x"` ``.
- **One call per step; save on the next line**:
  `the resulting `field` is saved as "..."`, `the resulting state id`,
  `the resulting task id`. `the result has ...` asserts on
  the last response.
- **Saved names** are quoted (spaces allowed), recalled bare as
  `<name>`: in a state id (`of "<account id>"`), user id, token, or
  value (`amount=<balance>`). Outline columns recall the same way, so a
  save may not reuse a column name.
- **Values are JSON5**: `owner={name: "Frank", tags: ["vip"]}`. Dotted
  paths nest in calls (`owner.name="Frank"`) and reach into responses
  in assertions (`balances[0].account_id=<ann account id>`,
  `owners["main"].name="Heidi"`).

### Reads, assertions, waiting

```gherkin
Then as "alice", `balances` on the `Customer` for "ann" has `balances` of length `1` and `balances[0].balance=25.0`
And as "anonymous", `all_customer_ids` on the `Bank` for "<bank id>" has `customer_ids` containing `"alice"`
And as "alice", `has_at_least` with `amount=50` on the `Account` for "<account id>" has `enough=true`
Then as "anonymous", `balance` on the `Account` for "<account id>" eventually has `amount=1.0` within 10 seconds
```

- `Then ... has` asserts `path=value`, `path` containing `value`
  (substring, list element, map key) or `path` of length `n`, joined by
  `and` or commas.
- `Given` / `When ... has` **saves**: `` has `owner.name` saved as "owner name" ``.
- `does` / `attempts` refuse a reader; `has` refuses a writer.
- Wait on a task, schedule or workflow with `eventually has ... within
  N seconds` (bounded reactive read), never a sleep.

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

- `attempts`: a call that may abort; a reader's abort is asserted on the
  read.
- An uncaught non-Reboot error (`ValueError`, index out of range) aborts
  with `Unknown`; declare an error and assert that instead.
- `spawns` runs a call as a task; a task id from a response is saved
  and awaited the same way.

### Tags: `@wip` and `@blocked`

- **`@wip`**: work in progress; runs normally, dashboard marks it green
  and filters by it. Start on the feature, move down to rules and
  scenarios as added, remove with the developer's agreement.
- **`@blocked`**: can't pass yet, or needs a person first. The paragraph
  under `Scenario:` says why; skipped with that reason, marked red.

`rbt dashboard` ([`dashboard` skill](../../dashboard/SKILL.md)) shows
each feature's rules, scenarios, exercised methods, unexercised methods,
these marks and browser recordings; send the developer there to review.

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

- Context: `world.context(user)`; `rbt.create_external_context()` only
  to leave the scenario's identity on purpose.
- Read `world.saved[name]`; save `world.save('name', value)` (fixtures
  too). A recall resolves when its step starts, so order it after a
  certain save. Derived values (a substring of a saved id): read
  `world.saved`, compute, `world.save(...)`.
- `async def` steps run on the harness loop.
- No `<name>` substitution in custom steps.

Mocked externals assert through one-line custom steps:

```python
@pytest.fixture(autouse=True)
def send_email() -> Iterator[mock.AsyncMock]:
    with mock.patch('account_servicer.send_email') as mocked:
        yield mocked


@then('the welcome email was sent')
def _the_welcome_email_was_sent(send_email: mock.AsyncMock) -> None:
    # Effect validation runs the method twice in tests (Limits).
    assert send_email.call_count == 2
```

Stand-ins are autouse fixtures shared module-wide, so each gets its own
test module.

### Races and outside services: a deterministic window

A scenario about a race or an outside service must fail red before the
fix and pass after it every run, so the window it names has to be made,
not waited for:

- **Script the service.** A stand-in that holds its answer until a step
  releases it, or hangs on demand, reaches "disconnect while a connect
  is under way" and "one mailbox never answers" on every run.
- **Answer from the arguments.** A patched seam that counts calls or
  pops a list breaks under effect validation, which replays it (see
  Never).
- **Can't be made to fail?** Say so to the developer rather than
  writing a scenario that passes either way.

## Never

- **`scope_id="<northwind id>"`** — quoted `<name>` is literal text: an
  id nobody created, aborting two steps later. Recall bare,
  `scope_id=<northwind id>`; only the state id, `of "<id>"`, is quoted.
- **`@then('mentioned "{text}"')` without `parsers.parse(...)`** —
  registers nothing; the scenario fails "Step definition is not found".
- **`eventually has` under `Given` or `When`** — it asserts; put it
  under `Then` (a later `Given` may follow).
- **A `Rule:` with no `Scenario:` under it** — runs nothing; green while false.
- **Asserting a remembered constant** (a flat price) — assert what the
  API returns, the way the UI computes it.
- **A scenario counting every call to a stand-in** ("asked 9 times in
  all") — one unrelated change breaks dozens. Count by kind.
- **A stand-in that answers from a counter or a popped list** —
  `at_least_once` runs it twice under effect validation and keeps the
  **second** result. Derive the answer from the input; a billed or
  non-deterministic call takes
  `at_least_once(..., effect_validation=EffectValidation.DISABLED)`.
- **Subclassing a servicer to weaken its authorizer** — declare who
  calls with `is an authenticated user`.
- **`World.call` / `World.request` in a custom step** — built-in
  internals; call the generated clients.

## Limits

- **`eventually has` doesn't wait for an actor to exist**; one a
  workflow hasn't created yet aborts at once with `StateNotConstructed`
  (reboot-crm, 1.6.0). Use a custom step that loops, treating
  `StateNotConstructed` as "not yet".
- **No arithmetic or substrings over saved values** in built-in steps;
  use a custom step.
- **The dashboard marks and filters only `@wip` and `@blocked`**, not
  custom tags (`@critical`), though `-m` selects them. To review a tier,
  add `@wip` beside it, check `-m "wip and not critical"` collects
  nothing, remove it after.
- **Effect validation runs writer and transaction bodies twice in
  tests** (idempotency check), so a mock called from one sees
  `call_count == 2`.

## Scales as

- Application bring-up dominates: 26 scenarios took 3.5 minutes
  (client-portal, 1.6.0). A browser
  scenario costs about 7× a backend one
  ([`testing-web-app.md`](testing-web-app.md)).

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `Step definition is not found:` | No step matches: a custom step without `parsers.parse`, a typo, or a `When`-only step (`saves the text of`, `clicks`, `fills`) after `Then` | Wrap in `parsers.parse`; match the built-in spelling and keyword |
| `Almost: a Given or When 'has' saves what it reads now; 'eventually has' asserts, under a Then` | `eventually has` under `Given`/`When` | Move it under `Then` |
| `Almost: a Given or When 'has' saves, e.g. `path` saved as `name`` | An assertion under `Given`/`When` | Assert under `Then` |
| `Almost: say a saved value as <name>, not $name` | `$name` / `${name}` spelling | `<name>` |
| `Almost: each clause goes in backticks` | A `with` / `has` clause without backticks | `` `amount=50` `` |
| `Nothing saved as "...";` | Recall before the save, or a misspelled name | Check the list of saved names it prints |
| `StateNotConstructed` (from `eventually has`) | The actor does not exist yet | Custom polling step (Limits) |

## See also

- [`testing-web-app.md`](testing-web-app.md) — browser steps and markup
- [`../../feature/SKILL.md`](../../feature/SKILL.md) — agreeing scenarios with the developer
- [`testing-failure-recovery.md`](testing-failure-recovery.md) — the harness-only crash tests
