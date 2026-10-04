---
id: ticketing-03
project: ticketing
source: "Punch List - Ticketing App Build Findings.md §3"
reboot_version: 1.4.1
severity: unrated
target: primer
names: []
tags: [pattern]
cluster: "8.4"
still_applies: unknown
status: Open
resolved_by: ""
---

# Chapter 4: the purchase transaction is also the consistency tool for derived state

**What happened.** The chapter's `purchase` example spans `Seat.buy` and `Order.record_seat`. The working app adds a third call, `Event.record_sale`, in the same transaction: the denormalized seat map commits with the sale or rolls back with it.

**Expected.** Extend the example (or add a sentence): a transaction is how a denormalized copy stays truthful, connecting the method-kind chapter to the boundary discussion in Chapter 2.

**Repro.** Not recorded.

**Where in the skills.** Primer Chapter 4 - Method Kinds Carry the Contract.
