---
id: agentic-demo-06
project: agentic-demo
source: "v 1.4.1 Reboot/Archive/agentic-demo/docs/reboot-learnings.md §7 (follow-up)"
reboot_version: 1.4.0
severity: unrated
target: plugin
names:
  - python/references/servicer-workflow.md
  - python/references/patterns-idempotency.md
tags: [pattern, negative-space, testing]
cluster: ""
duplicate_of: returns-desk-06
still_applies: yes
status: Open
resolved_by: ""
---

# An effect-validation replay re-submits a workflow's per_workflow transaction after it completed; make terminal handling idempotent

**What happened.** Live app, `rbt dev run` with effect validation on: the replay also re-fires `per_workflow`-scoped transaction calls. Observed in the browser: a race-scenario attempt committed its refund and completed, then a validation replay re-submitted "Commit proposal 1" against the now-resolved case, appending a spurious "duplicate attempt suppressed" event to real state and (without a guard) demoting the WON attempt to LOST. The author takes this to explain why theater-network runs dev with `--effect-validation=disabled`, and instead hardened the app to be correct under re-fire: (1) `CASE_ALREADY_RESOLVED` where the recorded winner is yourself is idempotent success, never a duplicate; (2) terminal display states are monotonic, a writer refuses to demote WON/COMPLETED to LOST; (3) narrative events ("reconciled") are gated on the workflow having actually observed the precondition (a timeout), not on provider response flags a replay can reproduce.

**Expected.** Not recorded as a skill change; the author calls hardening for re-fire the better posture and a reusable pattern.

**Repro.** Not recorded beyond the description: a race scenario under `rbt dev run` with effect validation on.

**Where in the skills.** `python/references/servicer-workflow.md`.

**Checked at 1.6.0.** `servicer-workflow.md` § Limits says effect validation re-runs memoized `at_least_once` callables and the last loop iteration; `patterns-idempotency.md` § Limits says it runs every writer and transaction body twice. Neither says a completed workflow's `per_workflow` transaction call can be re-submitted against state its first run already changed, and none of the three hardening rules appears (grep for monoton, demot, winner found nothing relevant). agentic-demo's learnings file repeats returns-desk's text for this section (it is the same file with §11 added); see returns-desk-06.
