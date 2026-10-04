---
id: reboot-crm-74
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P4.5"
reboot_version: 1.6.0
severity: green
target: plugin
names:
  - python/references/stdlib-queue.md
  - python/references/stdlib-ordered-map.md
tags: [negative-space, error-text, index-gap]
cluster: "4.1"
still_applies: yes
status: Open
resolved_by: ""
---

# A stdlib Queue needs no create, unlike an OrderedMap

**What happened.** `Queue.ref(id).create(context)` does not exist (`"WeakReference" has no attribute "create"`) because the queue builds its backing sorted map on first use. An `OrderedMap` aborts when read before its first insert, so the app constructs one explicitly. The neighbouring reference trains one to construct collections, so the error reads as a missing feature.

**Expected.** One line in `stdlib-queue.md`: a `Queue` builds its backing sorted map on first use and has no `create`, unlike an `OrderedMap`. (But see reboot-crm-63: an unused queue still aborts on `empty`.)

**Repro.** Not recorded.

**Where in the skills.** `python/references/stdlib-queue.md`.

**Checked at 1.6.0.** `python/references/stdlib-queue.md` has no line contrasting `Queue` with `OrderedMap` construction (grep for `create`).
