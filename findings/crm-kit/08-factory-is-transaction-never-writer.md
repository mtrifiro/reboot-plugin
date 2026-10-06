---
id: crm-kit-08
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §2"
reboot_version: 1.6.0
severity: unrated
target: plugin
names:
  - python/references/api-schema-evolution.md
  - python/references/state-actor-decomposition.md
tags: [negative-space, contradiction]
cluster: "4.1"
duplicate_of: reboot-crm-12
still_applies: no
status: Resolved
resolved_by: "python/references/state-actor-decomposition.md § Never; python/references/api-schema-evolution.md § Limits"
---

# Declare every factory as Transaction(mode=Exclusive(), factory=True); a Writer constructor cannot be promoted later

**What happened.** A `Writer` factory cannot call other actors, so it cannot construct an `OrderedMap` or a child actor. That need arrives after data exists, and a constructor cannot move from `Writer` to `Transaction` against persisted state (the boot is refused). Nested factory transactions work unchanged at two levels deep. §11 adds: `api-schema-evolution.md` says `Writer` <-> `Transaction` is compatible, but it is refused for a constructor.

**Expected.** Every constructor is `Transaction(mode=Exclusive(), factory=True)`, never `Writer(factory=True)`.

**Repro.** Not recorded.

**Where in the skills.** `api-schema-evolution.md` (§11).

**Checked at 1.6.0.** `python/references/state-actor-decomposition.md` § Never (line ~94) says start a constructor that may create another actor as `Transaction(mode=Exclusive(), factory=True)`; `api-schema-evolution.md` § Limits (line ~151) records the refusal observed at 1.6.0. The canonical reboot-crm-12 is still marked Open.
