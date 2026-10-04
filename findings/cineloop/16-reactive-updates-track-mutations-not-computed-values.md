---
id: cineloop-16
project: cineloop
source: "cineloop/reboot-findings.md Part 2 §C"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - web-app/references/react-client.md
  - python/references/react-generated-client.md
  - python/references/scheduling-basic.md
tags: [negative-space, pattern, frontend]
cluster: "E"
still_applies: yes
status: Open
resolved_by: ""
---

# Document: reactive means it must be a real mutation

**What happened.** `react-client.md` explains that readers are reactive but nothing states the consequence: a lazily-computed state change is invisible to other viewers. 'The kind of bug you ship, demo successfully in one tab, and discover in front of an audience with two.'

**Expected.** Add to `react-client.md` (cross-referenced from `scheduling-basic.md`): reactive updates track mutations, not computed values. If a reader derives a status at read time (a lapsed hold, an expired offer, a stale session) nothing changed, so no other subscriber is notified. Any transition users should watch happen needs a scheduled writer that commits it. Keep the lazy computation too: the schedule gives liveness, the computation gives correctness if the schedule is late.

**Repro.** Not recorded.

**Where in the skills.** `web-app/references/react-client.md`, `python/references/scheduling-basic.md`.

**Checked at 1.6.0.** No statement of the rule in `web-app/references/react-client.md`, `python/references/react-generated-client.md` (reader hooks as push-based subscriptions at line ~115) or `scheduling-basic.md`.
