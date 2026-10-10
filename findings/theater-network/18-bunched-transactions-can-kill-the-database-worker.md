---
id: theater-network-18
project: theater-network
source: "theater-network/docs/reboot-findings.md §18"
reboot_version: 1.4.0
severity: unrated
target: framework
names:
  - python/references/scheduling-basic.md
  - python/references/scheduling-recurring.md
tags: [negative-space, cost, error-text]
cluster: "D"
still_applies: unknown
status: Resolved
resolved_by: "python/references/scheduling-basic.md § Errors you will see"
---

# Bunched transactions on one actor can kill the database worker

**What happened.** Extends item 12: the `database.cc:1374 Check failed: inserted` assert is not fully avoidable by spacing schedules apart. (a) Retry backoff re-synchronizes tasks scheduled apart (`ExpireHold` tasks that ping out under load back off and then fire together). (b) A restart fires every past-due timer as a simultaneous catch-up, so a backlog of durable timers becomes a crash-loop that only `rbt dev expunge` clears. (c) A transaction that schedules onto N foreign actors builds the colliding shape itself (see item 20). Four occurrences across 2026-08-12/13, plus one previously unseen sibling assert in the degraded aftermath (`database.cc:3706 Check failed: txn.has_value()`). App-level mitigation: never hold any actor's lock across a cross-actor round-trip. Hold expiry became schedule-only end to end (`Cart.expire_hold` only fans out per-seat `Seat.expire` tasks and commits; the seat frees itself, generation-guarded, notes the showing, and schedules `Cart.forget_expired`, guarded by `CartState.hold_generation_by_label`). An 8-timer burst then matures with zero lock timeouts where the transactional version convoyed for 30s per slow seat and twice crashed the worker.

**Expected.** Not recorded.

**Repro.** Evidence and repro tarballs were kept by the source project; contents not reproduced here.

**Where in the skills.** Framework bug (file upstream); the app-level mitigation belongs in `scheduling-basic.md` Never/Scales as.

**Checked at 1.6.0.** Not checked against 1.6.0 runtime. `python/references/scheduling-recurring.md:204` covers catch-up after downtime firing once but not the multi-timer crash-loop.

**Resolution (2026-10-10).** The `database.cc:1374` row in `scheduling-basic.md` now names a restart firing every past-due timer at once and the schedule-only timer shape; § Limits says undeclared exceptions in scheduled methods retry with backoff.
