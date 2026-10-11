---
id: reboot-crm-38
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P3.5"
reboot_version: 1.6.0
severity: yellow
target: framework
names:
  - dashboard/SKILL.md
tags: [operations, error-text]
cluster: "F"
still_applies: unknown
status: Resolved
resolved_by: "dashboard/SKILL.md § Known issues"
---

# The dashboard's call-graph analysis is stale after a restart, and blames the wrong thing

**What happened.** A fresh dashboard showed "code checked at 1:56 PM" from before its restart, drew methods deleted hours earlier, showed a new type with no edges, and printed "Your API files changed since the generated code was written ... Run `rbt generate`" although generate had already run. It re-ran only after another `rbt generate`, which also restarted the dev loop twice (three "Pipeline ready" lines): the watcher fires once per output directory. Seen again on a cold start: dashboard started at 17:13 reported "code checked at 3:51 PM" (84 minutes stale) although the generated files were newer by mtime than the API file; a manual `rbt generate` cleared it.

**Expected.** Fixes proposed: re-analyse on start; compare against API and servicer sources rather than generated-file mtimes (`rbt generate` leaves unchanged outputs untouched); debounce the watcher across one generate. The source: confident staleness is worse than saying it does not know.

**Repro.** Restart the dashboard against a running app after deleting methods; or cold-start the dashboard and backend within the same minute.

**Where in the skills.** `dashboard/SKILL.md` (no known-issues section).

**Checked at 1.6.0.** `dashboard/SKILL.md` has no mention of staleness or the banner (grep).
