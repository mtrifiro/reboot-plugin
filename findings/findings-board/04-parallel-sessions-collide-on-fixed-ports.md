---
id: findings-board-04
project: findings-board
source: "findings-board/FINDINGS.md § Plugin skills, item 1"
reboot_version: 1.6.0
severity: green
target: plugin
names:
  - skills/run/SKILL.md
  - skills/dashboard/SKILL.md
tags: [operations]
cluster: ""
still_applies: unknown
status: Open
resolved_by: ""
---
# Two agent sessions on one machine collide on ports the plan fixed

**What happened.** A parallel session building a copy of this app from the same plan took the same dashboard (9941) and Vite (5160) ports. The dashboard skill's Step 3 caught it (`lsof` + `cwd`), but the other session's agent read our dashboard as its own. Moved this app's Vite to 5165. Not a framework bug.

**Expected.** The `run` and `dashboard` skills check a port's owner's cwd before trusting what answers on it.

**Repro.** Build two copies of one app from the same plan in two sessions on one machine.

**Where in the skills.** `skills/run/SKILL.md`, `skills/dashboard/SKILL.md`.
