---
id: constellation-07
project: constellation
source: "v 1.4.1 Reboot/constellation/docs/reboot-learnings.md §2026-08-16 — initial build"
reboot_version: 1.4.0
severity: unrated
target: positive
names:
  - python/references/servicer-workflow-external.md
tags: [pattern]
cluster: ""
still_applies: unknown
status: Open
resolved_by: ""
---

# Call a synchronous client through asyncio.to_thread inside the at_least_once callable

**What happened.** `youtube-transcript-api` 1.x is synchronous, so it is called through `asyncio.to_thread(...)` inside the `at_least_once` callable.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.

**Checked at 1.6.0.** Grep of `skills/` for `to_thread`, blocking and sync client found nothing; `servicer-workflow-external.md` examples use async clients only.
