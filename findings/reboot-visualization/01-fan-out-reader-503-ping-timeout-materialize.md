---
id: reboot-visualization-01
project: reboot-visualization
source: "v 1.4.1 Reboot/reboot-visualization/docs/reboot-learnings 03.md §1"
reboot_version: 1.4.0
severity: unrated
target: plugin
names:
  - python/references/patterns-cross-actor-reads.md
  - python/references/rpc-forall.md
  - python/references/patterns-load-and-benchmarking.md
tags: [cost, pattern, error-text]
cluster: ""
duplicate_of: theater-network-08
still_applies: yes
status: Resolved
resolved_by: "python/references/patterns-cross-actor-reads.md § Do this"
---

# Fan-out reads from inside a Reader 503 with 'ping timeout', even chunked forall, while each actor answers in 60ms

**What happened.** 48 seat actors; `Showing.seat_map` fanned out via `asyncio.gather` and then via `Seat.forall(...)` in chunks of 12-16 (theater-network's audit pattern and chunk size): every one-shot HTTP call to the reader returned `503 {"code":14,"message":"ping timeout"}` in 1-8s, with no server-side log at all (the string lives in the native layer, not the Python runtime). Direct `Seat.Get` on any seat: 200 in about 60ms. `--no-chaos` and `--effect-validation=disabled` made no difference. Theater-network's audit does the same successfully, so the trigger is environmental or shape-specific; left as an unresolved upstream question. Fix (theater's own design): materialize. Every seat commit already schedules a note to its Showing; the note now also updates `seat_status`/`holder`/`expires` maps on the Showing, so `seat_map` became a single-actor read, 100ms and fully reactive (the generated `useSeatMap()` hook pushes updates; no polling).

**Expected.** Rule of thumb from the source: fan-out readers are a smell; if commits can feed an aggregate at write time the read side becomes trivial and reactive.

**Repro.** One-shot HTTP call to a reader fanning out to 48 seat actors (gather, or `forall` in chunks of 12-16).

**Where in the skills.** `patterns-cross-actor-reads.md`, `rpc-forall.md`, `patterns-load-and-benchmarking.md`. Same gap as theater-network-08; meridian-circuit-01 hit it at 48 actors too. A later project traced one cause of `ping timeout` to Envoy on macOS arm64 (reboot-crm-07); the source does not establish that here.

**Checked at 1.6.0.** `patterns-cross-actor-reads.md` § Do this teaches materialize-on-write only for 'very wide fan-out (about 150 children)' and otherwise recommends a `forall` fan-out reader; `patterns-load-and-benchmarking.md` § Errors you will see maps `Unavailable: ping timeout` to the 150-actor case or the Envoy window. A failure at 48, and the absence of any server-side log line, are not recorded.
