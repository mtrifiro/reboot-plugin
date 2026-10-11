---
id: showtime-35
project: showtime
source: "2026.08.18 reboot-findings.md #35"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/scheduling-recurring.md
tags: [pattern, negative-space]
cluster: "E"
still_applies: yes
status: Resolved
resolved_by: "python/references/scheduling-recurring.md § Never"
---

# Generation tokens make recurring chains restart-safe; the flag writer must never overwrite a live generation

**What happened.** The `scheduling-recurring.md` stop-flag pattern extends to stop/restart: store a per-key generation token and have each tick check its own token before acting/rescheduling. Subtle bug caught by a test: if the 'set active' writer overwrites an existing token, a redundant start orphans the running chain (the pending tick sees a token it doesn't own and dies, while the caller, seeing `was_active=True`, never schedules a replacement).

**Expected.** Write the token only when transitioning inactive to active.

**Repro.** Not recorded.

**Where in the skills.** `scheduling-recurring.md`.

**Checked at 1.6.0.** python/references/scheduling-recurring.md describes a stop flag (`active`) and `start`/`tick`/`run` shape (lines 109-161) but no generation token or inactive-to-active-only rule.
