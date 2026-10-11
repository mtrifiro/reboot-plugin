---
id: showtime-31
project: showtime
source: "2026.08.18 reboot-findings.md #31"
reboot_version: 1.4.1
severity: unrated
target: positive
names: []
tags: [testing]
cluster: "8.4"
still_applies: unknown
status: Open
resolved_by: ""
---

# Concurrent same-method calls inside one transaction contend honestly

**What happened.** `asyncio.gather` of two `hold_seat` writer calls on the same Showing from one TransactionContext yields one winner and one typed refusal. Catching a declared `<Method>Aborted` inside a transaction is recoverable (the transaction still commits with the winner's effects), as `patterns-idempotency.md` promises. No aliases needed for repeated same-method calls in a transaction (unlike `initialize`). Verified by the lab-scenario test.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded (a thing that worked; keep it documented).
