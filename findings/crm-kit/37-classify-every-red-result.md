---
id: crm-kit-37
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §6"
reboot_version: 1.6.0
severity: unrated
target: framework
names:
  - python/references/lifecycle-dev-loop.md
tags: [testing, operations]
cluster: "4.4"
duplicate_of: reboot-crm-18
still_applies: no
status: Resolved
resolved_by: "python/references/testing-harness.md § Errors you will see"
---

# Classify every red result: no summary line with exit 0 means the run died, not that it passed

**What happened.** A failed assertion is real. A one-off `Method not found!` is a race, so rerun once. No summary line with exit 0 means the run died, **not that it passed**. Status `S` at 0.0% CPU on the `bin/python ... pytest` process (not on the `uv` or `timeout` wrappers) means it hung: kill it.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.

**Checked at 1.6.0.** `python/references/lifecycle-dev-loop.md` § Never ("Calling a run with no summary line a pass") and § Do this (timeout; `ps -o pid=,%cpu=,etime=` to tell alive from idle).

**Resolution (2026-10-10).** Rows in `testing-harness.md` § Errors you will see: a run that ends with no summary line and exit 0 died; the dual-stack port collisions on macOS and the `conftest.py` loopback setting; the `sys.excepthook` noise. `pytest-timeout` in the templates fails a hang on its own.
