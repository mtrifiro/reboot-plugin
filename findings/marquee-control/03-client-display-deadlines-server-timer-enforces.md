---
id: marquee-control-03
project: marquee-control
source: "v 1.4.1 Reboot/Archive/marquee-control/docs/reboot-learnings.md §2026-08-17 build session, bullet 3"
reboot_version: 1.4.1
severity: unrated
target: positive
names:
  - python/references/patterns-time-and-randomness.md
tags: [pattern]
cluster: ""
duplicate_of: meridian-circuit-08
still_applies: no
status: Resolved
resolved_by: "python/references/patterns-time-and-randomness.md § Three escape routes for addressed values, in order of preference"
---

# Client-supplied display deadlines; the scheduled timer is the enforcement

**What happened.** The server cannot read the clock in writers, so the client supplies the display deadline; a lying client can only mis-display its own countdown, because the enforced expiry is the scheduled timer, always `DEFAULT_HOLD_SECONDS` from commit.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** `patterns-time-and-randomness.md`. Same lesson as meridian-circuit-08.

**Checked at 1.6.0.** `patterns-time-and-randomness.md` § Three escape routes for addressed values, in order of preference teaches pushing the value into the request; `scheduling-basic.md` § Never says to commit expiry with a scheduled writer.
