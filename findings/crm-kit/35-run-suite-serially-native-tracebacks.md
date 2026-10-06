---
id: crm-kit-35
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §6"
reboot_version: 1.6.0
severity: unrated
target: plugin
names:
  - python/references/testing-project-setup.md
tags: [testing, cost]
cluster: "D"
duplicate_of: reboot-crm-16
still_applies: no
status: Resolved
resolved_by: "python/references/testing-project-setup.md § Limits"
---

# Run the suite serially, one test file per process, with a timeout and --tb=native

**What happened.** `-n auto` and `-n4` hang at 0% CPU (one run in five). Serial runs still flake (a random `Method not found!` that passes alone), occasionally hang, and can die mid-file with no summary and exit 0. In `pytest.ini`: `addopts = -n0 --tb=native`, each file with a timeout of about twice its runtime. `--tb=native` matters because the generated `*_rbt.py` run to about 365k lines, and pytest's own tracebacks cost about 20 s per failure.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.

**Checked at 1.6.0.** `python/references/testing-project-setup.md` § Limits per the canonical item; `--tb=native` and the traceback cost were not found under `skills/` (grep `tb=native`).
