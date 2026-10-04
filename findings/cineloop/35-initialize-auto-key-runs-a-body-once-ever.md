---
id: cineloop-35
project: cineloop
source: "cineloop/reboot-findings.md §25 (Part 4)"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/lifecycle-initialize-hook.md
tags: [seeding, negative-space]
cluster: "C"
still_applies: yes
status: Open
resolved_by: ""
---

# initialize's auto idempotency key runs a body once EVER, not once per boot (migrations)

**What happened.** Cost the most debugging time of anything in the project. `lifecycle-initialize-hook.md` says `initialize` auto-generates an idempotency key per `(actor, method)` so calls 'run once'. The source read that as once per boot; it means once, ever: the key is persisted, so every later boot returns the cached result and never executes the body. For seeding that is right; for a migration it is a trap: if the first execution was a no-op (ran before the data existed, or against a half-deployed build) the migration is permanently marked done. A ledger backfill ran once, did nothing, and silently never ran again: no error, no log, no execution at all; several rounds went on checking the guard clause, the fan-out and authorizers before realising the body was never entered. Fix: name the key (`await Admin.ref(ADMIN_ID).idempotently("ledger-backfill-v2").backfill(context)`); bumping the suffix re-runs it; the method's own guard (`if self.state.sale_count > 0: return`) makes re-running safe. Also: put a log line in any migration ('48 showings scanned, 11 prior sales found').

**Expected.** Add 'Seeding vs. migration' to `lifecycle-initialize-hook.md`: the auto key is derived from `(actor, method)` and persisted, so a bare call executes once in the lifetime of the application; give migrations an explicit versioned alias and make the method idempotent; the alias decides whether the body runs, the guard decides what it does. Symptom to recognise: a method in `initialize` that produces no effect, no error and no log is not failing, it is not being called.

**Repro.** Backfill method called bare from `initialize`; first run is a no-op.

**Where in the skills.** `python/references/lifecycle-initialize-hook.md`; proposal task C (`lifecycle-seeding.md`).

**Checked at 1.6.0.** `python/references/lifecycle-initialize-hook.md` lines 11-12 still say calls get an auto key 'and run once' with no 'once ever / persisted' clarification and no migration guidance.
