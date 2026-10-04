---
id: cineloop-09
project: cineloop
source: "cineloop/reboot-findings.md §9 (Part 1)"
reboot_version: 1.4.1
severity: unrated
target: positive
names:
  - python/references/state-nested-models.md
tags: [pattern, auth]
cluster: "E"
still_applies: unknown
status: Resolved
resolved_by: "python/references/patterns-cross-actor-reads.md § Do this"
---

# Do not return raw state; return a per-caller view

**What happened.** `ShowingState.seats` carries `held_by` (another patron's user ID) and their hold deadline; returning it would leak both. The API declares two models: `Seat` (stored) and `SeatView` (sent). The view adds `mine: bool` computed against the caller and blanks `hold_expires_at` for everyone else's holds. The reader is the natural place because it already has `context.auth`. This also simplified the frontend: the browser never needs user IDs.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Positive pattern; kept as a candidate for a `patterns-*` reference (proposal task E). The plugin gap is item 18.
