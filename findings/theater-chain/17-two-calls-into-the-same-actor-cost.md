---
id: theater-chain-17
project: theater-chain
source: "theater-chain/reboot-findings.md §16"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/servicer-transaction.md
tags: [cost, pattern]
cluster: "D"
still_applies: yes
status: Resolved
resolved_by: "python/references/servicer-transaction.md § Never; python/references/patterns-load-and-benchmarking.md § Scales as"
---

# Two calls into the same actor cost about 10x under load

**What happened.** The first load run was dismal: 40 concurrent holds on one seat took 75 seconds. In `User.add_seats`, `view = await showing.get(context)` read all 200 seats only to look up the seat's price and film title for the cart row, then `await showing.hold_seats(context, ...)` held one of them. Every click made two round trips into an actor that serializes writers and dragged a 200-seat payload across one, while 39 others queued. Fix: let the writer return what it already has, by adding `seats: list[Seat]` and `film_title: str` (zero defaults, so additive and accepted without an expunge) to `HoldSeatsResponse`. Measured back-to-back, same machine and script: A stampede 75.7s to 7.9s; B block 108s to 9.8s; C spread 85s to 15.6s; roughly 10x from deleting one line. Uncontended floor about 144 ms per hold (p50, in-process, effect validation off).

**Expected.** `servicer-transaction.md` says a transaction "may freely call other in-system actors", which reads as cheap. Add a line: prefer one call that returns what you need over two that read then write, and note that a `Writer`'s response is the natural place to hand back the state it just touched.

**Repro.** Not recorded.

**Where in the skills.** `python/references/servicer-transaction.md`.

**Checked at 1.6.0.** Still present. `python/references/servicer-transaction.md:99` still says transactions "may freely call other in-system actors" with no cost note (grep for cost / participants / queue found only line 21 on queued callers).
