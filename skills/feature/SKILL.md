---
name: feature
description: Specify a Reboot application's feature before and while building it, as a Gherkin `.feature` file the tests run and the dashboard shows. Use whenever the user asks for a new capability or a change to one ("add transfers", "users should be able to..."), before touching the API or code; and when converting an existing test suite to feature files. Agrees on the feature in plain English first, writes it down tagged `@wip`, builds it with the `python` / `web-app` / `mcp-ui` skills, then iterates on scenarios with the user until they agree to take the tag off.
argument-hint: [<feature-description>]
allowed-tools: Bash, Read, Write, Glob, Grep, Edit, AskUserQuestion
---

# feature — Specify a Feature, Then Build It

> **Version notices:** if `rbt` reports a version mismatch or a newer
> Reboot, follow the [upgrade skill](../upgrade/SKILL.md).

A feature is one `.feature` file in `tests/`: the spec the developer
reviews, the tests `pytest` runs, and the card on the dashboard's
Features page. Order of work: agree in English, write it down before
code, tag the unfinished `@wip`, untag only when the developer says so.

References (in the `python` skill), each at the step that needs it:

- `../python/references/testing-features.md` — **before writing any
  scenario**: step vocabulary, who calls, saved values, assertions,
  `@wip` / `@blocked`, custom steps.
- `../python/references/testing-web-app.md` — when a scenario opens the
  web app: the `frontend` fixture, web app steps, accessible markup,
  recordings.
- `../python/references/testing-project-setup.md` — the files a suite
  needs (`reboot[dev]`, `pytest.ini`, `.gitignore`).
- `../python/references/lifecycle-seeding.md` — only when fixtures load
  seed data; `../python/references/lifecycle-dev-loop.md` — when a run
  goes quiet or passes alone and fails in the suite.

## Step 1 — Propose the feature in English

Before any file changes, describe the feature as a person would, not as
an API:

