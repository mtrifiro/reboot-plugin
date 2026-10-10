---
id: returns-desk-10
project: returns-desk
source: "v 1.4.1 Reboot/Archive/returns-desk/docs/reboot-learnings.md §10 (platform observation)"
reboot_version: 1.4.0
severity: unrated
target: framework
names: []
tags: [operations, error-text]
cluster: ""
still_applies: yes
status: Resolved
resolved_by: "run/references/stop-restart-reset.md § Errors you will see"
---

# A task resumed after an unclean kill retries forever against the dead incarnation's internal port

**What happened.** The same `kill -9`ed instance also left a resumed task in a `ResetAborted: 'Unavailable' … 127.0.0.1:<old-port>` retry loop: a control-plane call pinned to the dead incarnation's internal port, retrying forever. A graceful SIGINT restart never showed this.

**Expected.** Possibly worth an upstream look: resumed tasks should re-resolve internal addresses after an unclean restart.

**Repro.** `kill -9` the worker tree mid-workflow, restart, watch the task log.

**Where in the skills.** Framework (file upstream). No skill names it.

**Checked at 1.6.0.** grep for `ResetAborted` across `skills/` finds nothing. Not checked against the 1.6.0 runtime.

**Resolution (2026-10-10).** Rows in `stop-restart-reset.md` § Errors you will see: `ResetAborted: 'Unavailable'` against a dead incarnation's port after `kill -9`; the dispatcher wedge (`ping timeout; will retry after backoff`) that survives restarts; the stale-address `Participant/Prepare` loop after a mid-commit kill. Each names the expunge as the reset.
