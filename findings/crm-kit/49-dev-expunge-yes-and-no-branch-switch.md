---
id: crm-kit-49
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §7"
reboot_version: 1.6.0
severity: unrated
target: plugin
names:
  - python/references/lifecycle-rbtrc.md
  - run/references/stop-restart-reset.md
tags: [operations]
cluster: "F"
duplicate_of: reboot-crm-53
still_applies: no
status: Resolved
resolved_by: "python/references/lifecycle-rbtrc.md § Never; run/references/stop-restart-reset.md § Reset dev state (expunge)"
---

# Always pass --yes to rbt dev expunge, and never switch git branches under a running dev loop

**What happened.** Expunge prompts, and without a tty it blocks forever. An older schema against newer state wedges the loop at "waiting for modification", and the way out is `rbt dev expunge --yes`.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.

**Checked at 1.6.0.** `--yes` is covered per the canonical item reboot-crm-53. Switching git branches under a running dev loop is not mentioned under `skills/` (grep `branch`); `lifecycle-dev-loop.md` § Never covers the related case of iterating a state shape under `--watch`.
