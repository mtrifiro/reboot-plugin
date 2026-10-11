---
id: crm-kit-72
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §11"
reboot_version: 1.6.0
severity: unrated
target: plugin
names:
  - web-app/references/react-client.md
tags: [scaffold, frontend, error-text]
cluster: "B"
duplicate_of: reboot-air-141-07
still_applies: no
status: Resolved
resolved_by: "web-app/references/react-client.md § Never"
---

# web-app react-client.md's Vite config uses process.env.PORT, which fails tsc -b

**What happened.** Its Vite config's `process.env.PORT` fails `tsc -b` with "Cannot find name 'process'". Drop it or add `@types/node`.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** `web-app/references/react-client.md`.

**Checked at 1.6.0.** `web-app/references/react-client.md` § Never (line ~136) and `patterns-common-gotchas.md` (~587) cover `process.env.PORT` without `@types/node`; `build/templates/README.md` lists `@types/node` in the web template.
