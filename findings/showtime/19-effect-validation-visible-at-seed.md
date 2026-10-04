---
id: showtime-19
project: showtime
source: "2026.08.18 reboot-findings.md #19"
reboot_version: 1.4.1
severity: unrated
target: positive
names: []
tags: [seeding]
cluster: "8.4"
still_applies: unknown
status: Open
resolved_by: ""
---

# Effect validation is visible at seed time

**What happened.** `initialize`'s 61 `create` calls each log 'Re-running method X.Create to validate effects' in dev; normal, and a confirmation that constructor bodies are deterministic.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded (a thing that worked; keep it documented).
