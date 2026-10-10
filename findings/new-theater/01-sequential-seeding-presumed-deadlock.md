---
id: new-theater-01
project: new-theater
source: "new-theater/FINDINGS.md § Framework, item 1"
reboot_version: 1.6.0
severity: yellow
target: framework
names: []
tags: [cost, seeding, error-text]
cluster: ""
still_applies: unknown
status: Resolved
resolved_by: "python/references/lifecycle-seeding.md § Errors you will see"
---
# Sequential seeding transactions each log a presumed deadlock, then succeed on retry

**What happened.** Under `rbt dev run` (effect validation `quiet`), every sequential seeding transaction from `initialize` (`Chain.add_cinema`, `Screen.schedule_showtimes`) logs `waited longer than 250ms for state ... held by the older transaction ... presumed deadlocked` plus a `Future exception was never retrieved` / `SystemAborted` traceback, then succeeds on retry. Calls are strictly sequential (one `await` at a time), so the "older transaction" looks like the same call's previous run. Cost: ~2.5 s per seeding transaction; 30 cinemas + 240 screen-days took ~25 minutes, and the log is mostly tracebacks.

**Expected.** Sequential transactions from `initialize` do not contend with each other, or the log says what the older transaction is.

**Repro.** Seed from `initialize` with one awaited transaction at a time (`Chain.add_cinema`, then `Screen.schedule_showtimes` per screen-day) under `rbt dev run`.

**Where in the skills.** Not applicable to a skill. Related to reboot-crm-23 (`PRESUMED_DEADLOCK` names a cause it has not established).

**Resolution (2026-10-10).** The presumed-deadlock row in `lifecycle-seeding.md` now says sequential `initialize` transactions trip it too at 1.6.0, about 2.5 s each, and to seed through bulk methods.
