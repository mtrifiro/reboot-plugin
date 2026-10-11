---
id: reboot-crm-94
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md A.13"
reboot_version: 1.6.0
severity: green
target: primer
names: []
tags: [pattern, auth]
cluster: "8.4"
still_applies: unknown
status: Open
resolved_by: ""
---

# One policy is spread over four research settings

**What happened.** Who may research, and how much, is decided by the Perplexity audience, the automatic-briefs switch, the roles on full research and an old templates audience that is no longer read; each gate reads its own.

**Expected.** One `research_policy(context)` that answers every question a gate asks, and the old setting gone at the next expunge.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.
