---
id: reboot-air-141-21
project: reboot-air-141
source: "reboot-air/REBOOT_FINDINGS.md §22"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/servicer-transaction.md
  - inspect/SKILL.md
tags: [negative-space, operations, error-text, cost]
cluster: "4.1"
still_applies: yes
status: Open
resolved_by: ""
---

# Caller that vanishes mid-transaction leaves the actor locked permanently

**What happened.** A load driver ran eight virtual users against the dev server for twenty seconds (searches, live-map reads, a small share of book-then-cancel), then cancelled its worker tasks at the end. Four of five development accounts were fine; the fifth could not sign in at all, still hung ten minutes later. Backend log: `reboot.aio.aborted.SystemAborted: aborted with 'Unavailable': Timed out waiting 30.0s to acquire exclusive lock; retry the transaction.` The wedged account was worker 0's, whose `book` transaction held an exclusive lock that was never released when its caller went away. It takes down sign-in, because Reboot's OAuth server calls `set_claims` (a write) on the `User` actor during token exchange, so the symptom looks like "OAuth is broken". It does not heal: no visible lease expiry or reaper; the 30 seconds is how long a waiter waits, not how long a holder holds; it outlives everything short of a restart. No reference says what happens when a caller vanishes mid-transaction. The people who hit it are load generators, timing-out integration tests, cancelled CI jobs, and Ctrl-C. The author's driver now drains instead of cancelling.

**Expected.** In order of value: release locks when the caller's channel closes; failing that, a holder-side lease; one paragraph in the transaction reference ("a transaction whose caller disconnects keeps its lock until the application restarts; do not cancel in-flight calls"); and `rbt inspect` showing which actors hold locks and for how long.

**Repro.** See the companion load-test findings for the step list: a Transaction writing a `User` actor, driven concurrently from an `ExternalContext` in another process, callers cancelled mid-flight, then sign in as the affected identity (it hangs; restart clears it).

**Where in the skills.** `python/references/servicer-transaction.md`; also the `inspect` skill.

**Checked at 1.6.0.** Still absent. `python/references/servicer-transaction.md`, `patterns-common-gotchas.md`, and `testing-*.md` have no text on disconnected callers or retained locks (grep for disconnect / vanish / cancel found only unrelated lines), and `inspect/SKILL.md` has no lock inspection.
