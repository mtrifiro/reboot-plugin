---
id: airport-1-01
project: airport-1
source: "airport-1/FINDINGS.md § Plugin skills, item 1"
reboot_version: 1.6.0
severity: yellow
target: plugin
names:
  - build/SKILL.md
  - python/references/state-collections.md
  - python/references/state-actor-decomposition.md
tags: [negative-space, pattern]
cluster: ""
still_applies: no
status: Resolved
resolved_by: "build/SKILL.md § Naming domain objects"
mechanism: prose
---
# Nothing tells the design to name a state type for what it holds, not for its key

**What happened.** The design named the per-gate, per-day lock `GateDay`, after its id (`A1:2026-10-11`), not after what it holds. The developer asked what it was, called the name unexplanatory, and it went through two renames (`GateDaySchedule`, then the user's own pick `GateSchedule`), each touching the API, servicers, feature files and generated code. `Day`, a day's list of flights, has the same flaw.

**Expected.** A naming rule in the design phase, applied before the API file is written: a state type is named for what it holds and is for, in the user's nouns (`GateSchedule`: one gate's flights and closures for a day), never for its key or time period (`GateDay`, `Day`). The test: someone in the domain knows what it holds from the name alone. The build's own model is a good name: `Stay`, not `GuestNight`.

**Repro.** Design any app whose lock is keyed by two things (a gate and a day, a room and a night); the key-shaped name comes first.

**Where in the skills.** `build/SKILL.md`, State Model Assessment item 7 ("Identity") and Design Phase item 4 ("State the design"), which say how an id is chosen but nothing about the type's name; `python/references/state-collections.md` and `state-actor-decomposition.md`, whose examples name types well but never state the rule. Suggested change: add to State Model Assessment "Name each type for what it holds, in the user's nouns, never for its id or key; show the names in the first map so the user can change them before the API is written."

**Resolution (2026-10-11).** `build/SKILL.md` § Naming domain objects (plugin 19a8059): name each state type for what it holds, never its key (`GateSchedule`, not `GateDay`), test each name on someone in the domain, flag key- or period-shaped names such as `Day` before showing the design, and propose names before the API is written.
