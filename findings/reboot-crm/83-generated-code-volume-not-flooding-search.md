---
id: reboot-crm-83
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md A.2"
reboot_version: 1.6.0
severity: green
target: primer
names: []
tags: [cost, pattern]
cluster: "D"
still_applies: unknown
status: Open
resolved_by: ""
---

# Generated code is 15x the hand-written code, but .gitignore already keeps it out of search

**What happened.** `rbt generate` writes about 555k lines of Python into `backend/api` and 321k of TypeScript into `web/src/api`, roughly eighty generated lines per line of schema. First written down as flooding every search; measured, it does not: both folders are in `.gitignore`, and ripgrep, the agent's own search tool and the machine's `grep` (ugrep) honour it, so a search for `QueueByHand` returned the two hand-written files and none of the 220 generated hits. Status: nothing to do; corrected 2026-10-04.

**Expected.** Keep the `.gitignore` entries; prefer search tools that honour `.gitignore` (plain `grep -r` and `find` still see everything).

**Repro.** Not recorded.

**Where in the skills.** Not recorded.
