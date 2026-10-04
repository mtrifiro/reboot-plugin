---
id: showtime-25
project: showtime
source: "2026.08.18 reboot-findings.md #25"
reboot_version: 1.4.1
severity: unrated
target: positive
names: []
tags: []
cluster: "8.4"
still_applies: unknown
status: Open
resolved_by: ""
---

# The additive schema gate works as advertised

**What happened.** Adding a nested model field (zero default) and a new method hot-reloaded under `rbt dev run` with no 'not backwards compatible' complaints, while carts, holds and scheduled expiries survived. The reloading server retried in-flight `ExpireHold` tasks it recovered ('TransactionShouldRetryWithoutBackoff' warnings, then success).

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded (a thing that worked; keep it documented).
