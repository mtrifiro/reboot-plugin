---
id: crm-kit-61
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §9"
reboot_version: 1.6.0
severity: unrated
target: framework
names:
  - mcp-ui/SKILL.md
  - mcp-ui/references/api-method-types.md
tags: [negative-space]
cluster: "8.4"
duplicate_of: reboot-crm-62
still_applies: no
status: Resolved
resolved_by: "mcp-ui/references/api-method-types.md § Limits"
---

# MCP hosts ask permission for every tool, reads included: generated tools carry no readOnlyHint

**What happened.** Generated tools carry no `readOnlyHint`, and `Tool()` cannot add one. Users "Always allow" each.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.

**Checked at 1.6.0.** `mcp-ui/SKILL.md` (§ Tool Exposure, line ~70) and `mcp-ui/references/api-method-types.md` (~194) say `Tool()` has no MCP annotations so hosts ask permission. The framework gap remains (canonical reboot-crm-62 Open).

**Resolution (2026-10-10).** As reboot-crm-62.
