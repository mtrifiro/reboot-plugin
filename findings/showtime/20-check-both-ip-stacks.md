---
id: showtime-20
project: showtime
source: "2026.08.18 reboot-findings.md #20"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - run/SKILL.md
tags: [operations]
cluster: "F"
still_applies: yes
status: Open
resolved_by: ""
---

# Check both IP stacks before handing out a dev URL

**What happened.** Another process was bound to `[::1]:5173` while Vite (host:true) had `*:5173`; `curl localhost` hit the other server over IPv6 and returned its 404. Moving to a clean port beat killing someone else's process.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded (source frames it as a discovery; the `run` skill is the natural home).

**Checked at 1.6.0.** run/SKILL.md has no mention of IPv6/`[::1]` or checking for a process already bound to the dev port (grep for `::1`, `IPv6` found nothing).
