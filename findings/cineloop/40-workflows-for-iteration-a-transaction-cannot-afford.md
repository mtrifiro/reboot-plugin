---
id: cineloop-40
project: cineloop
source: "cineloop/reboot-findings.md §30 (Part 4)"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/servicer-transaction.md
  - python/references/servicer-workflow.md
tags: [cost, pattern]
cluster: "D"
still_applies: yes
status: Resolved
resolved_by: "python/references/servicer-transaction.md § Never; python/references/patterns-load-and-benchmarking.md § Never; python/references/servicer-workflow-declare.md § Scales as"
---

# Workflows are for iteration a transaction cannot afford (Reset All over 48 showings)

**What happened.** `Reset All` touches 48 showings. One transaction over 48 showings makes every showing, order and the admin actor participants in a single two-phase commit, which is what stalled the test suite earlier. A workflow that iterates does one small transaction per auditorium. Every call inside is Reboot-internal and so carries a scope, not an idempotency key: `await Admin.ref().per_workflow(f"Reset {showing_id}").reset_showing(context, showing_id=showing_id)`. `.per_workflow(alias)` memoizes per step so a restart resumes rather than re-resets finished auditoriums; aliases derived from showing IDs are replay-stable and distinct per step. Progress reporting fell out for free: the workflow writes `reset_done` into its own actor's state and the panel reads it through a reactive reader (no polling).

**Expected.** Heuristic from the source: if the work is 'do this to N things' and N is more than a handful, the transaction boundary belongs around each thing, not around the loop.

**Repro.** `Reset All` as one transaction over 48 showings stalled the test suite.

**Where in the skills.** `servicer-transaction.md` / `servicer-workflow.md` (Scales as); see theater-network-14 and -20 for numbers on the same rule.

**Checked at 1.6.0.** `servicer-transaction.md` does not state that a transaction's cost is its participant set or recommend iterating in a workflow for N-more-than-a-handful; `servicer-workflow.md` documents `.per_workflow` mechanics only.
