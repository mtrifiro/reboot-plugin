---
id: reboot-crm-59
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P3.23"
reboot_version: 1.6.0
severity: yellow
target: plugin
names:
  - run/SKILL.md
tags: [operations, builder-drift]
cluster: "4.2"
duplicate_of: reboot-air-141-11
still_applies: yes
status: Resolved
resolved_by: "run/SKILL.md § Tunnel — MCP branch only"
---

# run skill mandates a Cloudflare quick tunnel for web apps

**What happened.** The skill says to start `cloudflared` "for both app types" before the backend. For a standalone web app with no MCP client it only exposes a local dev server to the internet. (Same finding as reboot-air-150-07.)

**Expected.** Make the Cloudflare quick tunnel MCP-UI-only in `run/SKILL.md`. The source argues for removal on security grounds alone.

**Repro.** Not recorded.

**Where in the skills.** `run/SKILL.md` Step 5.

**Checked at 1.6.0.** `run/SKILL.md` lines ~106-123 still start the tunnel under "Backend — both app types"; the frontmatter description still lists the tunnel unconditionally.
