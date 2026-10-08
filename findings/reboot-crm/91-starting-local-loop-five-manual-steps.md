---
id: reboot-crm-91
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md A.10"
reboot_version: 1.6.0
severity: yellow
target: primer
names:
  - run/SKILL.md
tags: [operations]
cluster: "F"
still_applies: unknown
status: Open
resolved_by: ""
---

# Starting the local loop is five manual steps

**What happened.** Check port 9989 for an orphaned backend (P1.9), start `rbt dev run`, start Vite, wait for "Pipeline ready", then touch the generated TypeScript in case Vite cached a half-written file. Background commands in the agent's harness also stop after two hours, so this recurs. Status: done 2026-10-04: `scripts/dev.sh` (`start`/`stop`/`status`) starts both servers detached; with it `scripts/test-feature.sh` and `scripts/where.py` replace common grep chains.

**Expected.** A `scripts/dev.sh` that does all five and is safe to run again.

**Repro.** Not recorded.

**Where in the skills.** `run/SKILL.md` (no stop/restart or orphan-clearing step).

**Reopened 2026-10-08.** Partly covered: `run/SKILL.md` § Before starting: is the port free? checks for an orphan on the port and starts the backend and frontend. Still missing: the two-hour limit on background commands, waiting for "Pipeline ready", touching the generated TypeScript in case Vite cached a half-written file, and a start script that is safe to run again.
