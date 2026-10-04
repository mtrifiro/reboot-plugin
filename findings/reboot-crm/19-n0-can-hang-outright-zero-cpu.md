---
id: reboot-crm-19
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P1.10c"
reboot_version: 1.6.0
severity: red
target: framework
names: []
tags: [testing, operations]
cluster: "F"
still_applies: unknown
status: Open
resolved_by: ""
---

# -n0 can also hang outright, alive and at zero CPU

**What happened.** 2026-09-24, `pytest -n0 tests/crm_test.py` (one file, no parallelism) run from a script giving each file its own process. Twenty minutes in it had produced nothing: the pytest process was at 0.0% CPU with an `envoy` child idle for 9 minutes (so it stopped about nine minutes in, mid-file). The same file had completed in 9:18 earlier that day and a second session ran it to completion (412 passed, 15 failed) within the hour. Unlike reboot-crm-16 (`-n auto`) and reboot-crm-18 (a run that dies and is gone), this process stayed alive indefinitely. Cost: the sweep script gave each file a single `timeout 2400`, so the nine files behind it would never have run; a hang in the first file silently converts a full sweep into no sweep; five sweeps were abandoned in one day and the suite never completed once against a settled tree. Detection: `ps -o pid=,%cpu=,etime= -p $(pgrep -f "pytest tests/")`. Mitigation adopted: `scripts/suite.sh` gives each file its own timeout at about twice its measured runtime and reports `TIMED OUT` separately from `NO SUMMARY`.

**Expected.** Whatever reboot-crm-16 and reboot-crm-18 turn out to share; the author reads all three as the same placement-convergence race.

**Repro.** Not reliable: run `uv run pytest -n0 tests/crm_test.py` repeatedly on a machine with an `rbt dev run` alive and watch for a run whose CPU goes to zero.

**Where in the skills.** Not applicable to a skill.
