---
id: crm-kit-47
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §6"
reboot_version: 1.6.0
severity: unrated
target: plugin
names:
  - python/references/testing-web-app.md
tags: [testing, frontend]
cluster: "4.1"
duplicate_of: reboot-crm-48
still_applies: no
status: Resolved
resolved_by: "python/references/testing-web-app.md § Do this"
---

# BDD: buttons match by accessible name, but checks and fills match by label text including aria-hidden glyphs

**What happened.** Buttons match by accessible name, but `checks` and `fills` match by label text, which includes an `aria-hidden` glyph or a count pill inside the `<label>`. Keep label text plain.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.

**Checked at 1.6.0.** `python/references/testing-web-app.md` § Do this (line ~134) distinguishes accessible name (glyph excluded) from label matching, per canonical reboot-crm-48.
