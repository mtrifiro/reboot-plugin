---
id: meridian-circuit-08
project: meridian-circuit
source: "v 1.4.1 Reboot/meridian-circuit/docs/2026.08.18 reboot-learnings porting supabase app.md §8"
reboot_version: 1.4.1
severity: unrated
target: positive
names:
  - python/references/patterns-time-and-randomness.md
tags: [pattern]
cluster: ""
still_applies: no
status: Resolved
resolved_by: "python/references/patterns-time-and-randomness.md § Three escape routes for addressed values, in order of preference"
---

# Writers never read the clock, including simulated ones: caller deadlines, relative timers, crc32, a virtual clock

**What happened.** Standard discipline applied throughout: a writer body re-executes under effect validation, so `random()` and `time.time()` both break it. Display deadlines come from the caller (`expires_at_epoch_s`), enforcement is a relative `schedule(when=timedelta(...))`, and the pre-sold seat spread is derived from `crc32(showing_id:seat_id)` rather than `random()`. The ambient crowd has no caller to ask for the time, so it carries a virtual clock: the browser seeds `clock_epoch_s` at `start` and each tick advances it by exactly the delay it just scheduled, keeping crowd events sortable against browser events in the chain-wide ticker without any body reading wall time. Order codes likewise went from `md5(random())` to `crc32(cart_id:order_counter)`, a pure function of state.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** `python/references/patterns-time-and-randomness.md`. marquee-control-03 records the same caller-display / server-timer split.

**Checked at 1.6.0.** `patterns-time-and-randomness.md` § Three escape routes for addressed values, in order of preference teaches 'push it into the request' and 'derive it from state you already persist'. The virtual-clock technique for a callerless loop is not there (grep for `virtual clock` found nothing).
