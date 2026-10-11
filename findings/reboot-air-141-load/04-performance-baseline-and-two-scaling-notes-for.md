---
id: reboot-air-141-load-04
project: reboot-air-141-load
source: "reboot-air/REBOOT_LOAD_TEST_FINDINGS.md Appendix"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/stdlib-ordered-map.md
  - python/references/rpc-forall.md
tags: [cost, pattern, negative-space]
cluster: "D"
still_applies: yes
status: Resolved
resolved_by: "python/references/patterns-load-and-benchmarking.md § Scales as"
---

# Performance baseline and two scaling notes for ordered-map and forall

**What happened.** Appendix of baseline numbers, included for context rather than as a complaint. Local dev server, 4-6 virtual users, read-only mix: `search_pair` 1151 calls 76.7 rps p50 20ms p90 29ms p99 58ms; `live_map` 438 calls 29.2 rps p50 63ms p99 129ms; `flight_details` 429 calls 28.6 rps p50 1ms p99 4ms; `trips` 301 calls 20.1 rps p50 6ms p99 14ms; TOTAL 2591 calls 172.7 rps. With about 10% book-and-cancel writes on a healthy server, 8 users: `book_and_cancel` 299 calls 14.9 rps p50 141ms p90 217ms p99 303ms; `search_pair` 1217 calls 60.8 rps p50 34ms p99 82ms; TOTAL 3013 calls 150.6 rps. A write-enabled run against the server holding the wedged actor managed 11 rps with about 400ms reads versus 185 rps read-only minutes later; the author says this is confounded by Finding 2 and draws no conclusion. Two notes: (1) `Airline.search_flights` without a city pair is about 100x slower than with one, because the schedule `OrderedMap` is keyed `date#origin#destination#departure#number` and dropping the pair turns a prefix scan into a whole-day scan with a `Flight.details` fan-out; the author calls this their schema choice, not a Reboot defect. (2) `Flight.forall(...).details(context)` across a few hundred actors is the dominant cost in that slow path.

**Expected.** A note in `stdlib-ordered-map.md` about designing keys for the queries you actually run; a word in `rpc-forall.md` about its scaling.

**Repro.** Not recorded.

**Where in the skills.** `python/references/stdlib-ordered-map.md` and `python/references/rpc-forall.md`.

**Checked at 1.6.0.** Still absent. Grep of `python/references/stdlib-ordered-map.md` for prefix / key design and of `python/references/rpc-forall.md` for scaling / hundred / timeout found nothing.
