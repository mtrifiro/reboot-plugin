---
id: ticketing-07
project: ticketing
source: "Punch List - Ticketing App Build Findings.md §7"
reboot_version: 1.4.1
severity: green
target: primer
names: []
tags: [pattern]
cluster: "8.4"
still_applies: unknown
status: Open
resolved_by: ""
---

# Minor: Chapter 6 refund sketch identity, Chapter 2 seat-ID scheme confirmed

**What happened.** Chapter 6: the refund sketch calls `Order.ref(request.order_id)` inside the workflow; when the workflow runs on the order actor, the id comes from `context.state_id` and the request can be empty, which is simpler and shows where a workflow's identity lives. Chapter 2: the seat-ID scheme (`event-204:A-14`) worked exactly as described; no change, but the app can now be cited as the concrete artifact.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Primer Chapter 6 and Chapter 2.
