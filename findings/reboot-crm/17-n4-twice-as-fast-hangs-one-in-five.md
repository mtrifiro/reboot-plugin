---
id: reboot-crm-17
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P1.10 measured, 2026-09-24"
reboot_version: 1.6.0
severity: unrated
target: framework
names: []
tags: [testing, cost]
cluster: "D"
still_applies: unknown
status: Resolved
resolved_by: "build/templates/README.md § Files"
---

# P1.10 measured, 2026-09-24: -n4 is twice as fast and hangs one run in five

**What happened.** A measurement on reboot-crm-16, not a separate finding. `pytest -m critical -n4`, 47 scenarios, 10-core machine with an `rbt dev run` alive, five runs: 58.0 s, 62.2 s, 67.9 s, 63.7 s, and one that hung (controller and all four workers at 0.0% CPU, killed at 300 s). Serial `-n0` baseline for the same 47: 126 s and 136 s, no hang. `-n4` halves the run (63 s against 126 s, at 220% CPU on a box 96% idle during a serial run), but a hung run costs its timeout plus a retry, so the expected cost is `0.8 x 63 + 0.2 x (300 + 63) = about 123 s` against 126 s serial, with far worse variance. The author's conclusion: parallelism is not worth it until the hang is fixed. The hang is not at start-up (four runs of the same 47 completed first); consistent with reboot-crm-19 (hang mid-file under `-n0`) and with the placement-convergence mechanism in reboot-crm-18. Sample size n=5, one machine, one tier, dev loop alive throughout; the first run passing is what prompted the other four.

**Expected.** Fixing the hang would make parallelism a genuine 2x on ten idle cores.

**Repro.** Not recorded beyond the measurement.

**Where in the skills.** Not applicable to a skill.

**Resolution (2026-10-10).** The templates' dev group has `pytest-timeout` and `pytest.ini` sets `timeout = 300`, setup included, so a hung run or a hung `Reboot().up()` fails on its own instead of sitting at zero CPU; `scripts/test.sh` runs the suite by area, and `full` once before a handoff.
