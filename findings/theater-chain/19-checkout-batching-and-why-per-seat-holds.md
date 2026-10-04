---
id: theater-chain-19
project: theater-chain
source: "theater-chain/reboot-findings.md §17"
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

# Checkout batching and why per-seat holds made it necessary

**What happened.** Round D still takes about 43 s for 40 concurrent checkouts. That is the direct cost of the click-is-the-hold design (§13c): every seat has its own `hold_id`, so `checkout` groups by `(showing_id, hold_id)` and issues one `confirm_seats` per seat, 99 calls for 40 patrons, all serialized on the same `Showing`. Proposed fix: a batched confirm taking `(seat_id, hold_id)` pairs so each patron's checkout is one call per showing. It is a new method (additive, allowed) and was not implemented; the author calls it the obvious next optimization if a real on-sale ever needs handling.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** No skill is named. Classified as primer (an application design record with no plugin edit suggested); see the report for the classification note.

**Checked at 1.6.0.** Not checked; no plugin edit is proposed.
