---
id: theater-network-11
project: theater-network
source: "theater-network/docs/reboot-findings.md §11"
reboot_version: 1.4.0
severity: unrated
target: plugin
names:
  - run/SKILL.md
  - python/references/lifecycle-rbtrc.md
tags: [operations, error-text]
cluster: "F"
still_applies: yes
status: Open
resolved_by: ""
---

# Dev-state hygiene: expunge incompatible dev state; do not race two dev runs

**What happened.** Dev state that lived through incompatible design generations (method kinds changed, old scheduled tasks pointing at reworked methods) eventually trips native asserts (`database.cc Check failed`) and context-type errors on task replay. `rbt dev expunge` (or removing `.rbt/dev/<app>`) plus reseeding is the fix, not debugging the wreck. Also: two `rbt dev run`s racing over one state dir fight over the rocksdb LOCK and crash-loop; always kill the old process and wait before starting the next.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** `run/SKILL.md` Stop / restart / reset section (proposal task F).

**Checked at 1.6.0.** `run/SKILL.md` has no expunge, LOCK or double-run guidance (grep for stop/pkill/LOCK/orphan found nothing). `expunge` appears only in `python/references/lifecycle-rbtrc.md`.
