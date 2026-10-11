---
id: theater-chain-07
project: theater-chain
source: "theater-chain/reboot-findings.md §7"
reboot_version: 1.4.1
severity: unrated
target: positive
names:
  - python/references/state-collections.md
tags: [pattern]
cluster: "E"
still_applies: unknown
status: Open
resolved_by: ""
---

# Design choices the app made: inline seats, summary reader, cart versus history

**What happened.** Recorded because the "which shape?" decisions took the most thought. (1) 200 seats live inline on `Showing` as `list[Seat]`, not 200 actors: a seat has no lifecycle, methods, or auth apart from its showing, and seat count is fixed by the building (a genuine domain bound, not the invented cap `state-collections.md` warns against); holding 8 seats is a single-actor `Writer` rather than an 8-actor transaction and one reactive reader streams the whole map instead of 200 subscriptions. (2) Two readers per showing, `get` and `stats`: the dashboard shows live occupancy for many showings; `stats` returns eight integers; reactive readers push the whole response on every change, so splitting a fat reader into a summary reader is cheap and probably should be a documented pattern. (3) Cart inline on `User` (bounded at 8 by the product rule), order history in an `OrderedMap` (unbounded); same actor, two container shapes, and `state-collections.md` picks them apart correctly.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** `python/references/state-collections.md`.

**Checked at 1.6.0.** Not checked; this item is a record of what worked (target positive).
