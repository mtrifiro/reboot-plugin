---
id: reboot-crm-62
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P3.26"
reboot_version: 1.6.0
severity: yellow
target: framework
names:
  - mcp-ui/SKILL.md
tags: [negative-space, frontend]
cluster: "8.4"
still_applies: yes
status: Open
resolved_by: ""
---

# Generated MCP tools carry no annotations, so a host asks permission for every Reader call

**What happened.** With nineteen methods exposed as tools, Claude asks "Allow once / Always allow" before every call including plain reads; drawing one account card takes three reads, so three prompts; "Always allow" is per tool and repeats for every tool added later. MCP tool `annotations` (`readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint`) exist and `FastMCP.tool(..., annotations=...)` accepts them (`mcp/server/fastmcp/server.py:446-451`), but the generated registration never passes any (`reboot/templates/reboot.py.j2:2768-2776`, UI tool at 2969) and `reboot.api.Tool` has only `name` and `title` (`reboot/api.py:892-897`). No application-side workaround; the `mcp-ui` skill does not mention the prompts.

**Expected.** `readOnlyHint=True` on every tool generated from a `Reader` and `idempotentHint` where the method has an idempotency alias; failing that `Tool(read_only=True)` or `annotations=...`.

**Repro.** Any `Reader` with `mcp=Tool()`, connected to claude.ai; watch the permission prompt on its first call.

**Where in the skills.** `mcp-ui/SKILL.md` and `mcp-ui/references/api-method-types.md` (no mention).

**Checked at 1.6.0.** No mention of annotations or permission prompts in `mcp-ui/` (grep).
