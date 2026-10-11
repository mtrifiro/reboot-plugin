---
id: client-portal-05
project: client-portal
source: "client-portal/reboot-findings.md §5"
reboot_version: 1.6.0
severity: unrated
target: plugin
names:
  - python/references/servicer-workflow.md
tags: [pattern, negative-space]
cluster: "E"
still_applies: unknown
status: Resolved
resolved_by: "python/references/servicer-workflow-external.md § Limits"
---

# A workflow's memoized steps include its view of the world

**What happened.** `at_least_once("List vault", ...)` memoizes the first successful result per workflow instance, which makes replays consistent, but a pass resumed after a long outage faithfully fetches a vault that has moved on. The author watched a three-hour-old pass re-download a pre-trim listing of a vault that had lost half its files. To get a fresh value during a replay, use an alias that has never run: `at_least_once("Capture claim time", ...)` executes on the replay because nothing memoized it, while `"Capture start time"` returns the original; that difference is the mechanism behind the age check.

**Expected.** Age out old passes; use a never-run alias when a fresh value is needed during a replay.

**Repro.** Not recorded.

**Where in the skills.** `python/references/servicer-workflow.md` (memoization and alias sections).

**Checked at 1.6.0.** `servicer-workflow.md` (lines ~19-39) explains memoization across replays but a grep did not find the stale-view consequence or the fresh-alias trick; not exhaustively read.
