---
id: crm-kit-42
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §6"
reboot_version: 1.6.0
severity: unrated
target: bdd
names:
  - python/references/testing-web-app.md
tags: [testing]
cluster: "4.4"
duplicate_of: reboot-crm-21
still_applies: no
status: Resolved
resolved_by: "python/references/testing-web-app.md § Never"
---

# BDD: quoted text in a built-in step must not contain " has " or " with "

**What happened.** The "Almost" catch-all swallows the step with a backtick complaint; rephrase it or rename the UI label.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.

**Checked at 1.6.0.** `python/references/testing-web-app.md` § Never, per the canonical item reboot-crm-21.
