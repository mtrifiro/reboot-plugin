---
id: encore-05
project: encore
source: "v 1.4.1 Reboot/encore/docs/reboot-learnings 02.md §5"
reboot_version: 1.4.0
severity: unrated
target: plugin
names:
  - run/SKILL.md
tags: [operations, error-text]
cluster: "F"
duplicate_of: reboot-crm-15
still_applies: no
status: Resolved
resolved_by: "run/references/stop-restart-reset.md § Stop completely"
---

# Killing the rbt dev run supervisor orphans Envoy; kill the worker instead

**What happened.** Doing the kill-and-resume beat live in dev mode (the pytest harness version of the same kill is clean): `pkill -9` on the `rbt dev run` process leaves its Envoy sidecar alive and bound to the port, and the next `rbt dev run` crash-loops on `cannot bind: Address already in use` until the orphan is killed by hand. Killing only `backend/src/main.py` lets the supervisor restart the worker; the author calls that the correct on-stage kill.

**Expected.** Kill the python worker, not the supervisor, for a crash demo.

**Repro.** `pkill -9` the `rbt dev run` process, then start `rbt dev run` again.

**Where in the skills.** Not recorded.

**Checked at 1.6.0.** `run/references/stop-restart-reset.md` § Stop completely says SIGTERM/SIGKILL on `rbt dev run` orphans `main.py` and Envoy, and gives the ordered stop with an `lsof ... | xargs kill` step for whatever still holds the port. Killing only the worker as a deliberate crash demo is not described there (grep for "kill" in `testing-failure-recovery.md` found only harness kills).
