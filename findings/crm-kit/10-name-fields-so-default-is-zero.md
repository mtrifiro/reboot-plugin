---
id: crm-kit-10
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §2"
reboot_version: 1.6.0
severity: unrated
target: plugin
names:
  - python/references/api-schema-evolution.md
  - python/references/state-scalar-fields.md
tags: [pattern, negative-space]
cluster: "4.1"
duplicate_of: reboot-crm-85
still_applies: no
status: Resolved
resolved_by: "python/references/api-schema-evolution.md § Do this"
---

# Name every field so the wanted default is the zero value (show_tags, not hide_tags)

**What happened.** Non-zero defaults are refused and fields cannot be deleted, so flipping a default later costs a second field, forever. Rule: `show_tags: bool = False`, never `hide_tags` defaulting to `True`.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.

**Checked at 1.6.0.** `python/references/api-schema-evolution.md` lines ~111-112 (under § Do this): "Name fields so the default is the zero value (`show_tags`, not `hide_tags`); flipping a default costs a second field."
