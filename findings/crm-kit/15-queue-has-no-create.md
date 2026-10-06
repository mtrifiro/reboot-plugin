---
id: crm-kit-15
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §2"
reboot_version: 1.6.0
severity: unrated
target: plugin
names:
  - python/references/stdlib-queue.md
tags: [error-text]
cluster: "4.1"
duplicate_of: reboot-crm-74
still_applies: no
status: Resolved
resolved_by: "python/references/stdlib-queue.md § Never"
---

# Never call create on a stdlib Queue

**What happened.** `Queue` has no `create` (`"WeakReference" has no attribute "create"`), unlike `OrderedMap`.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.

**Checked at 1.6.0.** `python/references/stdlib-queue.md` § Never covers it, per the canonical item reboot-crm-74.
