---
id: crm-kit-51
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §7"
reboot_version: 1.6.0
severity: unrated
target: framework
names:
  - python/references/lifecycle-rbtrc.md
  - run/references/stop-restart-reset.md
tags: [operations]
cluster: "F"
duplicate_of: reboot-crm-39
still_applies: no
status: Resolved
resolved_by: "python/references/lifecycle-rbtrc.md § Limits; run/references/stop-restart-reset.md § Never"
---

# --watch sometimes stops seeing backend/src/ edits; restart the dev loop

**What happened.** `--watch` sometimes stops seeing `backend/src/` edits while still reacting to `backend/api/`. When a saved backend fix seems ignored, restart the dev loop.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.

**Checked at 1.6.0.** `run/references/stop-restart-reset.md` § Never ("If an edit does not take ... Restart by hand").
