---
id: showtime-36
project: showtime
source: "2026.08.18 reboot-findings.md #36"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/scheduling-recurring.md
tags: [negative-space]
cluster: "4.1"
still_applies: yes
status: Open
resolved_by: ""
---

# A tick chain dying is silent

**What happened.** No task-failure warning and nothing in the logs; the symptom is just 'the recurring thing stopped.' When debugging, count executions (the effect-validation 'Re-running <method>' log doubles as an execution marker, though it silences itself for 5 minutes) and suspect the guard condition before the scheduler.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded; `scheduling-recurring.md` is the natural home.

**Checked at 1.6.0.** python/references/scheduling-recurring.md has no note on silent chain death or how to debug it (read headings and grep for 'stop'/'silent').
