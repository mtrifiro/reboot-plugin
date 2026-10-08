---
id: crm-kit-64
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §10"
reboot_version: 1.6.0
severity: unrated
target: plugin
names:
  - python/references/lifecycle-secrets.md
  - deploy/SKILL.md
  - python/references/lifecycle-reboot-cloud.md
tags: [operations]
cluster: "4.1"
duplicate_of: reboot-crm-40
still_applies: no
status: Resolved
resolved_by: "python/references/lifecycle-secrets.md § Limits; deploy/SKILL.md § Step 3 — Deploy the backend"
---

# First deploy order: cloud up, then one secret set with every secret, then cloud up again

**What happened.** `secret set` before the app exists fails ("does not have an application named ..."). A first `cloud up` creates the app (unhealthy if it needs secrets); then one `rbt cloud secret set A B C ... --application-name=... --organization=...`; then `cloud up` again. Each call rolls out a revision but never revives one that failed at boot. Secrets survive `down --expunge`. §11: neither `lifecycle-reboot-cloud.md`, `lifecycle-secrets.md` nor `deploy/SKILL.md` gave the order.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** `lifecycle-reboot-cloud.md`, `lifecycle-secrets.md`, `deploy/SKILL.md` (§11).

**Checked at 1.6.0.** `deploy/SKILL.md` Step 2 gives the order; `lifecycle-reboot-cloud.md` says "first `up` before first `secret set`".
