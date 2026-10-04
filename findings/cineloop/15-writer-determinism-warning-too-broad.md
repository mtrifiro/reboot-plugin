---
id: cineloop-15
project: cineloop
source: "cineloop/reboot-findings.md Part 2 §B"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/scheduling-recurring.md
  - python/references/servicer-writer.md
tags: [negative-space]
cluster: "E"
still_applies: yes
status: Open
resolved_by: ""
---

# scheduling-recurring.md determinism warning is too broad

**What happened.** The parenthetical in `scheduling-recurring.md` says to avoid persisting a wall-clock or random value into `self.state` from a writer because writer bodies re-execute and a stored non-deterministic value would differ across runs. Taken at face value it forbids storing a deadline, expiry, `created_at` or random token, which is common and mostly fine because effect validation retries rather than diffs. The source only established that by reading `EffectValidationRetry` in the runtime, which the skill tells you not to do. (See item 6.)

**Expected.** Replace with: persisting a `now()` or random value from a writer is safe when the value is only observed (deadline, `created_at`, display token), because effect validation aborts and retries rather than comparing two runs. It is not safe when something must later re-derive or address it (actor ID, idempotency key, foreign key, a confirmation code the user quotes back); derive those deterministically (owner ID plus a monotonic counter). In a `Workflow` the stricter rule applies to everything; capture now once via `at_least_once`.

**Repro.** Not recorded.

**Where in the skills.** `python/references/scheduling-recurring.md` (the parenthetical), cross-checked with `servicer-writer.md`. Conflicts with theater-network-03 on whether a differing persisted value fails validation.

**Checked at 1.6.0.** `python/references/scheduling-recurring.md` lines 195-203 still carry the original broad warning unchanged.
