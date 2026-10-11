---
id: showtime-45
project: showtime
source: "2026.08.18 reboot-findings.md Suggested skill improvements, bullet 2"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/servicer-transaction.md
tags: [negative-space]
cluster: "4.1"
still_applies: no
status: Obsolete
resolved_by: ""
---

# Document whether a Transaction method may mutate self.state

**What happened.** `servicer-transaction.md` never says; every example only calls other actors' writers.

**Expected.** An explicit yes/no, to prevent the defensive 'compose writers for everything' workaround if mutation is allowed.

**Repro.** Not recorded.

**Where in the skills.** `servicer-transaction.md`.

**Checked at 1.6.0.** python/references/servicer-transaction.md:18-25 now says `Exclusive()` mode 'is the choice for a body that writes `state`', and upgrade/migrations/1.6.0/transaction-mode.md:22-27 says a transaction that assigns to its own state chooses exclusive. Mutating own state is therefore documented as allowed.
