---
id: cineloop-13
project: cineloop
source: "cineloop/reboot-findings.md §13 (Part 1)"
reboot_version: 1.4.1
severity: unrated
target: positive
names:
  - python/references/api-errors.md
  - web-app/references/react-client.md
tags: [pattern, frontend]
cluster: "E"
still_applies: unknown
status: Open
resolved_by: ""
---

# Typed errors are the contract with the UI

**What happened.** `SeatUnavailableError(seat_ids=[...])`, `CartLimitError(limit, already_held, requested)` and `NoHeldSeatsError` each carry the payload the interface needs ('F-11 and F-12 were just taken' with the map re-rendering those red; 'That's 8 seats already'; 'Your hold expired while you were checking out'). Generic exceptions would have collapsed all three into 'something went wrong'. Because `<Method>Aborted` also rolls back the writer's mutations, the failure path needed no cleanup code.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Positive pattern; kept as a candidate for a `patterns-*` reference (proposal task E).
