---
id: crm-kit-46
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §6"
reboot_version: 1.6.0
severity: unrated
target: bdd
names:
  - python/references/testing-web-app.md
tags: [testing]
cluster: "4.1"
duplicate_of: reboot-crm-47
still_applies: no
status: Resolved
resolved_by: "python/references/testing-web-app.md § Do this"
---

# BDD: roles are a closed list and there is no hover, drag, right-click or modifier-click

**What happened.** Roles are `button, link, tab, checkbox, radio, menuitem, option, row, table`. There is no hover, drag, right-click or modifier-click; write a custom step over `web_app.page(user=...)`.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.

**Checked at 1.6.0.** `python/references/testing-web-app.md` § Do this lists the roles (line ~132) and says other gestures (hover, drag) are custom steps over the Playwright `Page` (~142).
