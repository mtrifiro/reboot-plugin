---
id: team-memo-0826-07
project: team-memo-0826
source: "2026.08.26 Findings for Reboot Team - Docs, Skills, and Runtime.md Q1"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/state-collections.md
  - python/references/servicer-writer.md
  - python/references/servicer-workflow.md
tags: [contradiction, negative-space, pattern]
cluster: "E"
duplicate_of: student-system-08
still_applies: yes
status: Open
resolved_by: ""
---

# Randomness in writer and transaction bodies: what is the contract?

**What happened.** The skills teach that bodies re-execute under retries and effect validation and must mutate deterministically, yet `state-collections` writes `str(uuid4())` inside a constructor writer, and the app's checkout generates `uuid4()` order ids inside a transaction. Both survived effect validation in practice.

**Expected.** Source asks: is there recorded-randomness machinery, does effect validation tolerate differing fresh ids, and is the pattern safe under a genuine mid-body transaction retry?

**Repro.** Not recorded.

**Where in the skills.** `state-collections.md`; `servicer-writer.md`; proposal task E (`patterns-time-and-randomness.md`).

**Checked at 1.6.0.** python/references/state-collections.md:188-222 still uses `uuid7()` in write bodies; python/references/servicer-workflow.md:658-665 still says there is no clock/random on the context for workflows. No reference states the writer/transaction contract.
