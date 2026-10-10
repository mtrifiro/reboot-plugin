---
id: reboot-crm-65
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P3.33"
reboot_version: 1.6.0
severity: yellow
target: bdd
names: []
tags: [testing, frontend, error-text]
cluster: "8.4"
still_applies: unknown
status: Resolved
resolved_by: "python/references/testing-web-app.md § Errors you will see"
---

# A browser scenario whose page does not load times out after 30 s and says nothing about why

**What happened.** About one full run in two, one browser scenario failed on its first step (`has signed in to the web app`) with `Page.goto: Timeout 30000ms exceeded ... waiting until "load"`, before any app step ran; rerun alone it passed. The error names the URL only. Not compilation: a fresh Vite server answers `/` in 0.4 s and a cold page loads in 1.2 s; four fresh servers at once, 3.0 s each; Vite's dependency cache was not being rebuilt. Likely contributor, removed: `web/index.html` loaded a Google Fonts stylesheet, which holds up `load`, so each of ~150 browser scenarios waited on it (forty requests: median 0.1 s, slowest 1.2 s; the tail exists but this does not prove it reached thirty). Fonts are now bundled (`@fontsource/*`). `tests/conftest.py` overrides the plugin's `web_app` fixture to track open requests and raise with those still open and how long each waited.

**Expected.** `WebApp.open` reports the unfinished requests itself on a navigation timeout, and the `ready()` check it waits on fetches the app's entry module, not only `/`, so a Vite that answers `index.html` but has not compiled the app is not called ready.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.

**Resolution (2026-10-10).** Rows in `testing-web-app.md` § Errors you will see: the bare `TimeoutError` from the `frontend` fixture after a new dependency (Vite's cold pre-bundle); `Page.goto: Timeout 30000ms` on a first step (a slow request holding `load`; bundle fonts, report open requests).
