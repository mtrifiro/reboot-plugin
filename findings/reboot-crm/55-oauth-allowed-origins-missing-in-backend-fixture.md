---
id: reboot-crm-55
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P3.19"
reboot_version: 1.6.0
severity: yellow
target: plugin
names:
  - python/references/testing-features.md
  - python/references/testing-web-app.md
tags: [testing, scaffold, auth, error-text]
cluster: "B"
still_applies: yes
status: Open
resolved_by: ""
---

# OAuth(...) needs allowed_origins in the test harness, but the backend-only fixture template does not show it

**What happened.** The first `uv run pytest` failed on every scenario with the "`OAuth` requires `allowed_origins=[...]` to be set explicitly in production" error (which the author calls excellent), because the harness is neither `rbt dev run` nor `rbt serve`. `testing-web-app.md` shows `allowed_origins=[frontend.origin]` for browser scenarios; `testing-features.md`'s minimal module has no `oauth=` at all, so a backend-only module for an `oauth=` app must discover `allowed_origins=[]` from the error.

**Expected.** Add `oauth=OAuth(..., allowed_origins=[])` to the minimal backend-only fixture in `testing-features.md`, with a line saying the harness requires the explicit empty list.

**Repro.** Run `uv run pytest` on a backend-only module for an app with `oauth=`.

**Where in the skills.** `python/references/testing-features.md` minimal fixture module.

**Checked at 1.6.0.** `testing-features.md` has no `oauth` or `allowed_origins` text (grep).
