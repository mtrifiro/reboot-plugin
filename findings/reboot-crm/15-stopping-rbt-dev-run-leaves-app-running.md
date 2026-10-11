---
id: reboot-crm-15
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P1.9"
reboot_version: 1.6.0
severity: red
target: plugin
names:
  - run/SKILL.md
tags: [operations, negative-space, error-text]
cluster: "F"
still_applies: yes
status: Resolved
resolved_by: "run/references/stop-restart-reset.md § Do this"
---

# Stopping rbt dev run leaves the application running (orphans keep serving; test harness leaks Envoys too)

**What happened.** SIGTERM to `rbt dev run` (and its `uv run` parent) ended the dev loop but the application it started (three `backend/src/main.py` processes plus their envoy) stayed up with ppid 1, still listening, until killed by hand; this broke the next test run, which sat behind ports the orphans held. Seen 2026-09-23, the worse half: the orphan keeps serving. After `rbt dev run` was killed, `main.py` and Envoy stayed up for two hours bound to 9989, `curl /__/oauth/whoami` returned 200 throughout while the store underneath had been expunged, so every write failed while every read succeeded. It blocked recovery twice: first `cannot bind '0.0.0.0:9989': Address already in use`, then `Failed to open rocksdb ... LOCK: Resource temporarily unavailable`, neither naming the orphan. Three Envoys aged 2h04, 2h31 and 3h04 were found in one cleanup, and their accumulation produced the 0%-CPU hang in reboot-crm-19. Seen 2026-09-28: the test harness leaks Envoys too: three orphaned Envoys (ppid 1), 29 and 30 hours old, with configs in temp directories, each listening on three ports in the range new test servers draw from (51353-51416); whether a new test server could share a port with an orphan turns on `SO_REUSEPORT`, left at Envoy's platform default, untested.

**Expected.** The dev loop owns its application's process group and takes it down with it. Source fix list: (1) own the process group; (2) detect orphans on start, name the holder and its age (and consider refusing to serve reads from an application whose storage has gone away); (3) `run/SKILL.md` gains the recovery line (`ps -eo pid,ppid,command | grep main.py`, then kill) for the version that leaks today.

**Repro.** Start `uv run rbt dev run --no-chaos`, `pkill -f "rbt dev run"`, then `ps -eo pid,ppid,command | grep main.py`.

**Where in the skills.** `run/SKILL.md` (no stop/recovery section).

**Checked at 1.6.0.** `run/SKILL.md` has no stop, kill or orphan-recovery text (grep).
