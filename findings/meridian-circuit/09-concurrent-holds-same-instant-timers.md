---
id: meridian-circuit-09
project: meridian-circuit
source: "v 1.4.1 Reboot/meridian-circuit/docs/2026.08.18 reboot-learnings porting supabase app.md §9"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/scheduling-basic.md
tags: [negative-space, pattern]
cluster: ""
duplicate_of: theater-network-12
still_applies: no
status: Resolved
resolved_by: "python/references/scheduling-basic.md § Never"
---

# Concurrent holds must not schedule timers for the same instant; jitter with crc32, not hash()

**What happened.** Two holds placed in the same instant would schedule two `expire_hold` tasks on one actor for the identical time, a known way to kill the database worker. Each hold's timer is jittered by `crc32(hold_id:seat_id) % 997` milliseconds: `crc32`, not `hash()`, because `hash()` is salted per process and the body re-executes under effect validation.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** `python/references/scheduling-basic.md`. Same gap as theater-network-12.

**Checked at 1.6.0.** `scheduling-basic.md` § Never forbids several scheduled transactions on one actor with the same `when=` and § Errors you will see has the `database.cc:1374` assert. The jitter technique and the salted-`hash()` trap are not mentioned (grep for `jitter`, `salted`, `hash(` found nothing).
