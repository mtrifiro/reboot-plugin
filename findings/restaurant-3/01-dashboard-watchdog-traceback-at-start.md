---
id: restaurant-3-01
project: restaurant-3
source: "restaurant-3/FINDINGS.md § Framework, item 1"
reboot_version: 1.6.0
severity: green
target: framework
names:
  - dashboard/SKILL.md
tags: [operations, error-text]
cluster: ""
still_applies: yes
status: Open
resolved_by: ""
---
# `rbt dashboard` logs a watchdog traceback at start but serves fine

**What happened.** `uv run rbt dashboard` printed `RuntimeError: Cannot add watch <ObservedWatch: path='.../restaurant-3', is_recursive=True> - it is already scheduled` from `watchdog/observers/fsevents.py`, then `Your dashboard is at http://127.0.0.1:9851/` and the page served normally.

**Expected.** No traceback on a clean start.

**Repro.** A fresh project with the dashboard stub `.rbtrc`, `uv run rbt dashboard` on macOS.

**Where in the skills.** `dashboard/SKILL.md` Known issues does not list it.
