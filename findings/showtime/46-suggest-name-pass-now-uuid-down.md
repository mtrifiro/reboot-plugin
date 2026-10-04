---
id: showtime-46
project: showtime
source: "2026.08.18 reboot-findings.md Suggested skill improvements, bullet 3"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/patterns-common-gotchas.md
tags: [pattern, negative-space]
cluster: "E"
still_applies: unknown
status: Open
resolved_by: ""
---

# patterns-common-gotchas could name the 'pass now/uuid down' pattern

**What happened.** Non-deterministic values belong at the Transaction level, passed to Writers as request fields (effect validation re-runs writer bodies). Implied by gotcha 8 but the constructive pattern is not stated.

**Expected.** Name the constructive pattern.

**Repro.** Not recorded.

**Where in the skills.** `patterns-common-gotchas.md`.

**Checked at 1.6.0.** Did not find the pattern named in python/references/patterns-common-gotchas.md by grep (`now_ms`, `time.time` hits are only in servicer-workflow.md:664-678); gotcha wording not read in full.
