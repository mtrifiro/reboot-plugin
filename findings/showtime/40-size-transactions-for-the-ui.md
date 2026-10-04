---
id: showtime-40
project: showtime
source: "2026.08.18 reboot-findings.md #40"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/servicer-transaction.md
tags: [cost, pattern]
cluster: "D"
still_applies: unknown
status: Resolved
resolved_by: "python/references/servicer-transaction.md § Limits; python/references/patterns-load-and-benchmarking.md § Never"
---

# Size transactions for the UI, not just for correctness

**What happened.** A force-reset of a full house was one transaction issuing ~200 writer calls; since a transaction commits atomically, subscribers saw nothing until the whole thing landed, which read as 'it hung'. Chunking into batches of 25 gave progressive visual feedback and bounded each commit.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.

**Checked at 1.6.0.** No guidance on chunking transactions for UI feedback found in python/references/servicer-transaction.md; grep for `chunk`/`batch` found only unrelated hits. Left unknown because a size-limit note may live elsewhere.
