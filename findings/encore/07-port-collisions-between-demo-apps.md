---
id: encore-07
project: encore
source: "v 1.4.1 Reboot/encore/docs/reboot-learnings 02.md §6"
reboot_version: 1.4.0
severity: unrated
target: plugin
names:
  - python/references/lifecycle-rbtrc.md
tags: [operations]
cluster: "F"
duplicate_of: hotel-trial-02
still_applies: yes
status: Resolved
resolved_by: "build/templates/README.md § Files"
---

# Parallel demo apps collide on port 9991

**What happened.** Multiple Reboot demo apps on one machine each want `:9991`, and a stale Envoy from any of them squats the port across sessions. Encore pins `dev run --port=9995` in `.rbtrc` (and the Vite proxy targets it) so it can coexist with theater-network and port-meridian dev servers.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.

**Checked at 1.6.0.** `python/references/lifecycle-rbtrc.md` documents `--port=<n>` "off the default 9991, when another Reboot app holds it", and `run/SKILL.md` says to set `dev run --port=<port>` when the port is held by something else: both fix the clash after it happens. No skill assigns a project its own port up front (the open part of hotel-trial-02).

**Resolution (2026-10-10).** The scaffold (`copy.sh`) now gives every project a backend, dashboard and Vite port of its own: a set from a hash of the project name, the next free set when one of its ports is held, and the ports the stub `.rbtrc` already names on a merge; written into `.rbtrc` (`dev run --port`, `--dashboard-port`, `dashboard --port`, the MCP UI's `--frontend-host`), the Vite config, `.env.development` and `scripts/screenshots.py`. `copy.sh --ports <project>` prints the set for the dashboard skill, which starts on it; the run and dashboard skills check a port owner's directory before trusting what answers.
