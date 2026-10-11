---
id: actor-flight-03
project: actor-flight
source: "reboot-findings.md §3"
reboot_version: 1.5.0
severity: unrated
target: positive
names: []
tags: [pattern, testing]
cluster: "E"
still_applies: unknown
status: Open
resolved_by: ""
---

# Things that worked and are worth documenting

**What happened.** (a) `at_least_once` takes an async callable returning a plain `dict`, and passing that dict's lists straight into a generated writer's list-of-Model fields (`types=result["types"]`) validates cleanly; the reference only shows scalars. (b) `reactively().get()` from the test harness was the right way to wait for a scheduled workflow's first result and its next refresh after touching a file (`test_browser_gets_the_graph_and_it_refreshes`). (c) The generated React hook for a large state (about 110 edges and 70 methods as nested Models) re-renders in one piece on every refresh; no partial updates observed.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded (a thing that worked).
