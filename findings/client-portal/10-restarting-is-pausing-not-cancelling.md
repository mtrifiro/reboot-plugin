---
id: client-portal-10
project: client-portal
source: "client-portal/reboot-findings.md §10"
reboot_version: 1.6.0
severity: unrated
target: plugin
names:
  - run/SKILL.md
  - python/references/servicer-workflow.md
tags: [operations, negative-space]
cluster: "F"
still_applies: yes
status: Resolved
resolved_by: "run/references/stop-restart-reset.md § Restart"
---

# Restarting is pausing, not cancelling

**What happened.** Stopping `rbt dev run` does not cancel an in-flight workflow. On the next start it replays from its memoized steps and carries on, which is the point of durability, and a surprise the first time a pass thought to be killed resumes mid-vault.

**Expected.** To actually stop recurring work you need an application-level switch (`sync_active` here, which nothing exposes a method to change) or `expunge`.

**Repro.** Not recorded.

**Where in the skills.** `run/SKILL.md` stop/restart section (does not exist).

**Checked at 1.6.0.** `run/SKILL.md` has no stop/restart section and no mention that workflows resume after a restart.
