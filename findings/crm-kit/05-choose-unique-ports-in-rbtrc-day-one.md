---
id: crm-kit-05
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §1"
reboot_version: 1.6.0
severity: unrated
target: plugin
names:
  - python/references/lifecycle-rbtrc.md
  - run/SKILL.md
  - dashboard/SKILL.md
tags: [operations]
cluster: "F"
duplicate_of: hotel-trial-02
still_applies: yes
status: Resolved
resolved_by: "build/templates/README.md § Files"
---

# Choose unique ports in .rbtrc on day one; .rbtrc flags cannot be overridden and another app's dashboard answers on 9871

**What happened.** Rule: set `dev run --port=`, `dev run --dashboard-port=` and `dashboard --port=` in `.rbtrc` on day one. A flag set in `.rbtrc` cannot be overridden on the command line ("the flag '--port' was set multiple times ... including in the `.rbtrc` file"). Another Reboot app on the default dashboard port 9871 shows its models under your URL. `rbt dev` state is per directory, so a second instance needs its own directory with its own `.rbtrc`.

**Expected.** Unique ports pinned in `.rbtrc` from the start.

**Repro.** Not recorded.

**Where in the skills.** Not named by the source.

**Checked at 1.6.0.** `python/references/lifecycle-rbtrc.md` § Limits states `.rbtrc` flags cannot be overridden; `dashboard/SKILL.md` Step 3 warns 9871 may belong to another project; `run/references/stop-restart-reset.md` § Never covers the second instance. Nothing assigns distinct ports when a project is created (same gap as hotel-trial-02).

**Resolution (2026-10-10).** The scaffold (`copy.sh`) now gives every project a backend, dashboard and Vite port of its own: a set from a hash of the project name, the next free set when one of its ports is held, and the ports the stub `.rbtrc` already names on a merge; written into `.rbtrc` (`dev run --port`, `--dashboard-port`, `dashboard --port`, the MCP UI's `--frontend-host`), the Vite config, `.env.development` and `scripts/screenshots.py`. `copy.sh --ports <project>` prints the set for the dashboard skill, which starts on it; the run and dashboard skills check a port owner's directory before trusting what answers.
