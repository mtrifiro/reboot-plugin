---
id: crm-kit-70
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §10"
reboot_version: 1.6.0
severity: unrated
target: plugin
names:
  - python/references/lifecycle-reboot-cloud.md
  - python/references/api-schema-evolution.md
tags: [operations]
cluster: "4.1"
duplicate_of: reboot-crm-61
still_applies: yes
status: Open
resolved_by: ""
---

# A breaking change to a deployed app: export, down --expunge, up, poll, import, up, publish, export and compare

**What happened.** A deleted or renamed method is refused at boot against existing state, and the deploy fails. The order that works: export, `cloud down --expunge`, `cloud up`, poll, `rbt import`, `cloud up` again, publish the frontend, then export again and compare. Rehearse on the dev loop first. Logs: `rbt cloud logs ... --organization=... --no-follow --last=500`.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.

**Checked at 1.6.0.** `lifecycle-reboot-cloud.md` § Limits says only `rbt export` / `rbt import` keep data across a breaking-change expunge; no step-by-step procedure exists under `skills/`.
