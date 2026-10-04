---
id: theater-network-07
project: theater-network
source: "theater-network/docs/reboot-findings.md §7"
reboot_version: 1.4.0
severity: unrated
target: plugin
names:
  - python/references/testing-project-setup.md
  - python/references/testing-features.md
tags: [testing, operations]
cluster: "8.4"
still_applies: yes
status: Open
resolved_by: ""
---

# Debugging discipline that actually worked

**What happened.** Four practices: (1) bisect with a scratch test that boots progressively more of the app (four runs isolated what four theory-driven code changes had not); (2) always run `pytest -s` when something hangs, because the runtime logs the real error and its retry loop; (3) `PYTHONFAULTHANDLER=1` plus `timeout -s ABRT` dumps every thread's stack at a wedge, and an idle event loop means awaiting something that never arrives, so look upstream; (4) never trust an exit code from the end of a pipeline (`cmd | tail` reports tail's exit), which produced two false 'suite passed' reports.

**Expected.** Not recorded.

**Repro.** See the four practices.

**Where in the skills.** Proposal 8.4 'Dev-loop hygiene': a short `lifecycle-dev-loop.md`, `step: any`.

**Checked at 1.6.0.** No `pytest -s`, faulthandler or pipeline-exit-code guidance found in `python/references/testing-*.md` or elsewhere under `skills/`.
