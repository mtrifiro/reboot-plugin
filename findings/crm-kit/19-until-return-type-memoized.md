---
id: crm-kit-19
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §3"
reboot_version: 1.6.0
severity: unrated
target: plugin
names:
  - python/references/servicer-workflow-wait.md
tags: [error-text]
cluster: "4.4"
duplicate_of: reboot-crm-13
still_applies: no
status: Resolved
resolved_by: "python/references/servicer-workflow-wait.md § Never"
---

# Never change an until callable's return type once it has run; rename the alias instead

**What happened.** Results are memoized with their type. Instances that already resolved retry forever with `TypeError: Stored result of type 'str' from 'callable' is not compatible with the expected type 'bool'`.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.

**Checked at 1.6.0.** `python/references/servicer-workflow-wait.md` § Never, per the canonical item reboot-crm-13.
