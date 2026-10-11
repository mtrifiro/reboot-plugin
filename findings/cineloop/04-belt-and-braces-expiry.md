---
id: cineloop-04
project: cineloop
source: "cineloop/reboot-findings.md §4 (Part 1)"
reboot_version: 1.4.1
severity: unrated
target: positive
names:
  - python/references/scheduling-basic.md
  - python/references/scheduling-recurring.md
tags: [pattern]
cluster: "E"
still_applies: unknown
status: Open
resolved_by: ""
---

# Belt-and-braces expiry: schedule for liveness, compute for truth

**What happened.** The 2-minute hold uses two mechanisms. `self.ref().schedule(when=timedelta(...)).sweep()` makes other viewers see the release without touching anything and is durable across restarts, but fires 'at or after' and cannot be the sole source of truth. A lazy `_reap(now)` at the top of every read and write keeps correctness independent of the scheduler, but is invisible to other viewers. `sweep` is idempotent and self-terminating: it releases whatever has lapsed, then re-schedules only if some hold is still outstanding. Overlapping sweeps (one per hold burst) are harmless and the chain ends by itself when the auditorium goes quiet; simpler than keeping exactly one timer alive.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Positive pattern; kept as a candidate for a `patterns-*` reference (proposal task E). Note theater-network-12/18 found multiple simultaneous schedules on one actor can crash the dev database worker; this design schedules a sweep per hold burst.
