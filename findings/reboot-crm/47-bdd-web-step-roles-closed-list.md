---
id: reboot-crm-47
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P3.11"
reboot_version: 1.6.0
severity: yellow
target: bdd
names:
  - python/references/testing-web-app.md
tags: [testing, frontend, negative-space]
cluster: "4.1"
still_applies: yes
status: Resolved
resolved_by: "python/references/testing-web-app.md § Do this"
---

# The web steps' roles are a closed list, and menuitemcheckbox is not in it

**What happened.** `ELEMENT` in `reboot/bdd/grammar.py` admits `button, link, tab, checkbox, radio, menuitem, option, row, table`. A menu item with `role="menuitemcheckbox"` therefore cannot be clicked by any step, and `get_by_role` does not fall back to `button` for an element whose explicit role overrides its tag. The app's theme toggle lives in such an item, so the scenario had to drive radios elsewhere and assert the menu followed.

**Expected.** Open `ELEMENT` to any ARIA role string (passed to `get_by_role`, which Playwright validates), or at least add `menuitemcheckbox`, `menuitemradio`, `switch`, `combobox`, `slider`, `dialog`, `tooltip`, `heading`, `listitem`. Recommendation: open the list.

**Repro.** Not recorded.

**Where in the skills.** `python/references/testing-web-app.md` (roles list at ~lines 152-154).

**Checked at 1.6.0.** `testing-web-app.md` lines 152-154 now document the closed role list (the framework limit itself is unchanged).
