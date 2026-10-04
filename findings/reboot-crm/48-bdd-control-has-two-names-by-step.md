---
id: reboot-crm-48
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P3.12"
reboot_version: 1.6.0
severity: yellow
target: plugin
names:
  - python/references/testing-web-app.md
tags: [testing, frontend, negative-space, error-text]
cluster: "4.1"
still_applies: yes
status: Open
resolved_by: ""
---

# The same control has two different names, depending on the step

**What happened.** `clicks the "X" button` resolves by accessible name, where an `aria-hidden` glyph inside the element is excluded. `checks "X"` and `fills "X"` resolve by `get_by_label(label, exact=True)`, which matches the label's text, where the same glyph is included. So `<label><span aria-hidden>...</span>Dark</label>` is `"Dark"` to one family of steps and only `"<glyph>Dark"` to the other. Both failures are a 30-second Playwright timeout with a `get_by_label` call log and no hint that the glyph is the problem.

**Expected.** Fixes proposed: resolve both families by accessible name (preferred); or relax label steps to `exact=False`/trim non-text nodes; skill fix: `testing-web-app.md` says which steps use which name.

**Repro.** Not recorded.

**Where in the skills.** `python/references/testing-web-app.md`.

**Checked at 1.6.0.** `testing-web-app.md` line 137 says click steps use accessible name; no statement for `checks`/`fills` label matching (grep for `get_by_label`).
