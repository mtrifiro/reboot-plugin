---
id: reboot-crm-23
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P1.13"
reboot_version: 1.6.0
severity: red
target: framework
names: []
tags: [error-text, cost, negative-space]
cluster: "4.4"
still_applies: unknown
status: Open
resolved_by: ""
---

# A retry against a long-held lock never surfaces to the caller, and PRESUMED_DEADLOCK names a cause it has not established

**What happened.** On 2026-09-23 a `pytest` run and an `rbt dev run` competed for the machine. The demo seed slowed, and from then on every write touching the `Team` singleton raised, retried and raised again: `SystemAborted: aborted with 'TransactionShouldRetry { reason: PRESUMED_DEADLOCK retry_age: ... }': Transaction ... waited longer than 250ms for state 'reboot-team' of type 'crm.v1.Team', which is held by the older transaction ..., and is presumed deadlocked with it; aborting so that the older transaction proceeds. Retry required.` The ids are UUIDv7 and decode to a holder age of 118.6 seconds: a cycle deadlocks at once, this did not, so `PRESUMED_DEADLOCK` on a 250 ms threshold named a cause the runtime had not established and sent the author hunting a loop that was not there (`User.set_name` calls `Team.register`, which awaits nothing). To a person it was a dead button: typing a display name and pressing Continue re-rendered the same screen with no error, spinner, console message or failed request. It could not be told from outside whether the holder was still running (slow seed on a loaded machine) or gone (a participant that died holding an exclusive lock), which want opposite responses.

**Expected.** A retry refused the same lock for, say, thirty seconds should stop and surface to the caller; the message should give the holder's age in seconds and whether it is still alive. Source fix list: (1) bound the retry and abort with state id and holder named; (2) print the holder's age and whether it is running; (3) release the locks of a transaction no longer running, if that is what happened. Source recommends (1) and (2) first.

**Repro.** Run a test suite and `rbt dev run` against the same checkout so the demo seed is starved of CPU, then sign in and set a display name while the seed is still going. Workaround: `rbt dev expunge --yes` and restart.

**Where in the skills.** Not applicable to a skill. Related to student-sor-05 and student-sor-06.
