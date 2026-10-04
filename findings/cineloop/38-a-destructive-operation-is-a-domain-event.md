---
id: cineloop-38
project: cineloop
source: "cineloop/reboot-findings.md §28 (Part 4)"
reboot_version: 1.4.1
severity: unrated
target: positive
names:
  - python/references/servicer-transaction.md
tags: [pattern]
cluster: "E"
still_applies: unknown
status: Open
resolved_by: ""
---

# A destructive operation is a domain event, not a DELETE (refund as a real transition)

**What happened.** Lab reset tools ('clear this auditorium', 'clear the chain') were routed through a real refund instead of blanking seat state, because blanking would leave every receipt pointing at seats somebody else can now buy (a confirmation code still saying 'valid for entry' for a resold seat). `Order.refund` marks the order refunded and keeps it; `Showing.release_order` puts the seats back; `Admin.refund_order` is the transaction that does both (half landing is worse than neither); the reset tools call that same route. Model the undo as a real state transition with its own name ('unsell' is a refund, 'remove user' is a deactivation). Payoff: the receipt could render 'RESERVATION REFUNDED - no longer valid for entry'.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Positive pattern; kept as a candidate for a `patterns-*` reference (proposal task E).
