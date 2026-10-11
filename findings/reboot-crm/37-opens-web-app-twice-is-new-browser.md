---
id: reboot-crm-37
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P3.4"
reboot_version: 1.6.0
severity: yellow
target: plugin
names:
  - python/references/testing-web-app.md
tags: [testing, frontend, negative-space]
cluster: "4.1"
still_applies: yes
status: Resolved
resolved_by: "python/references/testing-web-app.md § Never"
---

# "Opens the web app" a second time is a new browser, not a reload

**What happened.** To assert that a preference kept in `localStorage` survives a reload, two `opens the web app` steps do not work: `WebApp.open` calls `new_context()` and `context.new_page()` every time, so the second open is a fresh browser profile with empty storage, and `self.pages[user]` quietly replaces the first page (which is never closed, so its video keeps Playwright's default name; see reboot-crm-60). Reopening as a new machine is useful (used to prove a server-side preference follows a teammate), but nothing says that is what it means. A per-browser preference (theme) has no reachable assertion at all.

**Expected.** Fixes proposed: add a `reloads the web app` step mapping to `page.reload()`; document the distinction in `testing-web-app.md`. Recommendation: both.

**Repro.** Use two `opens the web app` steps in one scenario and assert persisted browser storage.

**Where in the skills.** `python/references/testing-web-app.md`.

**Checked at 1.6.0.** `testing-web-app.md` has no mention of reload or that a second open starts a new browser (grep for `reload`, `new_context`).
