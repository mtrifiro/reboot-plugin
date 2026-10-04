---
id: reboot-crm-58
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P3.22"
reboot_version: 1.6.0
severity: yellow
target: plugin
names:
  - web-app/references/react-client.md
tags: [scaffold, frontend, error-text]
cluster: "B"
duplicate_of: reboot-air-141-07
still_applies: yes
status: Open
resolved_by: ""
---

# web-app Vite template uses process.env.PORT

**What happened.** `vite.config.ts` from `react-client.md` references `process`, which fails `tsc -b` with "Cannot find name 'process'" unless `@types/node` is added.

**Expected.** Drop the `process.env.PORT` lookup from the template (preferred: a dev-server port belongs on the command line), or add `@types/node` to the template's devDependencies. The template should type-check as generated. See also reboot-air-150 (proposal task B).

**Repro.** Scaffold a project from the web-app template and run `tsc -b`.

**Where in the skills.** `web-app/references/react-client.md` (`vite.config.ts` template).

**Checked at 1.6.0.** `web-app/references/react-client.md` line 58 still has `port: parseInt(process.env.PORT || "5173", 10)`; no `@types/node` in that file (the mcp-ui scaffold at `mcp-ui/references/react-scaffolding.md` line 39 does list it).
