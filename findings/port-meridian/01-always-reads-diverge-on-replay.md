---
id: port-meridian-01
project: port-meridian
source: "v 1.4.1 Reboot/port-meridian/docs/reboot-learnings 04.md §1"
reboot_version: 1.4.0
severity: unrated
target: plugin
names:
  - python/references/servicer-workflow-calls.md
tags: [negative-space, pattern]
cluster: ""
still_applies: yes
status: Open
resolved_by: ""
---

# .always() reads that feed later steps diverge on replay

**What happened.** The voyage workflow picked a berth candidate from `Harbor.ref(...).always().snapshot(context)` inside its `context.loop("Acquire berth")`, attempted `dock` with a `.per_iteration(...)` scope, and kept the winning `berth_id` in a local variable. On a dev-run restart mid-fleet the workflow replayed: the memoized `dock` returned its cached success, but the `.always()` snapshot re-read live state and produced a different candidate, so the local `berth_id` diverged from the berth the transaction had actually claimed. Ships then reported releasing the wrong berth, the render model's berths stayed "occupied" forever, and every later ship queued at anchorage indefinitely. Rule of thumb: a value read with `.always()` may differ between a run and its replay, so it must never flow into state reports, IDs or decisions that outlive the current step. Scope the read (`.per_iteration` / `.per_workflow`) if a later step depends on it, and after a contested transaction commits, re-derive the winner's identity from committed state (a memoized reader on the participant), never from the replayed local plan. Generalizes the returns-desk finding "drive post-commit phases from committed case state".

**Expected.** Wish: a dev-mode lint or runtime warning when an `.always()` result is passed as an argument to a scoped (memoized) call; the divergence is silent and only shows after a restart.

**Repro.** 3+ ships mid-lifecycle, `Ctrl-C` the backend while at least one ship is berthed and others are waiting, restart. Pre-fix, ships "cast off from" berths they never held.

**Where in the skills.** Not recorded.

**Checked at 1.6.0.** `python/references/servicer-workflow-calls.md` § Reboot calls: pick a scope describes `.always()` only as "never memoized; a live read on every wake" and its example reads config with it; grep of `python/references/` for `always()` found no warning against feeding an `.always()` result into a memoized call or a later step.
