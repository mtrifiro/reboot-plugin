---
id: showtime-11
project: showtime
source: "2026.08.18 reboot-findings.md #11"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/patterns-common-gotchas.md
tags: [pattern, negative-space]
cluster: "E"
still_applies: unknown
status: Open
resolved_by: ""
---

# Compute non-deterministic values in the transaction and pass them to writers

**What happened.** Writer bodies re-execute under dev-mode effect validation; a writer that called `time.time()` itself would fail validation. Transactions may recompute on retry, which is safe because only one attempt commits. The source suggests `patterns-common-gotchas.md` name this 'pass now/uuid down' pattern (implied by its gotcha 8, but the constructive pattern is not stated).

**Expected.** Constructive pattern named in the gotchas reference.

**Repro.** Not recorded.

**Where in the skills.** `patterns-common-gotchas.md`.

**Checked at 1.6.0.** Not found as a named pattern for writers/transactions; python/references/servicer-workflow.md:658-678 covers only workflow-side capture via `at_least_once`. Did not confirm gotcha 8 wording.
