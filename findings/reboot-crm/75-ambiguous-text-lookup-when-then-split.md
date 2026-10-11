---
id: reboot-crm-75
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P4.6"
reboot_version: 1.6.0
severity: green
target: plugin
names:
  - python/references/testing-web-app.md
tags: [testing, frontend, error-text]
cluster: "4.1"
still_applies: yes
status: Resolved
resolved_by: "python/references/testing-web-app.md § Never"
---

# Ambiguous text lookups: the When/Then split of 'saves the text of the element' is unstated

**What happened.** `sees "55" in the web app` fails with a strict-mode violation when the number appears twice on the page (expected). The fix (a `data-testid` plus `saves the text of the "..." element`) took a while to find because the `Then`/`When` distinction is not stated: it is a `When`, and using it after `Then` fails with "Step definition is not found".

**Expected.** Fix proposed: state the When/Then split for the step in `testing-web-app.md`; suggest the remedy in the strict-mode error. Recommendation: the documentation first.

**Repro.** Not recorded.

**Where in the skills.** `python/references/testing-web-app.md`.

**Checked at 1.6.0.** `python/references/testing-web-app.md` (lines ~148, 160) documents the step and its `data-testid` use but not that it is a `When` and fails after a `Then`.
