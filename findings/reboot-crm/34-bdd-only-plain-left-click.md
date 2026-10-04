---
id: reboot-crm-34
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P3.1"
reboot_version: 1.6.0
severity: yellow
target: plugin
names:
  - python/references/testing-web-app.md
  - python/references/testing-features.md
tags: [testing, frontend, negative-space]
cluster: "4.1"
still_applies: yes
status: Open
resolved_by: ""
---

# The only click is a plain left click; every other pointer gesture needs a custom step

**What happened.** `CLICKS_IN_WEB_APP` (`reboot/bdd/grammar.py`) is anchored end to end with no room for a modifier or a count, and its body is an unqualified Playwright click (`reboot/bdd/web.py`). Not expressible in a feature file: shift-click, ctrl/cmd-click, alt-click, double-click, right-click, middle-click, click-and-hold, hover, drag-and-drop, scroll, focus. `presses "<key>"` maps to `keyboard.press(key)` so `Shift+Tab` works, but it cannot hold a modifier across a click step. Consequence: a `@blocked` scenario (double-clicking a board card) until the app wrote its own `double-clicks` and `right-clicks` steps over the raw Playwright `Page` exposed by `web_app.page(user=...)`; shift-click range selection and drag-to-reorder still have no scenario. Two caveats: a right-click is only testable if the frontend calls `preventDefault()` and renders its own `role="menu"`, and HTML5 drag-and-drop often defeats `drag_to()` and needs manual `mouse.down()/move()/up()`.

**Expected.** Playwright's `click()` already takes `button=`, `click_count=`, `modifiers=`. Minimum fix proposed: `double-clicks <element>`, `right-clicks <element>`, `clicks <element> while holding "<key>"`, then `hovers` and `drags`. Skill fix proposed: `python/references/testing-web-app.md` documents the custom-step escape hatch over `web_app.page(user=...)` and the two caveats. The source calls this the highest-value yellow item.

**Repro.** Not recorded beyond the custom-step workaround (`@when(parsers.parse('"{user}" shift-clicks the "{name}" {role} in the web app'))` calling `.click(modifiers=['Shift'])`).

**Where in the skills.** `python/references/testing-web-app.md`.

**Checked at 1.6.0.** `testing-web-app.md` has no mention of double-click, right-click, modifiers or the `web_app.page(user=...)` escape hatch (grep); `testing-features.md` line ~315 documents custom steps generally.
