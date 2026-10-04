---
id: ticketing-02
project: ticketing
source: "Punch List - Ticketing App Build Findings.md §2"
reboot_version: 1.4.1
severity: unrated
target: primer
names: []
tags: [cost, pattern]
cluster: "8.4"
still_applies: unknown
status: Open
resolved_by: ""
---

# Chapter 2: the instance-boundary discussion covers writes but not reads

**What happened.** The chapter argues per-seat instances so competing buyers contend only on their own seat, and rejects one big `Event` that serializes unrelated purchases. Correct for writes, silent on reads. The seat map, which every visitor opens, is an event-wide question; answering it from per-seat instances costs a fan-out read over every seat per evaluation, and a browser subscribing per seat opens one subscription per instance. Both made the real app visibly slow.

**Expected.** The boundary decision has a read side. App resolution: a denormalized `SeatSummary` list on `Event`, written by the purchase transaction, so the sold-once rule stays on `Seat` while the whole map is one instance read; purchases briefly serialize through the `Event` writer for the recording step, and that trade belongs in the text.

**Repro.** Not recorded.

**Where in the skills.** Primer Chapter 2 - State Types Hold Data and Rules Together.
