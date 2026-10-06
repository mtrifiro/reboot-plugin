---
id: agentic-demo-10
project: agentic-demo
source: "v 1.4.1 Reboot/Archive/agentic-demo/docs/reboot-learnings.md §10 (platform observation)"
reboot_version: 1.4.0
severity: unrated
target: framework
names: []
tags: [operations, error-text]
cluster: ""
duplicate_of: returns-desk-10
still_applies: yes
status: Open
resolved_by: ""
---

# A task resumed after an unclean kill retries forever against the dead incarnation's internal port

**What happened.** The same `kill -9`ed instance also left a resumed task in a `ResetAborted: 'Unavailable' … 127.0.0.1:<old-port>` retry loop: a control-plane call pinned to the dead incarnation's internal port, retrying forever. A graceful SIGINT restart never showed this.

**Expected.** Possibly worth an upstream look: resumed tasks should re-resolve internal addresses after an unclean restart.

**Repro.** `kill -9` the worker tree mid-workflow, restart, watch the task log.

**Where in the skills.** Framework (file upstream). No skill names it.

**Checked at 1.6.0.** grep for `ResetAborted` across `skills/` finds nothing. Not checked against the 1.6.0 runtime. agentic-demo's learnings file repeats returns-desk's text for this section (it is the same file with §11 added); see returns-desk-10.
