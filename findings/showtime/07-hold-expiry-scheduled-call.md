---
id: showtime-07
project: showtime
source: "2026.08.18 reboot-findings.md #7"
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

# Hold expiry is just a scheduled method call with a token guard

**What happened.** `ref.schedule(when=...).expire_hold(...)` from the transaction that placed the hold. A hold token makes expiry a no-op when the seat was already purchased or re-held; no background poller needed. (Design-phase finding.)

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded (a thing that worked; keep it documented).
