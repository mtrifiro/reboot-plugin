---
id: reboot-crm-97
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md What worked: a factory transaction that constructs a second actor"
reboot_version: 1.6.0
severity: green
target: positive
names:
  - python/references/state-actor-decomposition.md
  - python/references/api-schema-evolution.md
  - python/references/stdlib-queue.md
tags: [pattern, seeding, testing]
cluster: "E"
still_applies: unknown
status: Open
resolved_by: ""
---

# What worked: a factory transaction that constructs a second actor (and other things that worked)

**What happened.** `Account.create` as `Transaction(factory=True)` constructing an `Intelligence` actor in its constructor branch, itself called from `Pipeline.add_account`'s transaction, worked exactly as `state-actor-decomposition.md` shows, two levels deep, with no special handling; worth stating in the reference that nesting to that depth is fine. Other things that worked: (1) zero-value defaults and `context.constructor` made seeding idempotent and restarts mid-edit (dozens under `--watch`) never duplicated state; (2) `OrderedMap` + `forall` for the per-account timeline was the documented shape and needed no tuning at 47 accounts; (3) `at_least_once` with a memoized `uuid4` key made the chat call safely retryable; (4) the BDD web steps drove the real Vite app cross-origin with cookies and CORS exercised, and three browser scenarios caught two real accessibility bugs (checkbox names, duplicate link names); (5) asserting a reader's refusal with the "attempts ... / the attempt aborts" shape failed with a message naming the right shape verbatim, the whole fix; every harness error should read like that; (6) adding three `UserState` fields on fresh tags and two `User` methods was exactly as `api-schema-evolution.md` promises: no migration, no boot refusal; (7) the stdlib `Queue` did its job with no tuning (a producer line, a consumer loop taking three at a time, two registrations; `dequeue` blocking on empty means an idle list costs nothing); (8) `rbt task list` is the honest view of a fan-out, since the application log lags badly under load; (9) one `Reboot()` application per test file should make a suite parallelisable: splitting scenarios across files that each boot their own harness, then `pytest-xdist -n auto`, took a thirteen-minute suite to 2:09, and marking browser scenarios `browser` makes `-m "not browser"` the dev loop, but the speed did not hold (hangs returned, see P1.10 measured, P1.10c, P1.10d; the suite runs serially again, about thirty minutes), though the split still pays as blast radius. Area: Framework.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.
