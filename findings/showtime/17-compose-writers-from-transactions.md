---
id: showtime-17
project: showtime
source: "2026.08.18 reboot-findings.md #17"
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

# Avoid mutating self.state inside a Transaction; compose small internal Writers

**What happened.** The documented examples only ever compose other actors' writers from a transaction. Structure used: public Transactions on `User` compose small internal Writers (`push_cart_item`, `finalize_checkout`, ...), which also gave each mutation a natural authorization boundary. (The open question this raised, whether a Transaction may mutate `self.state`, is recorded as suggested improvement 2.)

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded (a thing that worked; keep it documented).
