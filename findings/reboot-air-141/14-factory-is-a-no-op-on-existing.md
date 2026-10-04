---
id: reboot-air-141-14
project: reboot-air-141
source: "reboot-air/REBOOT_FINDINGS.md §14"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/api-schema-evolution.md
  - python/references/servicer-constructor.md
  - python/references/rpc-constructor-calls.md
  - python/references/state-collections.md
tags: [contradiction, negative-space, error-text]
cluster: "4.1"
still_applies: yes
status: Open
resolved_by: ""
---

# Factory is a no-op on existing actor so new ID field is never back-filled

**What happened.** `api-schema-evolution.md` says adding a field with a zero default is compatible. `state-collections.md` says a reference to another actor must be a persisted ID field on the parent, allocated once in the constructor (`uuid4()`). The author added `flights_index_id` to `AirlineState` and allocated it in `found`, the `factory=True` constructor. On restart the app crashed: `InvalidStateRefError: The 'state_id' option must be at least 1 character(s) long; the given value is 0 character(s) long`. Because the `Airline` actor already existed, `Airline.found(...)` was a no-op (`rpc-constructor-calls.md` says so), the constructor body never ran, and the field stayed `""`; `OrderedMap.ref("")` then failed. The two rules are individually correct and jointly break every existing deployment; it fails only on the second run, so a fresh scaffold passes local testing.

**Expected.** A row in `api-schema-evolution.md`'s "Evolving Safely" playbook: adding a reference/ID field to an existing type should be allocated lazily at first use (`if self.state.x == "":`), not in the constructor. Cross-link from `state-collections.md`'s "allocate it once in the constructor" sentence.

**Repro.** Add an ID field to an existing type's state, allocate it in the factory constructor, restart against persisted state with the actor already created.

**Where in the skills.** `python/references/api-schema-evolution.md`, `servicer-constructor.md`, `rpc-constructor-calls.md`, and `state-collections.md`.

**Checked at 1.6.0.** Still present. `python/references/state-collections.md:196-204` still shows allocating the index ID in `if context.constructor:`; `python/references/api-schema-evolution.md` has no lazy-allocation row for ID fields (its only lazy mention, line 140, is about migrating data fields in writers).
