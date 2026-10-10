---
id: agentic-demo-02
project: agentic-demo
source: "v 1.4.1 Reboot/Archive/agentic-demo/docs/reboot-learnings.md §3"
reboot_version: 1.4.0
severity: unrated
target: plugin
names:
  - python/references/servicer-transaction.md
tags: [pattern, negative-space, error-text]
cluster: ""
duplicate_of: returns-desk-02
still_applies: yes
status: Resolved
resolved_by: "python/references/servicer-transaction.md § Errors you will see"
---

# Keep an observer's display state out of a commit transaction

**What happened.** The first cut had `ServiceCase.commit_replacement` (a transaction) also call `ResolutionAttempt.record_result(status=WON)` so the winner was marked atomically. Two problems: (a) any test or tool driving the transaction with a synthetic `attempt_id` hit `StateNotConstructed { requires_constructor: true }`, surfaced as an opaque `'Unknown'` abort; (b) it entangled display state with the business commit. Moving "mark yourself WON" into the attempt's own workflow (a `per_workflow` inline write after the commit succeeds) fixed both.

**Expected.** A rule of thumb in `servicer-transaction.md`: a transaction's participants should be exactly the actors whose invariants it enforces; observer/display state belongs to the observer.

**Repro.** Not recorded beyond the description: drive the transaction with an `attempt_id` that names no constructed actor.

**Where in the skills.** `python/references/servicer-transaction.md`.

**Checked at 1.6.0.** `servicer-transaction.md` § Never and § Limits cover N-participant transactions, external calls and hot actors, but give no rule limiting participants to the actors whose invariants the transaction enforces. `errors.md` lists `StateNotConstructed { requires_constructor: true }` and `propagating as 'Unknown'` as separate rows; neither says the first can reach a caller as the second through a transaction. agentic-demo's learnings file repeats returns-desk's text for this section (it is the same file with §11 added); see returns-desk-02.

**Resolution (2026-10-10).** Rows in `servicer-transaction.md` § Errors you will see: `StateNotConstructed` reaching a caller as `'Unknown'` through a transaction (keep observers out of the participant set); the lock convoy from a burst of transactions on one hot actor (aggregators out, updated after commit); `PRESUMED_DEADLOCK` repeating behind a long-held lock (expunge and restart).
