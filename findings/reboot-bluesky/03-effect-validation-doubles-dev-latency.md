---
id: reboot-bluesky-03
project: reboot-bluesky
source: "REBOOT_FINDINGS.md §3"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/lifecycle-rbtrc.md
  - python/references/testing-failure-recovery.md
tags: [cost]
cluster: "D"
still_applies: yes
status: Resolved
resolved_by: "python/references/patterns-load-and-benchmarking.md § Scales as; python/references/lifecycle-seeding.md § Scales as"
---

# Effect validation doubles dev-mode mutation latency, silently

**What happened.** Measured on `create_post` (a multi-actor transaction): ~10.6s median with effect validation on, ~5.7s off, before any app optimization. The 60-second log line explains what validation does, not what it costs.

**Expected.** Mention the ~2x mutation cost wherever `--effect-validation` is documented; consider sampling (validate every Nth execution) so dev keeps the bug-finder without full price on every write.

**Repro.** Not recorded.

**Where in the skills.** Wherever `--effect-validation` is documented.

**Checked at 1.6.0.** python/references/testing-failure-recovery.md:168-183 only says to disable effect validation for specific tests; no dev-latency cost is documented (grep `effect.validation` across skills).
