---
id: showtime-12
project: showtime
source: "2026.08.18 reboot-findings.md #12"
reboot_version: 1.4.1
severity: unrated
target: positive
names: []
tags: [pattern]
cluster: "E"
still_applies: unknown
status: Open
resolved_by: ""
---

# The token-guard pattern makes scheduled expiry race-free with zero coordination

**What happened.** Hold carries a UUID; expiry/release/confirm all present it; whoever changed the seat since invalidated the token, so a timer firing late (or after purchase) is a provable no-op. Verified by `test_expiry_is_a_noop_after_purchase`.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded (a thing that worked; keep it documented).
