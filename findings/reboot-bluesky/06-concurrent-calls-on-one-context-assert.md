---
id: reboot-bluesky-06
project: reboot-bluesky
source: "REBOOT_FINDINGS.md §6"
reboot_version: 1.4.1
severity: unrated
target: framework
names: []
tags: [error-text, seeding]
cluster: "4.4"
still_applies: unknown
status: Open
resolved_by: ""
---

# Concurrent top-level calls on one context fail with an internal assertion

**What happened.** Driving parallel transactions from a single `InitializeContext` via `asyncio.gather` (seeding 20 accounts) failed inside the runtime: `AssertionError: Transaction '<id>' missing for state type 'skyline.v1.Directory'`, plus cascading `cygrpc` errors from `Participant/Abort`. The 'one context, one call at a time' rule is documented for tests, but the failure mode when violated is an opaque internal assertion.

**Expected.** Detect concurrent use of a context and raise a clear 'contexts are not safe for concurrent calls; create one per caller' error.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.
