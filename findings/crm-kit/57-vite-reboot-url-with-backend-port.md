---
id: crm-kit-57
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §8"
reboot_version: 1.6.0
severity: unrated
target: plugin
names:
  - web-app/references/react-client.md
  - web-app/SKILL.md
tags: [frontend, operations]
cluster: ""
still_applies: yes
status: Resolved
resolved_by: "build/templates/README.md § Files"
---

# Change VITE_REBOOT_URL together with the backend port, or a second frontend silently talks to the first backend

**What happened.** For a second copy, `VITE_REBOOT_URL` (`web/.env.development`) must change with the backend port; otherwise a second frontend silently talks to whichever backend holds the first port. The kit's override list adds: `web-app/SKILL.md` shows `VITE_REBOOT_URL=http://localhost:9991`, while the kit's `.rbtrc` pins `dev run --port=9989`; `.rbtrc` is the source of truth, so `web/.env.development` points at the port `.rbtrc` names.

**Expected.** Point `VITE_REBOOT_URL` at the port `.rbtrc` names.

**Repro.** Not recorded.

**Where in the skills.** `web-app/SKILL.md` (the kit's override list).

**Checked at 1.6.0.** `web-app/references/react-client.md` (~49) still shows `VITE_REBOOT_URL=http://localhost:9991`; `run/references/stop-restart-reset.md` § Never covers a second instance's directory and `.rbtrc` but not its frontend's `VITE_REBOOT_URL` (grep).

**Resolution (2026-10-10).** The scaffold (`copy.sh`) now gives every project a backend, dashboard and Vite port of its own: a set from a hash of the project name, the next free set when one of its ports is held, and the ports the stub `.rbtrc` already names on a merge; written into `.rbtrc` (`dev run --port`, `--dashboard-port`, `dashboard --port`, the MCP UI's `--frontend-host`), the Vite config, `.env.development` and `scripts/screenshots.py`. `copy.sh --ports <project>` prints the set for the dashboard skill, which starts on it; the run and dashboard skills check a port owner's directory before trusting what answers. `web/.env.development` and `.rbtrc` carry the same backend port from the start; `react-client.md` says a second copy changes both.
