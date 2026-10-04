---
id: theater-network-12
project: theater-network
source: "theater-network/docs/reboot-findings.md §12"
reboot_version: 1.4.0
severity: unrated
target: plugin
names:
  - python/references/scheduling-basic.md
tags: [negative-space, cost, error-text]
cluster: "4.1"
still_applies: yes
status: Resolved
resolved_by: "python/references/scheduling-basic.md § Never"
---

# Never schedule two identical-when transactions on one actor (native assert)

**What happened.** A multi-seat hold that scheduled one `expire_hold` task per seat gave the same cart several scheduled transactions with identical `when=timedelta(seconds=45)`. They fired in the same instant, their two-phase-commit prepares collided, and a native assert killed a worker process: `F... database.cc:1374] Check failed: inserted` / `Application exited unexpectedly (with exit status -6)`. Reproduced twice on fresh state at the moment the first batch of holds expired; everything sharing that worker then wedged (writers starve, readers half-work; it looks like lock contention until the log is read). Fix: schedule one task per logical event covering all the work (`expire_hold(seat_labels=[...], hold_generations=[...])`). A five-minute max-speed soak that previously died in about 50s runs clean after the change. General rule: an actor's timers should be few and coarse; fan work out inside the task, not across many simultaneous tasks. Extended by items 18 and 20 (spacing alone is insufficient; do not fan out inside one transaction).

**Expected.** Not recorded.

**Repro.** Several scheduled transactions on one actor with identical `when`, firing together (reproduced twice).

**Where in the skills.** `python/references/scheduling-basic.md` (Never / Errors).

**Checked at 1.6.0.** `scheduling-basic.md` has no warning about identical-`when` schedules or the `database.cc` assert (grep for database.cc / Check failed / identical found nothing in `skills/`).
