---
id: theater-chain-10
project: theater-chain
source: "theater-chain/reboot-findings.md §10"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/lifecycle-rbtrc.md
  - run/SKILL.md
tags: [operations, error-text]
cluster: "F"
still_applies: yes
status: Open
resolved_by: ""
---

# Never run rbt dev expunge while rbt dev run is live

**What happened.** Resetting seed data mid-session looked harmless but the running dev server kept its handle on the deleted RocksDB directory and fell into an unrecoverable loop, once per second, forever: `Failed to flush monotonic clock high water mark: IO error: No such file or directory: .../p000000/000071.sst`. Remedy: stop the backend first, then expunge, then start it again.

**Expected.** One line in `lifecycle-rbtrc.md` next to `dev expunge --application-name=`.

**Repro.** Not recorded.

**Where in the skills.** `python/references/lifecycle-rbtrc.md`.

**Checked at 1.6.0.** Still absent. `python/references/lifecycle-rbtrc.md:49,63` mention `dev expunge --application-name=` with no warning about a live server; `run/SKILL.md` has no stop/expunge guidance.
