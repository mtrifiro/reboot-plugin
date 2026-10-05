---
id: reboot-crm-16
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P1.10"
reboot_version: 1.6.0
severity: red
target: plugin
names:
  - python/references/testing-project-setup.md
  - python/references/testing-harness.md
tags: [testing, negative-space, cost]
cluster: "D"
still_applies: yes
status: Resolved
resolved_by: "python/references/testing-project-setup.md § Limits"
---

# Parallel harness runs hang, silently

**What happened.** The suite's `pytest.ini` ran `-n auto` (xdist). Twice on 2026-09-20 it hung: ten workers, only two of which ever started an envoy, all at zero CPU for eight minutes, and later a four-worker run that idled for eighteen. No error, no timeout, no output; a hung run looks exactly like a slow one. Each file alone with `-n0` passed every time (`crm_test.py` 181 scenarios in under four minutes, `poggio_test.py` in 35 s, `research_test.py` in 25 s). The first hang coincided with orphaned app processes from a killed `rbt dev run` (reboot-crm-15); the second did not. Since: the suite was split so each file is its own application and `-n auto` did not hang for a while (thirteen minutes down to 2:09), then hung again; `-n4` hung one run in five on 2026-09-24 (reboot-crm-17), so `pytest.ini` defaulted to `-n0` from 2026-09-25, but serial runs are not safe either (reboot-crm-18, -19, -20). 2026-09-29, after reboot-crm-28: six `-n4` runs of the critical and important tiers as shipped and six with servers on loopback (792 scenarios each): no run hung and no worker's server got another worker's port; then 8 parallel runs on loopback (including two rounds of the whole backend suite, 719 scenarios each, 407 s and 391 s against about 1,170 s serial) did not hang, so `pytest.ini` runs `-n4` from 2026-09-29. The hang itself was never explained: the author calls the default a bet that it was reboot-crm-28 or is now rare.

**Expected.** Either concurrent `Reboot()` harness applications on one machine work, or the harness fails fast when it cannot start one. Source fix list: (1) startup timeout naming what it waits for (port, lock, subprocess), recommended first; (2) investigate contention; (3) skill: `testing-project-setup.md` documents one `Reboot()` application per test file as the parallelisation unit and the `-n0` one-file-at-a-time fallback.

**Repro.** `uv run pytest -m "not browser" -n 4` in the CRM repo; compare `uv run pytest tests/crm_test.py -n0`.

**Where in the skills.** `python/references/testing-project-setup.md`.

**Checked at 1.6.0.** No xdist, `-n0` or one-application-per-file guidance in `testing-project-setup.md` or `testing-harness.md` (grep). Hang itself is runtime/harness behaviour.
