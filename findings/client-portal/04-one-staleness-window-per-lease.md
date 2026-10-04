---
id: client-portal-04
project: client-portal
source: "client-portal/reboot-findings.md §4"
reboot_version: 1.6.0
severity: unrated
target: plugin
names:
  - python/references/servicer-workflow.md
tags: [pattern, negative-space]
cluster: "E"
still_applies: unknown
status: Open
resolved_by: ""
---

# One staleness window, not two (lease release)

**What happened.** Cost: the portal parked itself; no pass could run at all. The claim in client-portal-03 is the holding pass's `started_at`, so "is this claim worth honouring" and "is this pass worth running" are the same question. The app first answered with two windows, a 30-minute pass-age limit and a 4-hour claim expiry, creating a deadlock by policy: the holder was too old to work but its claim too young to ignore, and the only pass that could release it was the one standing down (`now (UTC): 22:32:17`, `claim: 19:44:59`, 2.79 h old, inside the 4 h window, honored).

**Expected.** One window (`SYNC_PASS_MAX_AGE_SECONDS`), and a pass that stands down for age releases the claim if it holds it. Any lease needs an answer to "who releases this if the holder never runs again?"

**Repro.** Not recorded.

**Where in the skills.** `python/references/servicer-workflow.md` (lease/claim pattern, once one exists).

**Checked at 1.6.0.** No reference covers lease or claim expiry design (grep of `servicer-workflow.md` found none); not specifically verified elsewhere.
