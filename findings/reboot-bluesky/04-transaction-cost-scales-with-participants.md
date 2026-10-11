---
id: reboot-bluesky-04
project: reboot-bluesky
source: "REBOOT_FINDINGS.md §4"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/servicer-transaction.md
tags: [cost]
cluster: "D"
duplicate_of: reboot-air-141-19
still_applies: yes
status: Resolved
resolved_by: "python/references/servicer-transaction.md § Scales as; python/references/patterns-load-and-benchmarking.md § Scales as"
---

# Transaction cost scales with participant count; worth a docs budget

**What happened.** Each cross-actor call inside a transaction adds coordination cost: a naive social-post transaction (~10 sequential participants) took ~10s in the dev harness, and even gathered/trimmed (~4 participants) it sits around 2-3s. `asyncio.gather` helps but does not change the per-participant floor.

**Expected.** Publish a rough latency budget per transaction participant, and steer authors early toward 'commit small, distribute via workflow' (which worked very well).

**Repro.** Not recorded.

**Where in the skills.** Not recorded; transaction reference.

**Checked at 1.6.0.** python/references/servicer-transaction.md has no per-participant cost note; python/references/rpc-calls.md:62 covers `asyncio.gather` mechanics only.
