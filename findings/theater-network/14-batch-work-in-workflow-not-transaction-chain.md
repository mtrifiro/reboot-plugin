---
id: theater-network-14
project: theater-network
source: "theater-network/docs/reboot-findings.md §14"
reboot_version: 1.4.0
severity: unrated
target: plugin
names:
  - python/references/servicer-workflow.md
  - python/references/servicer-transaction.md
tags: [cost, pattern]
cluster: "D"
still_applies: yes
status: Resolved
resolved_by: "python/references/servicer-transaction.md § Scales as; python/references/patterns-load-and-benchmarking.md § Scales as; python/references/servicer-workflow-declare.md § Scales as"
---

# Build batch work in a Workflow, not a transaction task chain

**What happened.** Room buildout ran at a hard about 5 constructor-writes/second however the transactions were arranged (sequential awaits, `asyncio.gather` in the transaction, more rows per task, three concurrent chains via separate builder actors). The cost is per two-phase-commit participant: every seat created inside a transaction pays about 200ms, serialized. Bare writer-factory calls measure 15-120ms and parallelize across actors; the transaction is the tax. Moving the build into a `Workflow` on the Showing fixed it: calls are plain independent writer calls (memoized per alias so a resumed build never double-places), state updates are inline `.per_workflow(alias).write(context, fn)`, and it is durable across restarts. 216 seats: 54s as a transaction chain, 15.7s as a workflow, audit-consistent, progress animating per row. Wave width matters: one row (about 20 concurrent calls) is the sweet spot; 3-row waves (about 54 concurrent) made placements ping out and retry-loop (103s).

**Expected.** Rule from the source: a transaction buys atomicity across participants; if the work is N independent creations it is the wrong tool, use a workflow.

**Repro.** 216-seat room build, transaction chain vs workflow (numbers above).

**Where in the skills.** `servicer-transaction.md` / `servicer-workflow.md` (Scales as); `patterns-load-and-benchmarking.md` in proposal task D.

**Checked at 1.6.0.** `servicer-transaction.md` steers external side effects to workflows but gives no participant-cost reasoning, wave width or numbers.
