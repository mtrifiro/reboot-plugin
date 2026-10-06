---
id: constellation-03
project: constellation
source: "v 1.4.1 Reboot/constellation/docs/reboot-learnings.md §2026-08-16 — YouTube rate limiting (bug + fix)"
reboot_version: 1.4.0
severity: unrated
target: positive
names:
  - python/references/api-schema-evolution.md
tags: []
cluster: "8.4"
duplicate_of: showtime-25
still_applies: unknown
status: Resolved
resolved_by: "python/references/api-schema-evolution.md § Do this"
---

# Additive schema changes hot-reloaded over persisted dev state

**What happened.** The whole rate-limiting fix (constellation-01, -02) shipped onto a dev server with persisted state as purely additive changes (new defaulted fields, new methods); hot-reload accepted it without an expunge, "exactly as `api-schema-evolution.md` promises".

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** `python/references/api-schema-evolution.md` (named by the source as accurate).

**Checked at 1.6.0.** `python/references/api-schema-evolution.md` § Do this still teaches that over persisted state only additive changes boot (add fields, tags, methods, types).
