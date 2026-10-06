---
id: constellation-01
project: constellation
source: "v 1.4.1 Reboot/constellation/docs/reboot-learnings.md §2026-08-16 — YouTube rate limiting (bug + fix)"
reboot_version: 1.4.0
severity: unrated
target: plugin
names:
  - python/references/servicer-workflow-external.md
  - python/references/scheduling-basic.md
tags: [pattern, negative-space]
cluster: ""
still_applies: yes
status: Open
resolved_by: ""
---

# A rate-limited external call needs a durable backoff through a writer, not a raise

**What happened.** Pasting a ~60-video playlist fired all import workflows at once; YouTube rate-limited the IP and the transcript library raised `IpBlocked`, a subclass of `CouldNotRetrieveTranscript`, so the "permanent failure" handler swallowed it and marked healthy videos `failed`. Fix pattern: catch `IpBlocked`/`RequestBlocked` before the base class, surface it as `{"throttled": "1"}` data, and have the workflow call a writer that marks the video `throttled` and reschedules `import_video` with exponential backoff via `self.ref().schedule(when=timedelta(...))`. Routing the reschedule through a writer keeps the durable delay in its canonical home (writer-context `schedule(when=)`); raising from the `at_least_once` callable instead would retry immediately via replay and hammer the rate limiter harder.

**Expected.** Not recorded.

**Repro.** `YouTubeTranscriptApi().list(id)` succeeds while `.fetch()` raises `IpBlocked` after a burst of requests.

**Where in the skills.** Not recorded.

**Checked at 1.6.0.** `python/references/servicer-workflow-external.md` § Limits says "No built-in retry budget or backoff on either primitive", and § Do this shows backoff only as an in-callable `asyncio.sleep(2**attempt)` loop returning exhaustion as data. Grep of `python/references/` for backoff / rate limit / throttle found no pattern for a durable delayed retry via a writer's `schedule(when=)`.
