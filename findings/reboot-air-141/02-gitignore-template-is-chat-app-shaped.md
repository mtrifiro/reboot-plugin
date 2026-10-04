---
id: reboot-air-141-02
project: reboot-air-141
source: "reboot-air/REBOOT_FINDINGS.md §2"
reboot_version: 1.4.1
severity: yellow
target: plugin
names:
  - python/references/lifecycle-project-setup.md
  - web-app/SKILL.md
tags: [scaffold]
cluster: "B"
still_applies: yes
status: Open
resolved_by: ""
---

# gitignore template is chat-app-shaped

**What happened.** The `.gitignore` template ignores `frontend/api/` and `frontend/dist/`. A Web App has no `frontend/` directory; per the web-app skill's layout, generated React output goes to `web/src/api` and the bundle to `web/dist`. Copying the template verbatim commits generated code and the production bundle. Silent failure: roughly 10k lines of regenerated TypeScript in every diff.

**Expected.** Either parameterize the shared template paths (`frontend/` for chat apps, `web/` for web apps) or have `web-app/SKILL.md` carry its own `.gitignore` block, as it already does for `.rbtrc` generate lines.

**Repro.** Not recorded.

**Where in the skills.** `python/references/lifecycle-project-setup.md` (`.gitignore` block) versus `web-app/SKILL.md` (Project Layout).

**Checked at 1.6.0.** Still present. `python/references/lifecycle-project-setup.md` `.gitignore` block still lists `frontend/api/` and `frontend/dist/`; `web-app/SKILL.md` has no `.gitignore` block (grep for gitignore in web-app returned nothing).
