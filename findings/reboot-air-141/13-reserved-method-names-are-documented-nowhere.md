---
id: reboot-air-141-13
project: reboot-air-141
source: "reboot-air/REBOOT_FINDINGS.md §13"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/api-methods.md
  - python/references/api-pydantic.md
tags: [negative-space, error-text]
cluster: "4.1"
still_applies: yes
status: Open
resolved_by: ""
---

# Reserved method names are documented nowhere

**What happened.** A `Flight` type with a `schedule` factory method fails at codegen: `Error processing 'airline/v1/fleet.proto': Reboot method 'airline.v1.FlightMethods/Schedule' has illegal name: Schedule is reserved`. `schedule` is reserved because `ref.schedule(...)` is the framework's deferred-call API, but no reference lists it or any other reserved name. Cost: one codegen failure and a rename late enough that the request model, servicer, and seed caller all changed together.

**Expected.** A "Reserved method names" subsection in `api-methods.md` listing `schedule` and whatever else the generator rejects (the author guesses `create`, `read`, `write`, `ref`, `spawn`, `idempotently` are plausible, unverified).

**Repro.** Not recorded.

**Where in the skills.** `python/references/api-pydantic.md` / `api-methods.md`.

**Checked at 1.6.0.** Still present. Grep for "reserved" across `python/references/`, `web-app/`, and `mcp-ui/` finds only the `REBOOT_*`/`RBT_*` secrets prefix and nothing on method names.
