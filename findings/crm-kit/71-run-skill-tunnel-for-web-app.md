---
id: crm-kit-71
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §11"
reboot_version: 1.6.0
severity: unrated
target: plugin
names:
  - run/SKILL.md
tags: [operations]
cluster: "4.2"
duplicate_of: reboot-air-141-11
still_applies: no
status: Resolved
resolved_by: "run/SKILL.md § Tunnel — MCP branch, only when the client is elsewhere"
---

# run/SKILL.md starts a Cloudflare quick tunnel for both app types

**What happened.** `run/SKILL.md` starts a Cloudflare quick tunnel for "both app types". Skip it for a web app with no MCP client, because it only exposes the dev server.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** `run/SKILL.md`.

**Checked at 1.6.0.** `run/SKILL.md` § Tunnel — MCP branch only.
