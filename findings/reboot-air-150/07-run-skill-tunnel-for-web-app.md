---
id: reboot-air-150-07
project: reboot-air-150
source: "reboot-air/reboot-findings.md §7"
reboot_version: 1.5.0
severity: unrated
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

# run skill tells a Web App to start a Cloudflare tunnel it has no use for

**What happened.** `run/SKILL.md` Step 5 says to start `cloudflared` "for both app types" so external MCP clients can reach the dev server. A standalone Web App with no MCP surface has no such clients, so the author skipped it. Likewise `rbt dev run` prints "MCP clients can connect at: .../mcp" for an app with no `mcp=Tool()` methods, which is confusing next to the skill's own "Web App has no MCP surface" rule.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** `run/SKILL.md`, Step 5 ("Backend — both app types").

**Checked at 1.6.0.** `run/SKILL.md` lines ~106-123 still start the Cloudflare tunnel under "Backend — both app types".
