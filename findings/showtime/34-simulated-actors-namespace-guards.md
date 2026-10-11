---
id: showtime-34
project: showtime
source: "2026.08.18 reboot-findings.md #34"
reboot_version: 1.4.1
severity: unrated
target: positive
names: []
tags: [pattern, auth]
cluster: "E"
still_applies: unknown
status: Open
resolved_by: ""
---

# Simulated actors need a namespace and guards

**What happened.** The `sim-` prefix is load-bearing three ways: the lab's only reset power is scoped to sim-owned seats, the expiry path skips cart cleanup for sim holders, and sweeps match the prefix. Prefix-scoped privileges kept the diagnostic tool unable to corrupt production state by construction, proven by a test that lab-restores a real hold and asserts it survived.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded (a thing that worked; keep it documented).
