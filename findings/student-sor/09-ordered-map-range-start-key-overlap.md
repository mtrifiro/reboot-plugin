---
id: student-sor-09
project: student-sor
source: "student-sor/reboot-findings.md §4d"
reboot_version: 1.5.0
severity: unrated
target: framework
names:
  - python/references/stdlib-ordered-map.md
tags: [negative-space, contradiction]
cluster: "8.4"
still_applies: unknown
status: Resolved
resolved_by: "python/references/stdlib-ordered-map.md § Limits"
---

# OrderedMap.range with a start_key returns rows from before the key at one node boundary

**What happened.** Paging the 2,014-row student index in pages of 200 with `range(start_key=<last key>+"\x00", limit=200)`, every page came back sorted and started at the cursor except one. With the cursor just past `S101600`, the page started at `S101537`: 64 rows that sort below the cursor and had been delivered on the previous page, followed by the correct continuation. No key was lost; a naive recount over-counted (term totals 52 to 64 high) and a list page shows those rows twice. It looks like the walk resumes from the start of the leaf holding the key when the key sits at (or just past) a node boundary. The author's `range_page` in `servicers/common.py` drops rows below the cursor and judges "more pages" on the raw page size (a first version judged on the trimmed page, ended early and hid 278 students).

**Expected.** The stdlib reference documents `start_key` as inclusive; a note on this, or a fix.

**Repro.** Page the student index with `range(start_key=<last key>+"\x00", limit=200)`; the per-page log is the project's `backend/src/seed.py` (`seed_v7`), which prints first/last key, sort order and rows below the cursor.

**Where in the skills.** `python/references/stdlib-ordered-map.md` (paging example, `start_key` inclusive, line ~190).

**Checked at 1.6.0.** `python/references/stdlib-ordered-map.md` line ~190 documents `start_key` as inclusive and shows paging; no note about rows before the cursor.
