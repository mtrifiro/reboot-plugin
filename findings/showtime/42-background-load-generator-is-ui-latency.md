---
id: showtime-42
project: showtime
source: "2026.08.18 reboot-findings.md #42"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/servicer-transaction.md
tags: [cost, pattern]
cluster: "D"
still_applies: unknown
status: Open
resolved_by: ""
---

# A background load generator becomes UI latency

**What happened.** The ambient crowd's tick was a transaction making dozens of writer calls on one Showing; a real patron's `add_seat` had to wait its turn, so the cart lagged seconds behind the optimistically painted seat. Fix: bound the per-tick work (resolve at most 4 parties, fewer arrivals) so the actor is held briefly, and mirror the optimism into every view of the same fact (the cart, not just the seat map).

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.

**Checked at 1.6.0.** No guidance on actor-as-lock cost from background work found in python/references/servicer-transaction.md or state-actor-decomposition.md (not read in full).
