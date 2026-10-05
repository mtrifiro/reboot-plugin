---
id: reboot-air-141-11
project: reboot-air-141
source: "reboot-air/REBOOT_FINDINGS.md §11"
reboot_version: 1.4.1
severity: red
target: plugin
names:
  - run/SKILL.md
tags: [contradiction, operations]
cluster: "4.2"
still_applies: yes
status: Resolved
resolved_by: "run/SKILL.md § Tunnel — MCP branch only"
---

# run skill starts a public tunnel for Web Apps

**What happened.** `run/SKILL.md` Step 5, headed "Backend - both app types", says to start a Cloudflare quick tunnel before the backend "so external MCP clients (e.g. ChatGPT) can reach it". A Web App has no MCP surface (Step 2 defines it so, and the wizard subsection says to skip it for Web Apps), but the tunnel carve-out is missing. Followed literally, it publishes the local dev server to a public `*.trycloudflare.com` URL, reachable by anyone who learns the hostname; with `Development()` sign-in the account picker mints an identity for any visitor, so this is a live console on the open internet. The author skipped it and told the user why; an agent following the step as written would not.

**Expected.** Retitle the block "Backend - MCP Chat Apps need a tunnel" and add the same skip sentence the wizard subsection has. If a tunnel is wanted for a Web App (sharing a preview) it should be an explicit, user-confirmed choice.

**Repro.** Not recorded.

**Where in the skills.** `run/SKILL.md`, Step 5 - "Backend - both app types".

**Checked at 1.6.0.** Still present. `run/SKILL.md:106-110` still has the heading "Backend - both app types" and starts the tunnel before the backend for external MCP clients, with no Web App skip.
