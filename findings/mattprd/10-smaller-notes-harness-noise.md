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
status: Open
resolved_by: ""
---

# Smaller notes: excepthook noise and duplicate allowed_origins warning

**What happened.** `Error in sys.excepthook: / Original exception was:` noise prints after every pytest run of the harness (teardown-time excepthook with no payload); harmless but alarming in CI logs. The `allowed_origins` warning prints twice at `rbt dev run` startup (once per consumer?); once would do.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.
