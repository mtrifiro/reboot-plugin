---
id: showtime-47
project: showtime
source: "2026.08.18 reboot-findings.md Suggested skill improvements, bullet 4"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/servicer-reader.md
  - python/references/react-generated-client.md
tags: [negative-space, index-gap, pattern]
cluster: "4.1"
duplicate_of: reboot-crm-30
still_applies: yes
status: Resolved
resolved_by: "python/references/patterns-cross-actor-reads.md § Do this"
---

# Document cross-actor reactive propagation for Readers

**What happened.** Nothing in `servicer-reader.md` or `react-generated-client.md` says whether a subscription to a Reader that reads other actors re-fires when those actors change. It does (showtime-27), and it decides between 'aggregate in a fan-out reader' (clean) and 'denormalize counts on the write path through one bottleneck actor'.

**Expected.** One sentence: 'reactive subscriptions track every read the ReaderContext makes, including cross-actor reads.'

**Repro.** Not recorded.

**Where in the skills.** `servicer-reader.md`, `react-generated-client.md`.

**Checked at 1.6.0.** python/references/servicer-reader.md:61-66 says calling other actors 'propagates the ReaderContext' and nothing about subscriptions; react-generated-client.md:112-116 says any session's mutation re-renders readers but not that cross-actor reads are tracked.
