---
id: student-sor-06
project: student-sor
source: "student-sor/reboot-findings.md §4b-2"
reboot_version: 1.5.0
severity: unrated
target: plugin
names:
  - python/references/stdlib-ordered-map.md
tags: [negative-space, cost, contradiction, error-text]
cluster: "D"
still_applies: yes
status: Resolved
resolved_by: "python/references/stdlib-ordered-map.md § Scales as"
---

# Lock waits on OrderedMap inserts from concurrent transactions: throughput one sixth of sequential

**What happened.** Retried with four students in flight, no reads inside the transaction, and every shared actor touched in one fixed order (Student, then Terms in calendar order, then Institution). It did not stall, but throughput fell from about six students a minute (sequential) to about one, and the log filled with a traceback per cancelled wait through `ordered_map_servicer.py` `_Insert` -> `transactionally` -> `_transaction_participant_start` -> `acquire_shared` -> `_wait`, ending `asyncio.exceptions.CancelledError` and `ERROR:asyncio:Future exception was never retrieved`. Concurrent transactions that each insert into the same `OrderedMap` (the student index; a term's roster) queue on the map's node locks, time out and are retried. Reverted to one student at a time.

**Expected.** The stdlib reference says `OrderedMap` "stores entries across many Node actors so concurrent writes scale"; that appears not to hold for writes from concurrent transactions, or there is a setting the author could not find. Guidance on bulk loading into an `OrderedMap` from transactions.

**Repro.** `GROWTH_CONCURRENCY = 4` in the project's `backend/src/seed.py` (see student-sor-07 for the repro with a fresh `rbt dev expunge`).

**Where in the skills.** `python/references/stdlib-ordered-map.md` (line ~21).

**Checked at 1.6.0.** `python/references/stdlib-ordered-map.md` line 21 still claims concurrent writes scale and gives no caveat for writes from concurrent transactions.
