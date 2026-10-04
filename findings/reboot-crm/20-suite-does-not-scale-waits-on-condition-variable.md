---
id: reboot-crm-20
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P1.10d"
reboot_version: 1.6.0
severity: red
target: framework
names: []
tags: [testing, cost]
cluster: "D"
still_applies: unknown
status: Open
resolved_by: ""
---

# The suite does not scale across cores, because it is not waiting for a core

**What happened.** Measurement on 2026-09-24, 10-core machine (4 performance). Experiment 1: `pytest -m critical -n4`, 47 scenarios, five runs: four passed in 58-68 s, one hung at 0.0% CPU and was killed at 300 s; serial baseline 126 s (see reboot-crm-17). Experiment 2: all ten test files at once, each its own `pytest -n0` process: alone vs ten at once: chat_test 0:39 / 1:18, poggio_test 0:43 / 1:27, importing_web_test 1:01 / 1:11, research_test 3:25 / 5:12, power_mode_web_test 3:22 / 6:08, web_test 9:01 / 11:36, crm_test 9:18 / never finished (killed at 25:00); wall clock 25:00 with the largest file incomplete against about 30:00 serial with everything finishing. No port or state collisions, so concurrency itself is sound. Not CPU (ten concurrent files peaked at about 114% of a possible 1000%), not disk (`iostat` 288, 128, 164 tps at 4.9, 0.8, 1.1 MB/s); the worker sits in state `S` at 0.0% CPU and `sample` puts essentially every thread in `std::condition_variable::wait` / `__psynch_cvwait`: waiting for a signal that has not come. The author ties reboot-crm-16, -18 and -19 together: the startup/readiness path serialises and something in it can fail to signal; each scenario builds an application and spends most of its life blocked waiting for it to become usable. Consequences: more cores cannot help; more concurrency makes each file 1.5-2x slower (a serialised shared resource); duplicate runs cannot hedge it.

**Expected.** Whatever makes readiness deterministic (reboot-crm-18 proposes awaiting it before `up()` returns); the author expects it would take a half-hour suite to a quarter of that.

**Repro.** `time uv run pytest -m critical -n0` against `time uv run pytest -m critical -n4`, several times each, watching `ps -o stat=,%cpu=` on the python worker rather than the `timeout`/`uv` wrappers (both read 0.0% always).

**Where in the skills.** Not applicable to a skill.
