---
id: reboot-bluesky-01
project: reboot-bluesky
source: "REBOOT_FINDINGS.md §1"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/stdlib-ordered-map.md
  - python/references/state-collections.md
tags: [version-drift, contradiction]
cluster: "A"
still_applies: no
status: Obsolete
resolved_by: ""
---

# OrderedMap construction API disagrees with the docs

**What happened.** The skill reference documented explicit construction as `await OrderedMap.create(context, map_id)`, but on `reboot==1.4.1` the generated `OrderedMap` class has no `create`/`Create` callable, only the `Create*` message types. The working spelling is `OrderedMap.ref(map_id).create(context)`, which the docs elsewhere say to avoid for constructors ('never invoke a constructor through `.ref()`').

**Expected.** Align the generated surface with the documented `Type.create(context, id)` convention, or fix the reference.

**Repro.** Not recorded.

**Where in the skills.** Stdlib OrderedMap reference / `state-collections.md`.

**Checked at 1.6.0.** python/references/stdlib-ordered-map.md:44 and :94 now document `OrderedMap.ref(id).create(context)` as the construction form, matching the working spelling.
