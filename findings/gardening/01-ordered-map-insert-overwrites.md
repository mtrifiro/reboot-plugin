---
id: gardening-01
project: gardening
source: "gardening/FINDINGS.md § Plugin skills, item 1"
reboot_version: 1.6.0
severity: green
target: plugin
names:
  - python/references/stdlib-ordered-map.md
tags: [negative-space]
cluster: ""
still_applies: yes
status: Open
resolved_by: ""
---
# stdlib-ordered-map.md doesn't say insert on an existing key overwrites

**What happened.** Needed to know whether re-inserting a key updates its value (to keep a view stored as the map value current). The reference is silent. A bounded grep of `reboot/std/collections/ordered_map/v1/ordered_map.py` (the sorted merge in insert, `# Update existing key.`) shows it replaces the value.

**Expected.** One line in the Methods table ("`insert` on an existing key replaces its value").

**Repro.** `insert(key="a", bytes=b"1")` then `insert(key="a", bytes=b"2")`; `search(key="a")` returns `b"2"`.

**Where in the skills.** `python/references/stdlib-ordered-map.md`, Methods table.
