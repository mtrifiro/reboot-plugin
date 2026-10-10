---
name: feature
description: Specify a Reboot application's capability as a Gherkin `.feature` file the tests run and the dashboard shows, before and while building it. Use whenever the user asks for a new capability or a change ("add transfers", "users should be able to..."), for a fix ("fix this", "fix all 4", a bug report, a review finding) before touching the API or code, and to convert an existing test suite. Agrees on the feature in plain English, writes it tagged `@wip`, runs each scenario red, builds it, then iterates on scenarios with the user until they agree to take the tag off.
argument-hint: [<feature-description>]
allowed-tools: Bash, Read, Write, Glob, Grep, Edit, AskUserQuestion
---

# feature — Specify a Feature, Then Build It

> **Version notices:** if `rbt` reports a version mismatch or a newer
> Reboot, follow the [upgrade skill](../upgrade/SKILL.md).

A feature is one `.feature` file in `tests/`: the spec the developer
reviews, the tests `pytest` runs, and the card on the dashboard's
Features page. Order of work: agree in English, write the scenario
down, see it fail, then write the code; tag the unfinished `@wip`,
untag only when the developer says so. A fix is a change: it follows
the same order.

In the **Reboot Flywheel**
([`build/references/flywheel.md`](../build/references/flywheel.md)),
Steps 1–2 are Design: the rules and scenarios the user accepts with the
domain model. Steps 2a–5 are Prove.

**A fix, a bug report or a review finding** starts at
[A fix, a bug report, a review finding](#a-fix-a-bug-report-a-review-finding),
not Step 1.

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
agree — the file follows the words. In a build, this agreement feeds
the build's "Accept the Design", where the user accepts the rules,
their scenarios and the domain model together, before any
implementation.

## Step 2 — Write it down, tagged `@wip`

Create `tests/<capability>.feature`, named for the activity
(`transfers.feature`, not `bank.feature`), with the agreed name,
description and rules (with descriptions), `@wip` on the whole
feature. Then write one scenario for each example situation from
Step 1, under the rule it illustrates (else at the feature's top
level), in the built-in steps (Step 4's bullets say how; the
transfer scenario in `testing-features.md` is a whole one). The
feature, before its scenarios:

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

## Step 2a — See each scenario fail before writing the code

Run the new scenarios against the code as it is
(`uv run pytest -m wip`, or `-k "<scenario name>"` for one), before
changing behavior, and check that each fails for the reason the scenario names:
the wrong value, the missing touch, the number that moved too far.
A failure for any other reason (a step not found, a field the response
lacks, a fixture that never started) proves nothing; fix the scenario
until the failure is the behavior's.

- **A new field the scenario reads may come first.** Add only the
  field (additive, with a zero default) and regenerate, so the run
  fails on its value rather than on its absence; no behavior yet.
- **A new method may come first, too.** For a capability that does not
  exist yet, declare the method in the API and regenerate, and leave
  its servicer body raising `NotImplementedError`: the run reaches the
  method and fails there, the failure the feature's absence should
  give. Write no behavior yet.
- **A scenario that passes before the fix is the wrong scenario.** It
  does not test the change; rewrite it before going on.
- **Races and outside services:** make the window deterministic, by
  `testing-features.md` (*Races and outside services*). If a case
  cannot be made to fail, say so to the user rather than writing a
  scenario that passes either way.
- **Red is expected here.** A failing `@wip` scenario shows red on the
  dashboard's Features page; tell the user that is the point of this
  step, not a broken suite.
- **Report it:** tell the user which scenarios failed, and why, before
  building.

### A fix, a bug report, a review finding

"Fix this", "fix all 4" or a list of review findings is a request to
change behavior, not permission to skip the feature. For each:

1. Say in one line what the app does now and what it should do.
2. Write that as a scenario under the rule it breaks (or a new rule),
   tagged `@wip`, in the feature that owns the behavior.
3. Route it ([`flywheel.md`](../build/references/flywheel.md), "The
   routing rule"; `python3 scripts/model_diff.py HEAD` sorts it). A new
   scenario under an existing rule is a code fix: it stays in Prove. A
   new or reworded rule, a changed scenario, or a fix that needs an API
   change or changes who may call a method (an `authorizer()`) is a
   design change: show the model diff and take it through
   the build's "Accept the Design" before any code.
4. Show the user the scenarios, and run them red (Step 2a), before
   any code. Approval of the fix ("go", "fix all 4") is not agreement
   on the scenarios: show them first.
5. Fix, run them green, and ask before taking `@wip` off (Step 5).

Only a change with no behavior a scenario could see (a typo in a
comment, a rename inside one function) skips this, and you say so.

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

Scenarios are written before the code (Steps 2 and 2a); this step is
the loop that follows. After each change, run them; then loop with the
user: show each scenario, ask what else the feature must do, write it,
see it fail, then make it pass.

- **Write scenarios in the built-in steps** (`testing-features.md`),
  named for the situation, under the rule it illustrates, else at the
  feature's top level.
- **Ids and saved values** as `testing-features.md` says: let a factory
  make the id up (`the resulting state id is saved as "account id"`),
  give one only when it means something to the application, and recall
  a saved value bare (`<account id>`, never quoted).
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

When `unittest` / `IsolatedAsyncioTestCase` tests should become feature
files (the user asks, or the `upgrade` skill's migration note says so),
follow the steps in
[`upgrade/migrations/1.6.0/feature-files.md`](../upgrade/migrations/1.6.0/feature-files.md):
one English line per test, features grouped by capability (never a
business rule the user did not state; ask), scenarios in the built-in
steps with helpers as custom steps, the crash-and-recover tests kept on
the harness, both suites run until the scenarios cover the tests, then
the converted tests deleted and every feature left `@wip` until the user
has reviewed the files.
