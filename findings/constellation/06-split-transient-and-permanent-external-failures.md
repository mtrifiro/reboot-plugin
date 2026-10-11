---
id: constellation-06
project: constellation
source: "v 1.4.1 Reboot/constellation/docs/reboot-learnings.md §2026-08-16 — initial build"
reboot_version: 1.4.0
severity: unrated
target: plugin
names:
  - python/references/servicer-workflow-external.md
tags: [pattern]
cluster: ""
still_applies: no
status: Resolved
resolved_by: "python/references/servicer-workflow-external.md § Do this; python/references/servicer-workflow-exit.md § Do this"
---

# Split transient and permanent external failures by hand in at_least_once callables

**What happened.** For YouTube: oEmbed 4xx and `CouldNotRetrieveTranscript` are permanent, so they are returned as data and the video is marked `failed`; 5xx and network errors are raised so `at_least_once` retries via replay. Getting this backwards either retries a deleted video forever or gives up on a network blip. (constellation-01 shows the classification going wrong when a transient error subclasses a permanent one.)

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.

**Checked at 1.6.0.** `python/references/servicer-workflow-external.md` § Do this: failures retry forever by replaying the workflow; return give-up outcomes as data. `servicer-workflow-exit.md` § Do this separates returning, raising a declared abort, and raising anything else (transient, replayed indefinitely), and the `at_most_once` example returns a permanent card error as data.
