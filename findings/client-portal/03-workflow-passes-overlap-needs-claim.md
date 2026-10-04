---
id: client-portal-03
project: client-portal
source: "client-portal/reboot-findings.md §3"
reboot_version: 1.6.0
severity: unrated
target: plugin
names:
  - python/references/servicer-workflow.md
  - python/references/scheduling-recurring.md
tags: [pattern, negative-space, testing]
cluster: "E"
still_applies: yes
status: Open
resolved_by: ""
---

# Workflow passes overlap unless something stops them

**What happened.** Cost: sixteen concurrent `Portal.Sync` tasks on one portal. The chain `tick -> sync -> tick` never overlaps itself because `_finish` schedules the next pass only when the current one ends, but `request_sync` (the admin button) and `ensure_syncing` (startup) each schedule a pass unconditionally and nothing consulted whether one was already running: `16 distinct UUIDs for Task 'portal.v1.Portal.Sync', 8-9 failures each`. `tests/vault_sync.feature` had asserted "Two sync passes over one portal never overlap" since before any of this, an unenforced rule. The author's fix: a claim. `sync_running_since` (the pass's own start time) is written in the same atomic check-and-set that marks the chain alive, and a pass that finds the portal claimed returns without calling `_finish` (calling it would append a fictitious run and schedule an extra tick).

**Expected.** If a workflow can be started from more than one place, give it a claim.

**Repro.** Not recorded.

**Where in the skills.** `python/references/servicer-workflow.md` and `python/references/scheduling-recurring.md` (no pattern for workflows started from two places).

**Checked at 1.6.0.** No reference describes a claim for workflows started from several places; `servicer-workflow.md` lines ~1154-1190 cover claiming a slot for a different purpose (`wait`/`until` with `Service.ref().write`).
