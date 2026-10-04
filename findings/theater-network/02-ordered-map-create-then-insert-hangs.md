---
id: theater-network-02
project: theater-network
source: "theater-network/docs/reboot-findings.md §2"
reboot_version: 1.4.0
severity: unrated
target: plugin
names:
  - python/references/stdlib-ordered-map.md
tags: [negative-space]
cluster: "4.1"
still_applies: yes
status: Resolved
resolved_by: "python/references/stdlib-ordered-map.md § Never"
---

# OrderedMap: create then touch the same map in one transaction hangs

**What happened.** Bisected on 1.3.0, one operation per run, within one transaction: `insert` alone works; `create` alone works; `insert` then `search` works; `create` then `insert` hangs. Related: `search`/`range` on a map nothing has ever inserted into abort with `StateNotConstructed`.

**Expected.** Let the first `insert` construct the map implicitly. Either guard reads with a `<index>_ready` flag, or use `maintain_size=True` and read `total_size` instead of a pre-`search` existence check.

**Repro.** Single transaction: `create` then `insert` on the same OrderedMap (1.3.0). Other combinations in the source table did not hang.

**Where in the skills.** `python/references/stdlib-ordered-map.md` (Never/Limits line for create-then-insert in one transaction).

**Checked at 1.6.0.** `python/references/stdlib-ordered-map.md` lines ~90-110 show `create` in a transaction and say to skip it and let the first `insert` construct the map; it documents `StateNotConstructed` on read-before-insert but has no warning about create-then-insert in one transaction. Behaviour not re-verified against the 1.6.0 runtime, so the framework may have been fixed.
