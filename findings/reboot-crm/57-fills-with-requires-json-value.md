---
id: reboot-crm-57
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P3.21"
reboot_version: 1.6.0
severity: yellow
target: plugin
names:
  - python/references/testing-web-app.md
tags: [testing, index-gap]
cluster: "4.1"
still_applies: unknown
status: Open
resolved_by: ""
---

# fills ... with requires a JSON value

**What happened.** `fills "Your name" in the web app with `Alice`` fails with a JSON parse error; it must be `"Alice"`. The message is clear, but `testing-web-app.md`'s examples only show numbers, so the first text fill always trips.

**Expected.** Add one string example to the `fills` row of the table: `fills "Your name" in the web app with "Alice"`.

**Repro.** Not recorded.

**Where in the skills.** `python/references/testing-web-app.md` `fills` row.

**Checked at 1.6.0.** `testing-web-app.md` line ~138 and examples at lines ~27, 175 still show numeric values only (as grepped); no string example found.
