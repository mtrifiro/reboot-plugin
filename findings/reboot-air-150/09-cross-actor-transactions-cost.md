---
id: reboot-air-150-09
project: reboot-air-150
source: "reboot-air/reboot-findings.md §9"
reboot_version: 1.5.0
severity: unrated
target: plugin
names:
  - python/references/api-methods.md
tags: [cost, pattern, negative-space]
cluster: "D"
still_applies: yes
status: Resolved
resolved_by: "python/references/patterns-load-and-benchmarking.md § Scales as"
---

# Cross-actor transactions cost ~300 ms; a click that must feel instant has to be a single-actor writer

**What happened.** Measured under the test harness (`backend/tests/timing_probe.py`, in-process, one call at a time, medians), effect validation on / off: `Flight.get` (Reader, 288 seats) 56 ms / 48 ms; `User.cart` (Reader) 32 ms / 32 ms; `Flight.hold` (Writer, self-schedule) 59 ms at rest / 51 ms; `User.add_to_cart` (Transaction: Flight writer + User write) 543 ms / 355 ms. The original design put "hold a seat" behind a `User` transaction so the cart entry and the seat hold landed atomically; in the browser that was 480 ms click-to-flip. Even a single-actor Reader is ~30 ms, so a sub-100 ms interaction has exactly one writer round-trip. Change: `Flight.hold` is now a Writer the browser calls directly; it schedules a workflow on itself that pushes the cart entry to the `User` actor afterwards. Click-to-confirm dropped to ~60 ms; the cart is eventually consistent by ~100 ms, hidden by the reactive hooks.

**Expected.** A one-line "a transaction is roughly 5-10x a writer" in `api-methods.md` would have steered the design correctly. Also: why is the transaction floor ~300 ms in dev (2PC round trips, effect validation, envoy hops) and is it the same on Reboot Cloud?

**Repro.** Not recorded beyond the timing probe described.

**Where in the skills.** `python/references/api-methods.md` (no relative cost of the four method kinds).

**Checked at 1.6.0.** `python/references/api-methods.md` has no cost comparison of method kinds (grep for `cost` found none).
