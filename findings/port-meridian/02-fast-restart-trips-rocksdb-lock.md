---
id: port-meridian-02
project: port-meridian
source: "v 1.4.1 Reboot/port-meridian/docs/reboot-learnings 04.md §2"
reboot_version: 1.4.0
severity: unrated
target: plugin
names:
  - run/SKILL.md
tags: [operations, error-text]
cluster: ""
still_applies: no
status: Resolved
resolved_by: "run/references/stop-restart-reset.md § Restart"
---

# Restarting rbt dev run too fast trips the RocksDB LOCK

**What happened.** `kill -INT` on the dev run followed immediately by a new one can crash the new process once with `Failed to open rocksdb ... LOCK: Resource temporarily unavailable`, because the old process has not fully released the lock. The supervisor retries and recovers. For a live demo, wait about 2 s between SIGINT and relaunch.

**Expected.** Not recorded.

**Repro.** `kill -INT` the `rbt dev run` process and start a new one immediately.

**Where in the skills.** Not recorded.

**Checked at 1.6.0.** `run/references/stop-restart-reset.md` § Restart step 1: stop completely and wait until the verify step prints nothing, since two `rbt dev run`s over one state directory fight over the RocksDB lock. Its errors table attributes the LOCK error to an orphaned `main.py`; the self-recovering, slow-release case here is not named separately. Related to reboot-crm-15 (orphan holds the lock), a different cause.
