---
id: crm-kit-23
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §3"
reboot_version: 1.6.0
severity: unrated
target: plugin
names:
  - python/references/state-actor-decomposition.md
tags: [pattern, cost]
cluster: ""
still_applies: no
status: Resolved
resolved_by: "python/references/state-actor-decomposition.md § Signals that a `Type` holds more than one concern"
---

# Put state written by slow external work (research or sync status) on its own actor

**What happened.** Writers on one actor serialize, so a slow status write queues behind ordinary edits, and the edits queue behind it.

**Expected.** State written by slow external work lives on its own actor.

**Repro.** Not recorded.

**Where in the skills.** Not named by the source.

**Checked at 1.6.0.** `python/references/state-actor-decomposition.md` lists as a signal "A background workflow's writes contend with user actions (the monitor's 'last scanned at' serializes against a persona edit)".
