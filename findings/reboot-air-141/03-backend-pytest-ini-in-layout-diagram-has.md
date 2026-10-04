---
id: reboot-air-141-03
project: reboot-air-141
source: "reboot-air/REBOOT_FINDINGS.md §3"
reboot_version: 1.4.1
severity: green
target: plugin
names:
  - web-app/SKILL.md
  - python/references/testing-project-setup.md
tags: [scaffold, index-gap]
cluster: "B"
still_applies: unknown
status: Open
resolved_by: ""
---

# backend/.pytest.ini in layout diagram has no contents nearby

**What happened.** The web-app layout diagram showed `backend/.pytest.ini  # pythonpath: src/ api/ ../api/`, a comment that looks like file contents but is not valid ini, and whose paths do not obviously match the layout (is `api/` `backend/api/` or project-root `api/`?). The real contents live in `testing-project-setup.md`, which the build flow does not point to until step 12, six steps after the shell is scaffolded. The author wrote the file at scaffold time from the comment and planned to re-check it at test time.

**Expected.** Either drop the file from the layout diagram (a test-phase concern covered by step 12) or inline the three real lines.

**Repro.** Not recorded.

**Where in the skills.** `web-app/SKILL.md`, Project Layout.

**Checked at 1.6.0.** Partly changed. `web-app/SKILL.md:484` now lists a root-level `pytest.ini  # testpaths: tests; pythonpath: backend/src backend/api api` and `python/references/testing-project-setup.md` has a `pytest.ini` section, but the layout still carries a comment rather than contents and the build flow still reads it late. Not clearly fixed.
