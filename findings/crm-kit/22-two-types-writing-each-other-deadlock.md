---
id: crm-kit-22
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §3"
reboot_version: 1.6.0
severity: unrated
target: plugin
names:
  - python/references/state-actor-decomposition.md
  - python/references/rpc-calls.md
tags: [pattern, negative-space]
cluster: "4.1"
duplicate_of: reboot-crm-25
still_applies: no
status: Resolved
resolved_by: "python/references/state-actor-decomposition.md § Never; python/references/rpc-calls.md § Never"
---

# Never let two types call each other's writers; one fact has one owner

**What happened.** "A's transaction writes B" plus "B's transaction writes A" deadlocks two ordinary concurrent requests. No tool reports it and no test produces it. The fix that holds removes the duplicated fact. Reaching back later through a workflow's `per_workflow` call is fine.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.

**Checked at 1.6.0.** `python/references/state-actor-decomposition.md` § Never forbids a writer cycle and § Do this has "Each fact has one owner"; `rpc-calls.md` § Never per the canonical item.
