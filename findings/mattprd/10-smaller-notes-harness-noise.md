---
id: mattprd-10
project: mattprd
source: "2026.08.22 REBOOT_FINDINGS.md §Smaller notes"
reboot_version: 1.4.1
severity: unrated
target: framework
names: []
tags: [error-text, testing]
cluster: "8.4"
still_applies: unknown
status: Resolved
resolved_by: "python/references/testing-harness.md § Errors you will see"
---

# Smaller notes: excepthook noise and duplicate allowed_origins warning

**What happened.** `Error in sys.excepthook: / Original exception was:` noise prints after every pytest run of the harness (teardown-time excepthook with no payload); harmless but alarming in CI logs. The `allowed_origins` warning prints twice at `rbt dev run` startup (once per consumer?); once would do.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.

**Resolution (2026-10-10).** Rows in `testing-harness.md` § Errors you will see: a run that ends with no summary line and exit 0 died; the dual-stack port collisions on macOS and the `conftest.py` loopback setting; the `sys.excepthook` noise. `pytest-timeout` in the templates fails a hang on its own.
