---
id: cineloop-36
project: cineloop
source: "cineloop/reboot-findings.md §26 (Part 4)"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/lifecycle-initialize-hook.md
  - python/references/api-schema-evolution.md
tags: [seeding, pattern]
cluster: "C"
still_applies: unknown
status: Resolved
resolved_by: "python/references/api-schema-evolution.md § Do this; python/references/lifecycle-initialize-hook.md § Do this"
---

# A new index needs a backfill, and the dashboard is where you notice

**What happened.** Adding the sales ledger to a chain that already had orders produced a dashboard reporting $668 of online sales against 0 orders, because revenue is derived from seats (durable since the first sale) while the order count came from an index that started empty. The seats are the record of truth, so the backfill reads them (`Showing.sold_orders`, distinct real order ids on sold seats). The backfill must be ordered deterministically; sold seats do not record when they were bought, so backfilled entries are keyed by order ID rather than purchase time (groups the oldest page by patron); sales recorded afterwards are in true purchase order. This limitation is documented in the method.

**Expected.** Rule from the source: when you add an index or counter to a system that already has the underlying data, ship the backfill in the same change.

**Repro.** Add a ledger/index to an app with existing data and show it next to a derived figure.

**Where in the skills.** Candidate for `lifecycle-seeding.md` / schema-evolution guidance (proposal task C).

**Checked at 1.6.0.** No backfill-with-new-index guidance found in `python/references/lifecycle-initialize-hook.md` or `api-schema-evolution.md`; not conclusive.
