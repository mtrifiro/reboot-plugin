---
id: findings-board-03
project: findings-board
source: "findings-board/FINDINGS.md § reboot.bdd, item 3"
reboot_version: 1.6.0
severity: yellow
target: bdd
names: []
tags: [testing, frontend, error-text]
cluster: ""
still_applies: unknown
status: Open
resolved_by: ""
---
# The test Vite gives a cold start 60 s, which a new dependency can exceed

**What happened.** The first web scenario after `npm install marked` failed with a bare `TimeoutError` from the `frontend` fixture: Vite was pre-bundling the new dependency (`SERVING_DEADLINE_SECONDS = 60` in `reboot/bdd/vite.py`). The rerun passed. The error doesn't say Vite was still starting or point at its log.

**Expected.** The timeout says Vite was still starting and points at its log.

**Repro.** Add a frontend dependency, then run a web scenario on a cold Vite cache.

**Where in the skills.** None.
