---
id: showtime-37
project: showtime
source: "2026.08.18 reboot-findings.md #37"
reboot_version: 1.4.1
severity: unrated
target: framework
names: []
tags: [negative-space]
cluster: "E"
still_applies: unknown
status: Resolved
resolved_by: "python/references/servicer-transaction.md § Limits"
---

# Effect validation tolerated a transaction whose sub-call arguments are random

**What happened.** `crowd_tick` re-ran under validation with a fresh `random.Random()` (different seats each run) and the suite stayed green, consistent with validation checking the actor's own state mutations (crowd_tick has none) rather than sub-call payloads. Observed behavior, not documented contract.

**Expected.** A deterministic tick (seed the rng from request fields) is the safer shape if a chain ever misbehaves under validation.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.

**Resolution (2026-10-10).** `servicer-transaction.md` § Limits: effect validation compares the actor's own state changes, not a sub-call's arguments; seed randomness from request fields.
