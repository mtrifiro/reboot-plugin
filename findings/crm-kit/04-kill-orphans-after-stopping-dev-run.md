---
id: crm-kit-04
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §1"
reboot_version: 1.6.0
severity: unrated
target: plugin
names:
  - run/references/stop-restart-reset.md
tags: [operations, error-text]
cluster: "F"
duplicate_of: reboot-crm-15
still_applies: no
status: Resolved
resolved_by: "run/references/stop-restart-reset.md § Do this"
---

# Stopping rbt dev run leaves main.py and its Envoy alive; kill the orphans before any restart or test run

**What happened.** SIGTERM leaves `main.py` and its Envoy alive (ppid 1) on the ports, and each watch-restart leaks an Envoy. An orphan answers reads while every write fails. The next start then dies with `Address already in use` or `rocksdb ... LOCK: Resource temporarily unavailable`, or tests hang. Check: `ps -eo pid,ppid,command | grep -E 'main\.py|envoy' | grep -v grep` must be empty.

**Expected.** Kill orphans after stopping `rbt dev run`, before any restart or test run.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.

**Checked at 1.6.0.** `run/references/stop-restart-reset.md` § Do this ("Stop completely") gives the stop-and-verify procedure; resolved for the canonical item.
