---
id: crm-kit-66
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §10"
reboot_version: 1.6.0
severity: unrated
target: cloud
names:
  - python/references/lifecycle-reboot-cloud.md
  - deploy/SKILL.md
tags: [operations]
cluster: "4.1"
duplicate_of: reboot-crm-43
still_applies: no
status: Resolved
resolved_by: "python/references/lifecycle-reboot-cloud.md § Limits; deploy/SKILL.md § Step 6 — Verify"
---

# After cloud up, poll before trusting the app or importing into it

**What happened.** `up` exits 0 about 30 s before `/__/inspect` stops answering 503. A 503 carrying CORS headers means "still starting". The first 200 comes from one replica, and the others resolve in DNS about 30 s later. Poll `rbt inspect state list --type=... --application-url=...` until it succeeds. `initialize` re-runs on every new revision.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.

**Checked at 1.6.0.** `lifecycle-reboot-cloud.md` § Limits ("`rbt cloud up` returns before the app serves") and `deploy/SKILL.md` Step 6.
