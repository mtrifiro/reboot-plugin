---
id: crm-kit-54
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §7"
reboot_version: 1.6.0
severity: unrated
target: framework
names:
  - inspect/SKILL.md
tags: [operations, error-text]
cluster: "F"
duplicate_of: reboot-crm-56
still_applies: no
status: Resolved
resolved_by: "inspect/SKILL.md § Known issues"
---

# rbt inspect needs --type=<pkg>.v1.<Type> and --application-url even locally; list output has two shapes

**What happened.** The URL is required. Repeated fields come back as `{"items": [...]}` or as bare arrays on the same type, so handle both. `inspect` does not open `OrderedMap` contents.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.

**Checked at 1.6.0.** `inspect/SKILL.md` § Known issues covers the required `--application-url`, `--type=` form, the two list shapes, and that an `OrderedMap` shows only an id (keys live in a `Node` actor).
