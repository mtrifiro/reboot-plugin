---
id: marquee-control-07
project: marquee-control
source: "v 1.4.1 Reboot/Archive/marquee-control/docs/reboot-learnings.md §2026-08-17 build session, bullet 7"
reboot_version: 1.4.1
severity: unrated
target: positive
names:
  - python/references/scheduling-recurring.md
tags: [pattern, cost]
cluster: ""
still_applies: yes
status: Open
resolved_by: ""
---

# Ambient-crowd pacing: batch per tick, bias to the focused showing, budget for dev tick overhead

**What happened.** N showings x one action per tick means any one map changes every `N x delay` seconds: at 48 showings and 2 s ticks, about 90 s of stillness. More actions per tick (4) beats faster ticks, because the tick transaction is one serialized chain, so batching adds throughput without concurrent 2PC pressure; but even 4/tick across 48 maps averages under one visible hold per map. What worked is focus bias: the SPA reports the on-screen showing via a `Crowd.focus` writer and the tick sends about 60% of hold parties there (verified live: focused map carries 6-14 standing amber holds; unfocused maps still churn). Measured tick cadence in dev: about 3.3 s for a 1.2-3.0 s scheduled delay (transaction commit plus effect validation eat the difference); budget for that when tuning.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** `scheduling-recurring.md`. Related to theater-network-10 (ambient simulator) and showtime-42 (bound per-tick work).

**Checked at 1.6.0.** `patterns-load-and-benchmarking.md` § Never and `servicer-transaction.md` § Scales as say to bound a background loop's per-tick work (showtime-42); the focus-bias technique and the dev tick-cadence overhead are not recorded.
