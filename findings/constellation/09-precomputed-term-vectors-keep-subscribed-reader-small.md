---
id: constellation-09
project: constellation
source: "v 1.4.1 Reboot/constellation/docs/reboot-learnings.md §2026-08-16 — initial build"
reboot_version: 1.4.0
severity: unrated
target: positive
names:
  - python/references/patterns-cross-actor-reads.md
tags: [cost, pattern]
cluster: ""
still_applies: unknown
status: Open
resolved_by: ""
---

# Store a compact derived vector at import time instead of re-shipping transcripts

**What happened.** Storing a ~120-term weighted vector on each `Video` at import time keeps the O(N²) similarity pass cheap and keeps full transcripts out of the graph reader the UI subscribes to.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.

**Checked at 1.6.0.** `python/references/patterns-cross-actor-reads.md` § 3. Declare summary and detail readers together teaches keeping heavy payloads out of subscribed list readers, but no reference describes precomputing a compact derived field at write time to keep a cross-actor O(N²) pass cheap (its § 2 argues the other way, deriving projections rather than storing them).
