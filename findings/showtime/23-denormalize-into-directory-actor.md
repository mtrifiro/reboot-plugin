---
id: showtime-23
project: showtime
source: "2026.08.18 reboot-findings.md #23"
reboot_version: 1.4.1
severity: unrated
target: positive
names: []
tags: [pattern, cost]
cluster: "E"
still_applies: unknown
status: Open
resolved_by: ""
---

# Kill reader waterfalls by denormalizing static facts into the directory actor

**What happened.** A dashboard chaining `Directory.get` -> N `Child.get` -> M `Grandchild.summary` pays a round-trip per level. Carrying immutable display facts (titles, times, prices) in the directory's own state collapses it to one read plus M parallel live subscriptions.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded (a thing that worked; keep it documented).
