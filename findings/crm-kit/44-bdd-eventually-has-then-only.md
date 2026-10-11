---
id: crm-kit-44
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §6"
reboot_version: 1.6.0
severity: unrated
target: bdd
names:
  - python/references/testing-features.md
  - python/references/testing-web-app.md
tags: [testing]
cluster: "4.4"
duplicate_of: reboot-crm-52
still_applies: no
status: Resolved
resolved_by: "python/references/testing-features.md § Never"
---

# BDD: eventually has works only under Then; saves the text of the element is a When

**What happened.** `eventually has` works only under `Then`. `saves the text of the "..." element` is a `When`.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.

**Checked at 1.6.0.** `python/references/testing-features.md` § Never: "`eventually has` under `Given` or `When`"; the When/Then split of `saves the text` is covered in `testing-web-app.md` § Never (canonical reboot-crm-75).
