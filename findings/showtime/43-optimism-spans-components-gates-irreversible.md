---
id: showtime-43
project: showtime
source: "2026.08.18 reboot-findings.md #43"
reboot_version: 1.4.1
severity: unrated
target: positive
names: []
tags: [pattern, frontend]
cluster: "E"
still_applies: unknown
status: Open
resolved_by: ""
---

# Optimism must span components and gate the irreversible action

**What happened.** Seat map and cart rail are siblings, so pending-hold state lives in a tiny shared store (`useSyncExternalStore`) rather than either component. While any entry is un-confirmed the checkout button is disabled: optimistic UI may lie about what has settled, but must never let the user commit money against a guess.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded (a thing that worked; keep it documented).
