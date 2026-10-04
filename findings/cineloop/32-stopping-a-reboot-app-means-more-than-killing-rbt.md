---
id: cineloop-32
project: cineloop
source: "cineloop/reboot-findings.md §21c (Part 4)"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - run/SKILL.md
tags: [operations, error-text]
cluster: "F"
still_applies: yes
status: Open
resolved_by: ""
---

# Stopping a Reboot app means more than killing rbt dev run (orphans hold the RocksDB lock)

**What happened.** Restart failed with `Failed to instantiate service: Failed to open rocksdb at '.rbt/dev/cineloop/p000000': IO error: While lock file: .rbt/dev/cineloop/p000000/LOCK: Resource temporarily unavailable`. `rbt dev run` supervises the app in separate child processes and killing the parent does not reap them; three orphaned `backend/src/main.py` processes were alive and one held the RocksDB lock. `lsof .rbt/dev/<app-name>/p000000/LOCK` names the culprit. A full local stop is three things: the supervisor (`pkill -f "<project>/.venv/bin/rbt dev run"`), the application processes (`pkill -f "<project>/backend/src/main.py"`), and the proxy fronting :9991 (`pkill -f "envoy-v"`). The failure mode is friendly: `rbt dev run` prints the error then sits in 'waiting for modification' rather than exiting; clearing the lock while it waits does nothing until a watched file is touched or it is restarted.

**Expected.** Add to `run/SKILL.md` a 'Stopping the app' section: killing the `rbt` parent alone leaves the app process and envoy behind; the orphan keeps the RocksDB lock so the next run fails with the lock error; stop all three (`pkill -f "rbt dev run"; pkill -f "backend/src/main.py"; pkill -f "envoy-v"`) and confirm `lsof .rbt/dev/<app-name>/p000000/LOCK` prints nothing. Matters most when restarting inside one session.

**Repro.** Kill `rbt dev run` and start it again.

**Where in the skills.** `run/SKILL.md` Stop / restart / reset section (proposal task F).

**Checked at 1.6.0.** `run/SKILL.md` covers starting only; no stop, pkill, LOCK or orphan guidance found (grep).
