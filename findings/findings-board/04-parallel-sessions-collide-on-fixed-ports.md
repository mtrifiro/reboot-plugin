---
id: findings-board-04
project: findings-board
source: "findings-board/FINDINGS.md § Plugin skills, item 1"
reboot_version: 1.6.0
severity: green
target: plugin
names:
  - run/SKILL.md
  - dashboard/SKILL.md
tags: [operations]
cluster: ""
still_applies: unknown
status: Resolved
resolved_by: "build/templates/README.md § Files"
---
# Two agent sessions on one machine collide on ports the plan fixed

**What happened.** A parallel session building a copy of this app from the same plan took the same dashboard (9941) and Vite (5160) ports. The dashboard skill's Step 3 caught it (`lsof` + `cwd`), but the other session's agent read our dashboard as its own. Moved this app's Vite to 5165. Not a framework bug.

**Expected.** The `run` and `dashboard` skills check a port's owner's cwd before trusting what answers on it.

**Repro.** Build two copies of one app from the same plan in two sessions on one machine.

**Where in the skills.** `skills/run/SKILL.md`, `skills/dashboard/SKILL.md`.

**Resolution (2026-10-10).** The scaffold (`copy.sh`) now gives every project a backend, dashboard and Vite port of its own: a set from a hash of the project name, the next free set when one of its ports is held, and the ports the stub `.rbtrc` already names on a merge; written into `.rbtrc` (`dev run --port`, `--dashboard-port`, `dashboard --port`, the MCP UI's `--frontend-host`), the Vite config, `.env.development` and `scripts/screenshots.py`. `copy.sh --ports <project>` prints the set for the dashboard skill, which starts on it; the run and dashboard skills check a port owner's directory before trusting what answers. Two copies of one project get two sets, since the second finds the first's ports held.
