---
id: marquee-control-16
project: marquee-control
source: "v 1.4.1 Reboot/Archive/marquee-control/docs/reboot-learnings.md §2026-08-17 build session, bullet 15"
reboot_version: 1.4.1
severity: unrated
target: positive
names:
  - python/references/lifecycle-seeding.md
tags: [seeding, cost]
cluster: ""
duplicate_of: showtime-19
still_applies: no
status: Resolved
resolved_by: "python/references/lifecycle-seeding.md § Scales as"
---

# Effect validation re-runs every writer at seed; with inline seats the 48-showing seed still takes about 10 s

**What happened.** Effect validation re-runs every writer in dev (`Re-running method Showing.Create to validate effects`), so the 48-showing seed does about 96 create executions on first boot; still only about 10 s. Inline 200-seat construction is a non-event compared with theater-network's 216-actor builds.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** `lifecycle-seeding.md`. Same observation as showtime-19.

**Checked at 1.6.0.** `lifecycle-seeding.md` § Scales as says effect validation roughly doubles mutation latency and how to disable it for large seeds; `servicer-writer.md` § Errors you will see explains `Re-running method`.
