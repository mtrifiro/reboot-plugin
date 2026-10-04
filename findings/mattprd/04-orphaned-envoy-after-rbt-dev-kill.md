---
id: mattprd-04
project: mattprd
source: "2026.08.22 REBOOT_FINDINGS.md §4"
reboot_version: 1.4.1
severity: yellow
target: plugin
names:
  - run/SKILL.md
tags: [operations]
cluster: "F"
still_applies: yes
status: Open
resolved_by: ""
---

# Orphaned Envoy processes survive rbt dev termination

**What happened.** After killing another project's `rbt dev` (SIGTERM then SIGKILL on the `rbt` and `uv run` PIDs), its Envoy child kept running and kept port 9991 bound; found via `lsof` and killed by hand. `ps` also showed eight Envoy processes from old sessions' temp configs (`/var/folders/.../tmp*/envoy.yaml`) still alive, so the leak is chronic and feeds finding 3 (the next `rbt dev run` hits the stale envoy's port).

**Expected.** Source recommends tying Envoy's lifetime to the parent (process-group kill on shutdown, and/or Envoy-side parent-shutdown supervision) and an `rbt dev doctor`/cleanup command that lists and reaps orphaned envoys. Also (project architecture notes): `lsof -nP -iTCP:<port> -sTCP:LISTEN` and kill it.

**Repro.** Not recorded.

**Where in the skills.** Not recorded; `run` skill has no stop/cleanup section (proposal task F).

**Checked at 1.6.0.** run/SKILL.md has no stop/restart/orphan guidance; grep for `orphan`, `lsof` across skills finds nothing relevant.
