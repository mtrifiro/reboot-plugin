---
id: constellation-02
project: constellation
source: "v 1.4.1 Reboot/constellation/docs/reboot-learnings.md §2026-08-16 — YouTube rate limiting (bug + fix)"
reboot_version: 1.4.0
severity: unrated
target: positive
names:
  - python/references/scheduling-basic.md
tags: [pattern]
cluster: ""
still_applies: unknown
status: Open
resolved_by: ""
---

# Stagger fan-out to external APIs with scheduled start delays

**What happened.** Prevention for the rate limiting in constellation-01: `add_videos` and `retry_failed` schedule each import `3s * index` apart via a `start_delay_seconds` field on the create/retry-later requests.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.

**Checked at 1.6.0.** No reference describes staggering scheduled work to spare an external API (grep for stagger / rate limit). `python/references/scheduling-basic.md` § Limits warns that retry backoff can re-synchronize tasks scheduled apart and that a restart fires every past-due timer at once, which bears on how long such a stagger holds.
