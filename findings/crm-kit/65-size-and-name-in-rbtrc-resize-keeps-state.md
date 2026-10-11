---
id: crm-kit-65
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §10"
reboot_version: 1.6.0
severity: unrated
target: plugin
names:
  - python/references/lifecycle-reboot-cloud.md
tags: [operations]
cluster: "4.1"
duplicate_of: reboot-crm-42
still_applies: no
status: Resolved
resolved_by: "python/references/lifecycle-reboot-cloud.md § Limits"
---

# Put cloud up --size= and --application-name= in .rbtrc; resizing keeps state

**What happened.** One forgotten flag on a redeploy silently resizes. Resizing itself is non-destructive: it rolls a new revision and keeps the state.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.

**Checked at 1.6.0.** `lifecycle-reboot-cloud.md` § Limits: "Changing `--size` keeps state". Pinning `--size` in `.rbtrc` is not suggested.
