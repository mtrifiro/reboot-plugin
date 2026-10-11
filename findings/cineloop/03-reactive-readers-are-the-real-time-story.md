---
id: cineloop-03
project: cineloop
source: "cineloop/reboot-findings.md §3 (Part 1)"
reboot_version: 1.4.1
severity: unrated
target: positive
names:
  - python/references/react-generated-client.md
  - web-app/references/react-client.md
tags: [pattern, frontend]
cluster: "E"
still_applies: unknown
status: Resolved
resolved_by: "python/references/patterns-react-state.md § Never; python/references/patterns-cross-actor-reads.md § Do this"
---

# Reactive readers are the whole real-time story

**What happened.** 'Live for all viewers' needed no pub/sub, websocket code, `Topic` or polling, only making `seat_map` a `Reader`. Corollary: anything that should appear live must be an actual state mutation. The first instinct for hold expiry was purely lazy (compute 'expired' at read time, never write); that is correct but invisible, because viewer B's screen does not update when viewer A's hold lapses. The fix kept the lazy check AND added a scheduled writer that really releases the seats. 'If a state transition is only computed, not committed, no one else will ever see it happen.'

**Expected.** Not recorded.

**Repro.** Two viewers; one hold lapses.

**Where in the skills.** Positive pattern; kept as a candidate for a `patterns-*` reference (proposal task E). The plugin gap is item 16.
