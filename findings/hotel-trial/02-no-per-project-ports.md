---
id: hotel-trial-02
project: hotel-trial
source: "hotel-app A/B build trial, 2026-10-05; reboot-crm/.rbtrc; client-portal-09"
reboot_version: 1.6.0
severity: yellow
target: plugin
names:
  - run/SKILL.md
  - dashboard/SKILL.md
  - build/templates/web-app/web/vite.config.ts
tags: [operations, scaffold]
cluster: "F"
still_applies: yes
status: Open
resolved_by: ""
---

# Every project starts on the same ports; clashes are fixed by hand after they happen

**What happened.** On a machine running several Reboot apps, every new
project takes the defaults (backend `9991`, dashboard `9871`, the
template's Vite `5273`), so each one after the first collides and is
moved by hand. In the hotel trial the new-skills build's dashboard
failed with `cannot bind '0.0.0.0:9872': Address already in use`
(another project's dashboard) and the agent moved it to `9875`; both
trial builds also had to run one after the other because both wanted
`9991`. Other projects show the same pattern: reboot-crm's `.rbtrc` pins
`dev run --port=9989` with the comment "other Reboot projects on this
machine use 9991-9998", and client-portal ran on `9999` for the same
reason (client-portal-09).

**Expected.** The skills give a new project its own free ports up front:
at scaffold or first run, pick a backend, dashboard and Vite port that
nothing is listening on, write them into `.rbtrc`
(`dev run --port=`, `dev run --dashboard-port=`, `dashboard --port=`)
and `vite.config.ts`, and point `VITE_REBOOT_URL` and `allowed_origins`
at them. The `run` skill's existing "is the port free?" check would
then rarely fire.

**Repro.** Run any Reboot app, then build a second one with the
`web-app` skill in another directory.

**Where in the skills.** `run/SKILL.md` § "Before starting: is the port
free?" reacts to a clash; `build/SKILL.md` Step 2 (project shell) and
the templates fix the defaults. Related, resolved: mattprd-03 (the
clash error reads as an Envoy bug), client-portal-09.

**Checked at 1.6.0.** `run/SKILL.md` handles a taken port when it is
found; nothing assigns distinct ports when a project is created.
