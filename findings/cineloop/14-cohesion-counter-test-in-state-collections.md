---
id: cineloop-14
project: cineloop
source: "cineloop/reboot-findings.md Part 2 §A"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/state-collections.md
  - python/references/state-actor-decomposition.md
tags: [negative-space, pattern]
cluster: "E"
still_applies: yes
status: Resolved
resolved_by: "python/references/patterns-cross-actor-reads.md § Do this; python/references/state-collections.md § Do this"
---

# state-collections.md should name the cohesion test

**What happened.** The reference is strongly biased toward decomposition ('decompose aggressively', 'N of them = N actors'); the counter-case is stated only as a negative ('no identity, lifecycle, or methods'). Applied naively a seat looks entity-ish (domain noun, acted on individually, has a status field). What decided it, which is nowhere in the reference: seats within a showing must change atomically, so they belong to one actor. The source calls this the single most valuable addition to the whole skill set.

**Expected.** A peer of the decomposition signals in Step 1: 'Counter-test: does the collection need atomic multi-item mutation?' If one user action must change several items at once, all or none ('hold these 4 seats', 'move these 3 cards', 'reserve this whole row'), keep them inline on one actor; splitting into `Type`s turns each action into a multi-actor transaction. Cohesion beats decomposition when the items share a consistency boundary.

**Repro.** Not recorded.

**Where in the skills.** `python/references/state-collections.md` Step 1.

**Checked at 1.6.0.** `python/references/state-collections.md` Step 1 and the decision flow (line ~328) test only identity/lifecycle/own methods; no atomic-multi-item-mutation counter-test (grep for cohesion/change together found nothing). `api-pydantic.md:437` mentions 'consistency boundary' only in passing.
