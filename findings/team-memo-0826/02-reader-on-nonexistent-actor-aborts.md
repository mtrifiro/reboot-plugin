---
id: team-memo-0826-02
project: team-memo-0826
source: "2026.08.26 Findings for Reboot Team - Docs, Skills, and Runtime.md §2"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/rpc-refs.md
tags: [negative-space, contradiction, error-text]
cluster: "4.1"
duplicate_of: cineloop-33
still_applies: yes
status: Resolved
resolved_by: "python/references/rpc-refs.md § Do this"
---

# A reader on a non-existent actor can abort rather than return zero state

**What happened.** The `rpc-refs` skill says a reader call on a non-existent actor 'returns the zero-valued state.' On 1.4.1, calling a declared reader on an unconstructed actor of a type with an explicit `factory=True` constructor aborts with `StateNotConstructed` (observed calling `Event.details` from `initialize` before the event existed). The zero-state claim may hold only for types with implicit constructors.

**Expected.** The skill should say which types it applies to.

**Repro.** Not recorded.

**Where in the skills.** `rpc-refs.md`.

**Checked at 1.6.0.** python/references/rpc-refs.md:105 still says a reader call on a non-existent actor returns the zero-valued state, with no factory exception.
