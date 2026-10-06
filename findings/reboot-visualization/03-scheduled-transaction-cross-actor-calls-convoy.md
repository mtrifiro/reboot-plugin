---
id: reboot-visualization-03
project: reboot-visualization
source: "v 1.4.1 Reboot/reboot-visualization/docs/reboot-learnings 03.md §3"
reboot_version: 1.4.0
severity: unrated
target: plugin
names:
  - python/references/scheduling-basic.md
  - python/references/servicer-transaction.md
tags: [cost, pattern, error-text]
cluster: ""
still_applies: no
status: Resolved
resolved_by: "python/references/scheduling-basic.md § Limits"
---

# A scheduled Transaction that makes cross-actor calls under its own lock convoys, and its retry loop never converges

**What happened.** First expiry design: `Cart.expire_hold` as a Transaction calling `Seat.release` per held label and scheduling showing notes. When the timer fired the task wedged in `Timed out waiting 30.0s to acquire exclusive lock; retry the transaction` retries forever (tasks_dispatcher backoff loop), while some of its scheduled side effects (the showing's 'free' notes) landed anyway, so the seat map showed the seat free while the cart still listed it, permanently. The same convoy theater-network hit: 2xN cross-actor calls while holding the cart's exclusive lock; one slow seat call pins the lock for its full 30s timeout and everything on the cart convoys behind it. Fix (theater's design, re-validated): make the timer schedule-only. `expire_hold` only fans out `Seat.schedule().expire(generation, cart_id)`, with no state writes and no synchronous cross-actor calls; each seat expires itself (generation-guarded), then schedules the showing's map note and the cart's `forget_expired` (a plain Writer guarded by the per-label generation captured at hold time). Nothing does slow work under the cart's lock. Test corollary: the showing note and the cart forget arrive independently, so assert both with polls, not one after the other.

**Expected.** Not recorded.

**Repro.** Scheduled `Cart.expire_hold` Transaction calling `Seat.release` per label while seats are contended.

**Where in the skills.** `scheduling-basic.md`, `servicer-transaction.md`. Related to theater-network-18 (same schedule-only redesign, there motivated by a worker crash).

**Checked at 1.6.0.** `scheduling-basic.md` § Limits says 'never hold a lock across a cross-actor round-trip' and keep timers few and coarse; `servicer-transaction.md` § Errors you will see has the 30 s lock-timeout text. Neither records the never-converging retry or that some scheduled side effects landed while the transaction kept retrying.
