---
id: ticketing-06
project: ticketing
source: "Punch List - Ticketing App Build Findings.md §6"
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

# Chapter 6: the refund example ends before the business does

**What happened.** The chapter's refund workflow stops at 'record the outcome and send a receipt', but the refunded seat must go back on sale; building the app surfaced a user-visible bug where refunded seats stayed sold on the seat map. Working resolution: the workflow's last step calls a `release_seats` transaction that atomically clears each `Seat` and the event's denormalized map entry. The release is guarded (`buyer_id` must still match) so replaying or racing a release can never free a seat someone else now holds.

**Expected.** The example carries two points: a workflow's later steps can and often must use a transaction to keep multi-instance state consistent (method kinds compose), and the guard is the chapter's idempotency discipline applied to business state.

**Repro.** Not recorded.

**Where in the skills.** Primer Chapter 6 - Work Survives Interruption.
