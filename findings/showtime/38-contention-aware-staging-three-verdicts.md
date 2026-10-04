---
id: showtime-38
project: showtime
source: "2026.08.18 reboot-findings.md #38"
reboot_version: 1.4.1
severity: unrated
target: positive
names: []
tags: [pattern, testing]
cluster: "E"
still_applies: unknown
status: Open
resolved_by: ""
---

# Scenarios sharing a live environment need contention-aware staging and a third verdict state

**What happened.** With the ambient crowd running, a lab scenario picked a 'free' seat from the browser snapshot and lost it before its setup hold landed, reported as a red FAIL. Fix: stage resources where the load generator rarely goes (front rows its gaussian avoids), retry setup with a fresh resource a few times, and report SKIP (amber) when staging still fails, reserving FAIL for a guarantee that actually broke.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded (a thing that worked; keep it documented).
