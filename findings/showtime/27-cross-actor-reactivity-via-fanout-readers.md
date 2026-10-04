---
id: showtime-27
project: showtime
source: "2026.08.18 reboot-findings.md #27"
reboot_version: 1.4.1
severity: unrated
target: positive
names: []
tags: [pattern, cost, index-gap]
cluster: "E"
still_applies: unknown
status: Resolved
resolved_by: "python/references/patterns-cross-actor-reads.md § Do this"
---

# Cross-actor reactivity propagates through fan-out Readers (verified)

**What happened.** A `reactively()` subscription on `BoxOffice.overview` (a Reader that `asyncio.gather`s 48 `Showing.summary` reads) is pushed a fresh response when a single Showing changes. Settled in one 9-second harness test. Aggregated dashboard readers are the right pattern: N per-entity subscriptions collapse into one, updates arrive as one frame, and no write-path denormalization is needed. The source notes the references only hint at this; its documentation ask is suggested improvement 4.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded (a thing that worked; keep it documented).
