---
id: team-memo-0826-04
project: team-memo-0826
source: "2026.08.26 Findings for Reboot Team - Docs, Skills, and Runtime.md §4"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - run/SKILL.md
  - inspect/SKILL.md
tags: [operations]
cluster: "F"
duplicate_of: reboot-crm-15
still_applies: yes
status: Resolved
resolved_by: "run/references/stop-restart-reset.md § Do this"
---

# Stopping the rbt dev run CLI leaks the application's server processes

**What happened.** Killing `rbt dev run` (SIGTERM to the CLI or its `uv` wrapper) leaves the spawned `python backend/src/main.py` servers and the envoy proxy running. Over a day of restarts four orphaned generations (twelve server processes) accumulated, contending over one state directory. Consequences: per-user slowness (actors sharded onto contended servers); `rbt dev expunge` reporting success while orphans held or recreated state; a zombie scheduled task retrying forever against a dead generation's internal port (`Connection refused ... will retry after backoff`); split-brain state where a seeded actor existed under one application id and `rbt inspect` reported `Unknown state reference` under another. Invisible until severe, because each new `rbt dev run` boots cleanly beside the orphans.

**Expected.** Source asks whether there is a supported 'stop everything' command for the dev loop, and whether SIGTERM to the CLI is supposed to reap children.

**Repro.** Not recorded.

**Where in the skills.** `run` skill (no stop section); `inspect` skill.

**Checked at 1.6.0.** run/SKILL.md and inspect/SKILL.md contain no stop/cleanup guidance; grep for `orphan`/`lsof` finds nothing relevant.
