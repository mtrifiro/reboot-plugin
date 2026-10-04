---
id: cineloop-22
project: cineloop
source: "cineloop/reboot-findings.md Part 2 §I"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/lifecycle-rbtrc.md
tags: [scaffold, negative-space]
cluster: "B"
still_applies: yes
status: Open
resolved_by: ""
---

# Minor: .rbtrc watch globs should include api/

**What happened.** The canonical `.rbtrc` in `lifecycle-rbtrc.md` watches `backend/api/**/*.py` and `backend/src/**/*.py` but not the hand-written `api/**/*.py`. `api/` is the file actually edited, and `backend/api/` is regenerated from it, so a newcomer edits the API definition and sees nothing reload.

**Expected.** Add `dev run --watch=api/**/*.py` to the canonical example.

**Repro.** Edit the API file under `api/` with `rbt dev run` running; nothing reloads.

**Where in the skills.** `python/references/lifecycle-rbtrc.md` canonical example.

**Checked at 1.6.0.** `python/references/lifecycle-rbtrc.md` lines 40-42 still watch only `backend/api/**/*.py` and `backend/src/**/*.py`. Whether 1.6.0 scaffolds still use a top-level `api/` was not verified.
