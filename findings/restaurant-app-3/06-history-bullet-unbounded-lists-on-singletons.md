---
id: restaurant-app-3-06
project: restaurant-app-3
source: "restaurant-app-3/FINDINGS.md § Plugin skills, item 3"
reboot_version: 1.6.0
severity: yellow
target: plugin
names:
  - build/SKILL.md
  - python/references/state-collections.md
tags: [negative-space, cost, pattern]
cluster: ""
still_applies: yes
status: Resolved
resolved_by: "build/SKILL.md § Design Phase"
---
# "History" in the design step leads to unbounded lists on singletons

**What happened.** `build/SKILL.md`'s Design Phase asks, per rule someone will later have to explain, for "the events the owning state records: who, when, which step, the provider's reference". It does not say where the events go. This build put a `history: list[Event]` on each long-lived singleton (Floor, Menu, Staff, Waitlist). The floor's list grows with every seating, every night, and each write re-serializes all of it. `state-collections.md` warns against exactly this (an invented `MAX_ITEMS` "is Shape C in disguise"), but the two pieces of advice never meet.

**Expected.** One sentence on the History bullet: events go on the short-lived entity they explain (a check, a reservation, an order), or into an `OrderedMap` or per-day actor; never appended to a singleton that lives as long as the app. Link `state-collections.md` § Scales as.

**Repro.** Follow the History bullet for a rule enforced by a singleton.

**Where in the skills.** `build/SKILL.md`, Design Phase, History; `python/references/state-collections.md` (Scales as; Shape C).

**Resolution (2026-10-10).** The History bullet in the build skill's Design Phase says where events live: on the short-lived entity they explain or in an `OrderedMap` or per-day actor, never on an app-lifetime singleton; the `design-ready-for-both` eval gains a `history-placement` grader.
