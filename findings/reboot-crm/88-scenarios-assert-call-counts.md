---
id: reboot-crm-88
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md A.7"
reboot_version: 1.6.0
severity: yellow
target: primer
names:
  - python/references/testing-features.md
tags: [testing, pattern]
cluster: "E"
still_applies: unknown
status: Open
resolved_by: ""
---

# Scenarios assert call counts, so an unrelated change breaks dozens

**What happened.** "Perplexity was asked 9 times in all" broke when new accounts began getting their About (a scan and seven pages) instead of one brief: thirty-five scenario edits, most in features about leads and contacts that never mentioned accounts. Status: done 2026-10-04: `research_test` counts by kind ("asked for 2 briefs on people", "... company briefs", "... template pages", "... signal scans").

**Expected.** Steps that count by kind ("asked for 1 brief on a person", "asked for no company research") so a scenario breaks only when the behaviour it is about changes.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.
