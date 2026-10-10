---
title: "Flywheel fixes from the Primer V4 review"
summary: "Who may call a method is now a Design change, and the review table's example row matches the primer."
kind: report
audience: maintainer
---

# Flywheel fixes from the Primer V4 review

## Context

Reviewing the Reboot Primer V4 revision (2026-10-10) against the
Flywheel work in this branch turned up two places where the skills and
the book disagreed. The book was right in both; these fixes bring the
skills in line. They ride with PR 6 (`Skills: the Reboot Flywheel`) in
[`upstream-submission.md`](upstream-submission.md).

## 1. Who may call a method is a Design change

**What was wrong.** The design the user accepts includes who may call
each method: it is a column of the review table, and the primer's
Chapter 6 makes it part of acceptance. But authorizers are code in
`backend/`, and the routing rule sent all code to Prove. A fix that let
any signed-in guest call `approve_refund` passed as a code fix, with no
acceptance, and `scripts/model_diff.py` did not see it.

**What changed.**

- `scripts/model_diff.py` (all three templates) reads every servicer's
  `authorizer()` under `backend/` (not the generated `backend/api/`) at
  both revisions and reports, as Design:
  - an authorizer added or removed (removed means the generated
    default applies);
  - with `<Type>.Authorizer(method=...)`, each method whose rule
    changed (`who may call \`Room.book\` changed`);
  - otherwise, the servicer whose rule changed.

  A rule is compared by its syntax tree, so comments and docstrings
  don't count, and the module-level checks it calls (a shared
  `is_manager`) are followed across the backend, so changing one
  counts against every authorizer that uses it. The report has a new
  "Who may call" section between the domain model and the feature
  files.
- `tests/model_diff_test.py`: two new tests, one for authorizer
  changes (per method, whole servicer, a helper, a comment that must
  not count, a body change that must not count) and one that the
  generated `backend/api/` is not read.
- `build/references/flywheel.md`: the routing table gains the
  authorizer row ("Other code" stays in Prove), a paragraph says every
  authorizer change is listed as Design, including one that only
  carries out the accepted column, and the Never and Limits lists name
  it.
- `build/references/evidence.md`: the PR body's "Domain model" section
  carries the who-may-call lines.
- `build/SKILL.md`, Update Flow step 5: authorizers follow the accepted
  "Who may call"; one the design didn't name goes back to the gate.
- `feature/SKILL.md`, the fix sub-flow: a fix that changes who may call
  a method is a design change.
- `hooks-handlers/remind.sh`, `README.md`, `build/templates/README.md`:
  the one-line routing summaries name authorizers.

**Limits.** An authorizer assigned rather than defined as a method, or
a rule built at import time, is not seen; `flywheel.md` says so.

## 2. The review table's example row

**What was wrong.** The example in `build/SKILL.md`, "Accept the
Design", showed `Room.book` callable by a "signed-in guest". The
primer's Chapter 6 uses the same row to teach the opposite: a guest's
browser has no reason to call `Room.book`, which only
`Reservation.create` reaches (`is_app_internal`). An agent copying the
example would have proposed the looser rule.

**What changed.** The row's "Who may call" reads "the app itself (from
`Reservation.create`)".

## Verification

- `tools/check-all.sh`: exit 0 (the README budget table and two
  generated regions refreshed).
- `tests/model_diff_test.py` in the web-app template: 6 tests pass; the
  file is identical in `both/` and `mcp-ui/`.
- `SMOKE_FULL=1 tools/templates-smoke.sh`: all three templates pass
  (mypy clean, 9 tests each).

## The primer depends on this shipping

The primer now says these behaviors exist "today" (Foreword, Ch1, Ch6,
Ch7, Ch9, Glossary, Diagram 02). None of the Flywheel work is released:
it is uncommitted on `ia-restructure`, and the upstream submission is
on hold. The primer carries a `[NEED: the Reboot skills release ...]`
placeholder in the Foreword, Ch1 and Ch9 until a release ships the
checkpoint, the model diff and the deploy ledger; fill it with that
version, or turn the "today" passages back to "proposed".

Primer edits made with these fixes, for the writer's record:

- **Ch1, Ch6, Ch7, Glossary:** who may call a method is in the routing
  rule's Design list and in the model diff.
- **Ch7, Glossary:** a feature description change is Design; `@wip`
  comes off only with the developer's agreement.
- **Ch1:186:** the deploy warns on a test run with uncommitted changes
  and refuses to deploy uncommitted changes.
- **Ch1's domain model table:** it lists `expire` and `approve_refund`,
  which Ch6's review table uses.
- **Ch1:47:** the model diff and the release record are in the list of
  today's evidence.

Still open in the primer: the Foreword is unsigned, and its
`[NEED: feedback channel]` placeholder needs filling.
