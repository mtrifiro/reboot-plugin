---
id: cineloop-24
project: cineloop
source: "cineloop/reboot-findings.md §15 (Part 3)"
reboot_version: 1.4.1
severity: unrated
target: positive
names:
  - python/references/testing-harness.md
  - python/references/servicer-writer.md
tags: [testing, pattern]
cluster: "E"
still_applies: unknown
status: Resolved
resolved_by: "python/references/patterns-time-and-randomness.md § Do this; python/references/testing-harness.md § Never"
---

# Patch the clock, not the servicer (one module-level _now())

**What happened.** A 2-minute hold is untestable in real time. The seam was a module-level `_now()` indirection in the showing servicer, swapped for a hand-cranked `FakeClock` in `asyncSetUp`. This is a behaviour mock, not an auth mock; the skill's line ('subclassing to mock non-auth behavior is fine; overriding `authorizer()` is not') is right. Design tip: in any Reboot app with deadlines route every wall-clock read through one module-level helper; the difference between a 2-second test and a 2-minute one.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Positive pattern; candidate for `patterns-time-and-randomness.md` (proposal task E).
