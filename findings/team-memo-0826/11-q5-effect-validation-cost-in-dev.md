---
id: team-memo-0826-11
project: team-memo-0826
source: "2026.08.26 Findings for Reboot Team - Docs, Skills, and Runtime.md Q5"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/testing-failure-recovery.md
  - python/references/lifecycle-rbtrc.md
tags: [cost]
cluster: "D"
still_applies: yes
status: Open
resolved_by: ""
---

# Effect validation cost in dev

**What happened.** Disabling it (`--effect-validation=disabled`) took a three-actor transaction from roughly 1.9s to 1.4s perceived in the browser.

**Expected.** Source asks whether `quiet` mode is cheaper than `enabled` or only quieter, and requests a one-line docs note on the dev-mode latency tax.

**Repro.** Not recorded.

**Where in the skills.** Wherever effect validation is documented.

**Checked at 1.6.0.** Same as reboot-bluesky-03: no dev-latency note in python/references/testing-failure-recovery.md:168-183.
