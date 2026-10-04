---
id: showtime-48
project: showtime
source: "2026.08.18 reboot-findings.md Suggested skill improvements, bullet 5"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/react-generated-client.md
tags: [pattern, frontend]
cluster: "E"
still_applies: yes
status: Open
resolved_by: ""
---

# react-generated-client.md could sketch the optimistic-override pattern

**What happened.** 'Live updates are free' is documented; the natural companion (paint expected state on click, drop the override when the pushed snapshot matches, revert on `aborted`) is the idiom every interactive Reboot UI wants, about 20 lines once known.

**Expected.** A short example, to stop people shipping round-trip-gated clicks (or bolting on a refetch library).

**Repro.** Not recorded.

**Where in the skills.** `react-generated-client.md`.

**Checked at 1.6.0.** Same as showtime-22: no optimistic pattern in python/references/react-generated-client.md.
