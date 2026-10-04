---
id: team-memo-0826-06
project: team-memo-0826
source: "2026.08.26 Findings for Reboot Team - Docs, Skills, and Runtime.md §6"
reboot_version: 1.4.1
severity: unrated
target: framework
names: []
tags: [error-text]
cluster: "4.4"
still_applies: unknown
status: Open
resolved_by: ""
---

# The runtime's effect-validation log links to a 404

**What happened.** Every dev-mode effect-validation message points to `https://docs.reboot.dev/develop/side_effects`, which returns 404; the live page is `https://docs.reboot.dev/learn_more/side_effects/`. The stale path is baked into 1.4.1 at `reboot/aio/internals/middleware.py:271` and `reboot/aio/memoize.py:185` (both built from `DOCS_BASE_URL` in `reboot/settings.py`).

**Expected.** Fix the two format strings, or add a docs-site redirect from `/develop/side_effects` (cheaper, and repairs every shipped release).

**Repro.** Not recorded.

**Where in the skills.** Not recorded.
