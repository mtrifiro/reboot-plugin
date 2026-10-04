---
id: reboot-crm-42
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P3.7d"
reboot_version: 1.6.0
severity: yellow
target: plugin
names:
  - python/references/lifecycle-reboot-cloud.md
tags: [operations, negative-space]
cluster: "4.1"
still_applies: yes
status: Open
resolved_by: ""
---

# Nothing says whether resizing an application keeps its state

**What happened.** Moving from `xsmall` to `small` raised "does `--size` repartition, and does the state survive?" `lifecycle-reboot-cloud.md` describes `--size` as "the application footprint" and lists the five values; no other plugin skill mentions it. The answer, confirmed by Reboot: resizing is non-destructive; `rbt cloud up` at a new size rolls a new revision forward and keeps state, like any other redeploy. The gap pushes a cautious operator toward `down --expunge`, which is destructive.

**Expected.** One sentence next to `--size`: changing it rolls a new revision and preserves state.

**Repro.** Not recorded.

**Where in the skills.** `python/references/lifecycle-reboot-cloud.md` (~line 81).

**Checked at 1.6.0.** `lifecycle-reboot-cloud.md` lines 81-82 list the sizes with no statement about state.
