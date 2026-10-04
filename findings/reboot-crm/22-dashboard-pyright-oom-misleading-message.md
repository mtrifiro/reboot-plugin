---
id: reboot-crm-22
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P1.12"
reboot_version: 1.6.0
severity: red
target: framework
names:
  - dashboard/SKILL.md
tags: [operations, error-text, cost]
cluster: "F"
still_applies: yes
status: Open
resolved_by: ""
---

# The dashboard's pyright runs out of heap on a mid-sized app, and the page blames the developer's generated code

**What happened.** The dashboard's Models page permanently showed "Your application imports generated code that does not exist yet, so the static call graph anaysis [sic] cannot be done. Run `rbt generate`" with status `CODE NOT CHECKED YET`, though `rbt generate` had just run; re-running it, restarting the dashboard and deleting its state changed nothing. The real failure is only in the dashboard's own log: `RuntimeError: pyright exited` / `Task 'rbt.dashboard.v1.Dashboard.WatchCode' failed with SystemAborted ... will retry after backoff`. The pyright language server is killed by Node's default old-space limit partway through the walk; on this app (14 state types, about 180 methods, `backend/api` holding the whole generated tree, 27 MB of generated Python plus about 9 kLOC of servicers) the `nodejs_wheel` Node process reached 4.1 GB RSS and died three times, each retry starting cold. `needs_generate_reason` compares `state.api_digests` against `state.generated`, which the code walk writes, so when pyright dies every API module looks `MISSING`. Outside fix: `NODE_OPTIONS="--max-old-space-size=12288" rbt dashboard` (past 4.1 GB with no exit; 5.2 GB and climbing). Also seen: the dashboard's durable watch tasks survive the app they watch: after `rbt dev expunge` and a restart of `rbt dev run` the dashboard kept retrying the old dev run's internal address forever (`Dashboard.WatchApi` failed with `ResetAborted ... Connection refused`); restarting the dashboard does not clear it, deleting `.rbt/dashboard` does; `rbt dev expunge --application-name=dashboard` is refused when `.rbtrc` already carries a `dev expunge --application-name=` line ("the flag '--application-name' was set multiple times"), and there is no command-line override of an `.rbtrc` value.

**Expected.** Source suggestions: set `--max-old-space-size` when the dashboard spawns pyright; say "the code analysis did not finish (pyright exited)" instead of "your generated code does not exist" (`MISSING` cannot distinguish no module from no walk completed); surface the retry in the status rail.

**Repro.** An app whose generated directory is large enough that pyright's analysis exceeds about 4 GB; start `rbt dashboard` without `NODE_OPTIONS`, open Models, watch the log.

**Where in the skills.** `dashboard/SKILL.md` (no known-issues section). Related to reboot-air-150-12 and student-system-10.

**Checked at 1.6.0.** `dashboard/SKILL.md` has no mention of pyright, memory or `NODE_OPTIONS`.
