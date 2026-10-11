---
id: returns-desk-11
project: returns-desk
source: "v 1.4.1 Reboot/Archive/returns-desk/docs/reboot-learnings.md §10 (operational)"
reboot_version: 1.4.0
severity: unrated
target: plugin
names:
  - run/SKILL.md
tags: [operations]
cluster: ""
still_applies: no
status: Resolved
resolved_by: "run/references/stop-restart-reset.md § Stop completely"
---

# pkill patterns must be surgical: workers have no rbt in their command line, and the project name matches Vite too

**What happened.** The app's worker processes are `python backend/src/main.py`, with no "rbt" or "reboot" in the command line, and a path-based pattern (`-f returns-desk`) also kills the Vite dev server, whose cwd contains the project name.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not named by the source; the `run` skill owns stopping.

**Checked at 1.6.0.** `run/references/stop-restart-reset.md` § Stop completely names the worker as `python <project>/backend/src/main.py` and stops it with `pkill -f "$PWD/backend/src/main.py"` and the supervisor with `pkill -INT -f "$PWD/.venv/bin/rbt dev run"`, exact paths rather than a project-name pattern.
