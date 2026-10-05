---
id: reboot-crm-60
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P3.24"
reboot_version: 1.6.0
severity: yellow
target: bdd
names:
  - python/references/testing-web-app.md
tags: [testing, frontend, negative-space]
cluster: "8.4"
still_applies: unknown
status: Resolved
resolved_by: "python/references/testing-web-app.md § Limits"
---

# A user who opens the web app twice leaves a video the dashboard names page@<guid>

**What happened.** Most browser scenarios show two videos in the dashboard: `VIDEO · <USER>` and `VIDEO · PAGE@<guid>` (92 stray files across `tests/*.recordings/`); the unnamed one is usually the longer. Cause, from reboot-crm-37: the second `WebApp.open` (`reboot/bdd/web.py:93`) makes a new context and overwrites `self.pages[user]`; `WebApp.close` (`web.py:137`) closes and renames only the contexts still in `self.pages`, so the first context's video finishes under Playwright's default name and the dashboard labels it with its file stem (`features_watcher.py`, `user=video.stem`). The named video shows only the tail of the scenario; sign-in is in the guid video, which keeps recording the abandoned page until teardown.

**Expected.** Options proposed: (1) `open` goes to the new path in the existing page (`page.goto`); (2) close the replaced context in `open` and keep its video under a numbered name (`alice-1.webm`, `alice.webm`); (3) `close` sweeps leftover `page@*.webm`. Recommendation: (2) alone, and name popup pages (`<user>-popup-<n>.webm`) by walking `page.context.pages` in `close`. Status 2026-09-25: not patched; a ~20-line local patch in the venv's `reboot/bdd/web.py` was described.

**Repro.** Write two `"alice" opens the web app` steps (or a custom sign-in step calling `web_app.open` then `opens the web app at`), run it, and list the scenario's digest directory: `alice.webm` and `page@<guid>.webm`.

**Where in the skills.** `python/references/testing-web-app.md` (Recordings section, ~line 228).

**Checked at 1.6.0.** `testing-web-app.md` Recordings section does not mention the stray page video.
