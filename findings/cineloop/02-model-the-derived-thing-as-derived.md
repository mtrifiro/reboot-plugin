---
id: cineloop-02
project: cineloop
source: "cineloop/reboot-findings.md §2 (Part 1)"
reboot_version: 1.4.1
severity: unrated
target: positive
names:
  - python/references/state-actor-decomposition.md
tags: [pattern]
cluster: "E"
still_applies: unknown
status: Open
resolved_by: ""
---

# Model the derived thing as derived; do not give it state (no Cart actor)

**What happened.** The spec says 'cart'; no `Cart` actor was built. A patron's cart IS 'the seats on this showing currently held by me', derived in the `seat_map` reader. A hold and a cart can never disagree, the 2-minute expiry needs no cart-side cleanup, and checkout needs no cart/showing reconciliation. Rule: before adding a state `Type`, ask whether it is a projection of state you already have. The cost of a wrong `Type` is high (schema evolution is additive-only once state persists) and readers are cheap and reactive.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Positive pattern; kept as a candidate for a `patterns-*` reference (proposal task E).
