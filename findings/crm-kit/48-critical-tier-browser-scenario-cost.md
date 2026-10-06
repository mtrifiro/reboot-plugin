---
id: crm-kit-48
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §6"
reboot_version: 1.6.0
severity: unrated
target: plugin
names:
  - python/references/testing-web-app.md
  - python/references/testing-features.md
tags: [testing, cost]
cluster: "D"
duplicate_of: reboot-crm-33
still_applies: no
status: Resolved
resolved_by: "python/references/testing-web-app.md § Never"
---

# Tag a small @critical tier; a browser scenario costs about 11 s against 1.5 s for a backend one

**What happened.** A full serial sweep is about 30 minutes. A browser scenario costs about 11 s (a Vite server each; module-scoped fails `already serving`), a backend one about 1.5 s. Rule: tag a small `@critical` tier (about 2 minutes) to run before every commit and mark browser scenarios `browser`; tags become pytest marks.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.

**Checked at 1.6.0.** `python/references/testing-web-app.md` (line ~276, § Never) says a shared `frontend` fixture fails `already serving`, and its errors table indexes it; `testing-features.md` § Limits notes the dashboard does not show custom tags such as `@critical` though `-m` selects them.
