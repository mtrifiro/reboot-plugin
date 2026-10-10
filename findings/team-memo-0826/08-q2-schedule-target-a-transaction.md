---
id: team-memo-0826-08
project: team-memo-0826
source: "2026.08.26 Findings for Reboot Team - Docs, Skills, and Runtime.md Q2"
reboot_version: 1.4.1
severity: unrated
target: framework
names: []
tags: [negative-space]
cluster: "8.4"
still_applies: unknown
status: Resolved
resolved_by: "python/references/scheduling-basic.md § Limits"
---

# Can schedule() target a transaction method?

**What happened.** The skills show writers and workflows being scheduled. The cart-hold expiry needed cross-actor work on a timer; it was routed as a scheduled workflow that calls a guarded transaction, which works, but scheduling the transaction directly would be simpler if supported.

**Expected.** Source asks whether it is supported.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.

**Resolution (2026-10-10).** `scheduling-basic.md` § Limits states what is known: whether `schedule()` can target a `Transaction` is undocumented; schedule a writer, or a workflow that calls the guarded transaction. The answer itself is Reboot's.
