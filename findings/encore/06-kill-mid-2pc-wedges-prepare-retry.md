---
id: encore-06
project: encore
source: "v 1.4.1 Reboot/encore/docs/reboot-learnings 02.md §5"
reboot_version: 1.4.0
severity: unrated
target: plugin
names:
  - run/references/stop-restart-reset.md
tags: [operations, negative-space, error-text]
cluster: ""
still_applies: yes
status: Resolved
resolved_by: "run/references/stop-restart-reset.md § Errors you will see"
---

# Killing the worker mid-2PC wedges a durable Prepare retry loop that only expunge clears

**What happened.** After a dev-mode kill-and-resume, the resumed checkout completed correctly (exactly one charge; the app-level guarantee held), but the dev runtime kept retrying a `/rbt.v1alpha1.Participant/Prepare` against the dead worker's address (`UNAVAILABLE ... 0.0.0.0:<stale-port>`), and later external writers to the affected actor failed with the same error. It survives clean restarts; `rbt dev expunge` is the only reset. The author places it in the same family as agentic-demo's dispatcher-wedge finding. Practical rule: reset with expunge between kill-demo runs.

**Expected.** Not recorded beyond the practical rule.

**Repro.** Kill the python worker while a checkout transaction is in two-phase commit under `rbt dev run`, let it resume, then call a writer on a participating actor.

**Where in the skills.** Not recorded.

**Checked at 1.6.0.** Grep of `skills/` for `Participant/Prepare`, `stale`, `wedge` and `2PC` found only `servicer-transaction.md` (2PC participants and colliding prepares) and `lifecycle-dev-loop.md` (stack dumps for a wedge); `run/references/stop-restart-reset.md` § Reset dev state (expunge) lists when to expunge but not a stale-address Prepare loop after a mid-commit kill.

**Resolution (2026-10-10).** Rows in `stop-restart-reset.md` § Errors you will see: `ResetAborted: 'Unavailable'` against a dead incarnation's port after `kill -9`; the dispatcher wedge (`ping timeout; will retry after backoff`) that survives restarts; the stale-address `Participant/Prepare` loop after a mid-commit kill. Each names the expunge as the reset.
