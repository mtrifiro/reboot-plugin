---
id: showtime-24
project: showtime
source: "2026.08.18 reboot-findings.md #24"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/lifecycle-initialize-hook.md
tags: [seeding, pattern]
cluster: "C"
still_applies: yes
status: Open
resolved_by: ""
---

# `.idempotently("<versioned-alias>")` in initialize as a dev-state migration tool

**What happened.** `create` is a no-op on an existing actor, so new denormalized fields stay empty after an additive schema change; a `set_catalog` writer called with alias `catalog-v2` runs exactly once against existing state, with no expunge and no data loss. Bump the alias to re-run. Caveat: migration-time recomputation can drift from create-time data. The catalog rebuilt `starts_at_ms` with the same 'today at 14:00' formula as seeding, but `Showing.create` is a no-op on existing actors, so if the aliased migration runs on a different day than first seed, catalog times diverge from the Showings' persisted times.

**Expected.** Derive migration payloads from persisted state (or only truly immutable inputs), not by re-running seed-time computations.

**Repro.** Not recorded.

**Where in the skills.** Not recorded; relevant home is a seeding/initialize reference (proposal task C).

**Checked at 1.6.0.** python/references/lifecycle-initialize-hook.md:78-109 covers `.idempotently("alias")` only for repeated calls in `initialize`; the versioned-alias-as-migration pattern and the drift caveat are not present (grep `migrat` in that file found nothing).
