---
id: theater-chain-08
project: theater-chain
source: "theater-chain/reboot-findings.md §8"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - run/SKILL.md
tags: [contradiction, operations]
cluster: "4.2"
still_applies: yes
status: Open
resolved_by: ""
---

# mcp=None cannot be an app-type signal and tunnel is MCP-only

**What happened.** `run/SKILL.md` detects an MCP Chat App if an API file uses `mcp=Tool()`, `mcp=None`, or `UI(`. But `mcp=` is a required keyword on all four method factories in every Reboot project (`api-pydantic.md` says so) and `mcp=None` is the documented value for a non-MCP method, so every web app the skill scaffolds is full of `mcp=None` and trips the Chat App branch. Also, the run skill starts a Cloudflare quick tunnel before the backend "so external MCP clients can reach it"; a standalone web app has no MCP clients, so the tunnel is pure overhead.

**Expected.** Drop `mcp=None` from the signal list (`mcp=Tool(` and `UI(` are genuine signals); scope the tunnel step to Chat Apps, as the setup-wizard step already is.

**Repro.** Not recorded.

**Where in the skills.** `run/SKILL.md`. Duplicates `reboot-air-141-10` and `reboot-air-141-11`.

**Checked at 1.6.0.** Still present. `run/SKILL.md:42` still lists `mcp=None` as an MCP UI signal and `run/SKILL.md:106-110` still starts the tunnel for "both app types".
