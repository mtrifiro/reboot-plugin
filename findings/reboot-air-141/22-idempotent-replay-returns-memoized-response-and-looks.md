---
id: reboot-air-141-22
project: reboot-air-141
source: "reboot-air/REBOOT_FINDINGS.md §23"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/patterns-idempotency.md
tags: [negative-space, seeding]
cluster: "4.1"
still_applies: yes
status: Open
resolved_by: ""
---

# Idempotent replay returns memoized response and looks like a fresh run

**What happened.** `initialize` published the schedule one service day per transaction, each under `.idempotently(f"Publish schedule for {date}")`, and summed the returned `flights_created` to log what it did. On every restart the log claimed "Published 540 flights" when only 180 (one new day) were new. A replayed idempotent call returns the memoized response from its first execution, original counts and all; the method body does not run, so the servicer's early-return reporting `flights_created=0, already_seeded=True` is never reached and the caller gets the first run's `already_seeded=False, flights_created=180` forever. Cost: a misleading startup log for weeks, then a real API change (a `schedule_status` reader so `initialize` could ask which days were genuinely new). Any caller that branches on an idempotent method's response (counts, `created` flags, timestamps) has the same trap.

**Expected.** One sentence in `patterns-idempotency.md`: a replayed idempotent call returns the memoized response from its first execution, the method body does not run, so response fields describing what happened describe the first execution. Consider a framework `response.was_replayed` marker.

**Repro.** Not recorded.

**Where in the skills.** `python/references/patterns-idempotency.md`.

**Checked at 1.6.0.** Still absent. The word "memoiz" does not appear in `python/references/patterns-idempotency.md` (grep for memoiz / replay returned nothing).