- **Name**: a sentence about the activity ("Customers can transfer
  money between accounts").
- **Purpose**: a short paragraph — who does it, why, what they see
  when it worked.
- **Rules**: only clear business rules or system-wide invariants worth
  formal verification (money is conserved by a transfer; a balance
  never goes below zero; a customer sees only their own accounts). Most
  features have one or two, many none; "the button works" is not a rule.
- **Example situations**, one prose line each ("a transfer between two
  customers' accounts"; "a transfer for more than the source holds").
- **Web app involvement**, when the app has one: the click-through
  flow, if that is how the feature is used.

Ask whether that is the feature; iterate on the English until they
agree — the file follows the words.

## Step 2 — Write it down, tagged `@wip`

Create `tests/<capability>.feature`, named for the activity
(`transfers.feature`, not `bank.feature`), with the agreed name,
description and rules (with descriptions). Write it even with no
scenarios yet, `@wip` on the whole feature:

```gherkin
@wip
Feature: Customers can transfer money between accounts
  A customer moves money from one of their accounts to another
  account of the bank in one step, which is how they pay someone
  without a withdrawal and a deposit that could come apart.

  Background:
    Given the application is up

  Rule: A transfer moves exactly the amount from one account to the other
    Neither account sees any other change.

  Rule: A transfer that would overdraw the source leaves both accounts unchanged
    A transfer is one transaction: when the withdrawal from the source
    account aborts, the deposit into the destination is rolled back
    too, so money is never created by a failed transfer.
```

- Add the file to the `scenarios(...)` call of the test module for its
  application, or create the module (minimal one in
  `testing-features.md`).
- No test suite yet: set one up per `testing-project-setup.md`
  (`reboot[dev]` in dev dependencies, `*.recordings/` in `.gitignore`).
- Scenarios needing data: seed the minimum each needs, per test, not the
  production catalog — call the seed function `initialize` calls with
  less data, through an app-internal context, constructing what
  production's `initialize` constructs
  ([`lifecycle-seeding.md`](../python/references/lifecycle-seeding.md)).
- If the dashboard is running (the `dashboard` skill), the feature
  appears on its Features page at once as work in progress; tell the
  user.

## Step 3 — Build the feature

Change the API, servicers and frontend by the
[`build` skill](../build/SKILL.md)'s flow with your front-door skill
(`web-app` or `mcp-ui`), or the `python` skill for backend-only work.
Two rules matter most:

- **Every property gets a `description=`** on its `Field(...)` saying
  what the value means (`api-pydantic.md`); the dashboard shows it
  beside the property, or a request to add it.
- **Build web app pages with accessible markup** from the start
  (`testing-web-app.md`): labels paired with inputs, buttons that say
  what they do, tables with a labeled heading — that is what lets a
  scenario drive the page.

## Step 4 — Iterate on the scenarios with the user

After the API and code change, turn the example situations into
scenarios and run them; then loop with the user: show each scenario,
ask what else the feature must do, write it, run it.

- **Write scenarios in the built-in steps** (`testing-features.md`),
  named for the situation, under the rule it illustrates, else at the
  feature's top level.
- **Let a factory make the id up**: `` "alice" creates an `Account` via
  `open` ``, then `the resulting state id is saved as "account id"`, then
  `<account id>`. Give an id only when it means something to the
  application (a user id, a singleton the code refers to).
- **Recall a saved value bare**: `scope_id=<account id>` passes the
  saved value; `scope_id="<account id>"` passes the literal text
  `<account id>` and fails elsewhere, usually as `StateNotConstructed`.
- **Give every rule at least one scenario**: a `Rule:` with no
  `Scenario:` is checked by nothing, so it stays green while false.
- **Move `@wip` down as scenarios land**: put `@wip` on each written
  rule or scenario and take it off the feature, so the dashboard shows
  exactly what is in progress.
- **Tag `@blocked` what cannot pass yet**: a declared error the app
  does not raise yet, or a scenario needing a person to act first (a
  credential, a decision, an external system). The paragraph under the
  `Scenario:` line says why; it is the skip reason the dashboard shows.
  Never delete or weaken a scenario to make the suite green.
- **Suggest a web app scenario** when the feature is something a person
  does in the app: the clicks and what they see, plus backend
  assertions on the resulting state (`testing-web-app.md`). Running it
  records a video and screenshots viewable on the Features page.
- **Suggest a rule only for a real invariant** worth formal
  verification; a scenario that only shows what an operation does stays
  at the top level.
- **Run the suite** (`uv run pytest`, or `-m wip` for in-progress) and
  `uv run mypy backend/ tests/`; fix what fails.
- **Suggest a dashboard review** after each round: the feature's card,
  its rules, the methods it uses and those no feature uses, the
  recordings.

## Step 5 — Ask before taking `@wip` off

When every scenario passes (or is `@blocked` with a reason) and the
user says the feature does what they meant, ask whether to remove the
`@wip` tags; remove them only with agreement. `@blocked` stays until
the blocking is resolved.

## Converting an existing test suite

When `unittest` / `IsolatedAsyncioTestCase` tests (the pre-feature-file
layout) should become feature files — the user asks, or the `upgrade`
skill's migration notes say so:

1. Read every test; list what each shows, one English line per test.
2. **Group into features by capability**, not servicer or test file: a
   `test_bank.py` with deposits, withdrawals and transfers becomes
   `deposits.feature`, `withdrawals.feature`, `transfers.feature`. When
   the grouping is unclear, propose one and ask; never guess a business
   rule they did not state.
3. Do steps 1 and 2 per feature, then write scenarios from the tests'
   calls and assertions in the built-in steps. A helper the steps can't
   express becomes a custom step in plain Reboot code
   (`testing-features.md`); a mock becomes an autouse fixture asserted
   through a one-line custom step.
4. Keep tests not about application behavior: the crash-and-recover
   tests of `testing-failure-recovery.md` stay on the harness.
5. Run both until the scenarios cover the tests, then delete the
   converted tests. Leave every feature `@wip` until the user has
   reviewed the files, then ask to remove the tags.
