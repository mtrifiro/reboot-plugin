---
id: reboot-air-141-10
project: reboot-air-141
source: "reboot-air/REBOOT_FINDINGS.md §10"
reboot_version: 1.4.1
severity: red
target: plugin
names:
  - run/SKILL.md
tags: [contradiction, operations]
cluster: "4.2"
still_applies: yes
status: Resolved
resolved_by: "run/SKILL.md § Step 2 — Detect the app type"
---

# run skill web-app detection rule is unsatisfiable

**What happened.** `run/SKILL.md` Step 2 classifies an MCP Chat App if an API file uses `mcp=Tool()`, `mcp=None`, or `UI(`, and a Web App if (among other conditions) there is no `mcp=` anywhere under `api/`. But `mcp=` is a required keyword on every `Reader`, `Writer`, `Transaction`, and `Workflow` (`api-pydantic.md` says so; omitting it is a codegen error), so every Reboot API file contains `mcp=` and non-MCP methods read `mcp=None`. Followed literally, a standalone Web App classifies as an MCP Chat App on the strongest signal, and the skill would open a setup wizard the backend does not serve and hand the user an MCP endpoint instead of the SPA URL. No cost to the author, who knew the app type; misfires every time for "bring up an app at the start of a fresh session".

**Expected.** Drop `mcp=None` from the chat-app signal list (it is the negative signal). Discriminating tokens are `mcp=Tool(` and `UI(`. Restate the web-app rule as "no `mcp=Tool(` and no `UI(` anywhere under `api/`".

**Repro.** Not recorded.

**Where in the skills.** `run/SKILL.md`, Step 2 - Detect the app type.

**Checked at 1.6.0.** Still present. `run/SKILL.md:42` still lists `mcp=Tool()`, `mcp=None`, or `UI(` as MCP UI signals, and line 49 still says "No `mcp=` / `UI(` anywhere under `api/`" for Web Apps.
