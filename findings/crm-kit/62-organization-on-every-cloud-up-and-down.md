---
id: crm-kit-62
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §10"
reboot_version: 1.6.0
severity: unrated
target: cloud
names:
  - python/references/lifecycle-reboot-cloud.md
  - deploy/SKILL.md
tags: [operations, error-text]
cluster: "4.4"
duplicate_of: reboot-crm-41
still_applies: no
status: Resolved
resolved_by: "python/references/lifecycle-reboot-cloud.md § Never; deploy/SKILL.md § Step 2 — Deploy the backend to Reboot Cloud"
---

# Pass --organization to every rbt cloud up and rbt cloud down

**What happened.** Without it, `up` refuses ("--organization=... is required for new applications"), and `down` says "User '<uuid>' does not have an application named ...", which reads as if production is gone. §11: `lifecycle-reboot-cloud.md` said it was needed only the **first** time.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** `lifecycle-reboot-cloud.md` (§11).

**Checked at 1.6.0.** `lifecycle-reboot-cloud.md` ("on **every** `rbt cloud` command", § Never) and `deploy/SKILL.md` Step 2.
