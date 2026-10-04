---
id: showtime-21
project: showtime
source: "2026.08.18 reboot-findings.md #21"
reboot_version: 1.4.1
severity: unrated
target: positive
names: []
tags: [frontend]
cluster: "8.4"
still_applies: unknown
status: Open
resolved_by: ""
---

# Generated React client types catch real mistakes at npm run build

**What happened.** Hooks, camelCase renames and `{response, aborted}` mutation results all type-checked without opening the generated file, as the skill promises.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded (a thing that worked; keep it documented).
