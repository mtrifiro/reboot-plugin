---
id: cineloop-42
project: cineloop
source: "cineloop/reboot-findings.md §32 (Part 4)"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/patterns-idempotency.md
  - python/references/testing-external-context.md
tags: [testing, error-text, negative-space]
cluster: "4.1"
still_applies: yes
status: Open
resolved_by: ""
---

# Asserting a denial poisons the context; asserting a declared error does not

**What happened.** A test asserting three authorization denials in a row failed on the second one with `IdempotencyUncertainError: Because we don't know if the mutation from calling 'AdminMethods.ResetShowing' failed or succeeded AND you've made some NON-IDEMPOTENT mutations we can't reliably determine whether the call to 'AdminMethods.ResetAll' is due to a retry...`. `patterns-idempotency.md` says asserting a declared error is safe while anything else (transport failure, cancellation, undeclared error) leaves the client unable to tell and marks the context uncertain. `PermissionDenied` is a framework error, not one declared in `errors=[...]`, so the context is marked uncertain and the next bare mutation from that context is refused. Seat-level tests never hit it because they assert declared errors (`SeatUnavailableError`, `CartLimitError`). Fix: one alias per denial (`await Admin.ref(ADMIN_ID).idempotently("patron tries to reset the chain").reset_all(self.alice)`).

**Expected.** Add to `patterns-idempotency.md`: negative authorization tests are the common trigger; give each denied mutation its own `.idempotently("...")` alias or use a fresh context per assertion. Asserting a declared error is free; asserting a denial costs an alias.

**Repro.** Two or more denied-mutation assertions from one context.

**Where in the skills.** `python/references/patterns-idempotency.md` 'Uncertain Mutations'.

**Checked at 1.6.0.** `python/references/patterns-idempotency.md` lines 76-88 describe `IdempotencyUncertainError` generally; no mention of authorization-denial tests as a trigger or the alias-per-denial fix (grep for denial found nothing there).
