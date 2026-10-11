---
id: cineloop-05
project: cineloop
source: "cineloop/reboot-findings.md §5 (Part 1)"
reboot_version: 1.4.1
severity: unrated
target: positive
names:
  - python/references/servicer-writer.md
  - python/references/patterns-idempotency.md
tags: [pattern]
cluster: "E"
still_applies: unknown
status: Resolved
resolved_by: "python/references/patterns-time-and-randomness.md § Do this"
---

# Determinism is a design constraint: derive ids that must be re-addressed

**What happened.** Writer/transaction bodies may be re-executed (transient retries, dev effect validation), so any persisted non-deterministic value is suspect. Three resolutions: order IDs use `_order_id(user_id, sequence)`, a SHA-256 of the patron plus their monotonic order number, instead of `uuid4()`, so a retry re-addresses the same actor; confirmation codes are derived from the same inputs; the orders-index ID is derived from the user ID and persisted in a real `orders_index_id` field (persisted so `rbt inspect` sees the edge, derived so a retry cannot allocate two indexes). The one deliberate exception is `hold_expires_at = now() + 120` (see item 6).

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Positive pattern; kept as a candidate for a `patterns-*` reference (proposal task E).
