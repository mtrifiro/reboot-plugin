---
id: reboot-air-150-11
project: reboot-air-150
source: "reboot-air/reboot-findings.md §11"
reboot_version: 1.5.0
severity: unrated
target: plugin
names:
  - python/references/react-generated-client.md
tags: [contradiction, frontend]
cluster: "4.1"
duplicate_of: reboot-air-141-16
still_applies: yes
status: Resolved
resolved_by: "python/references/react-generated-client.md § Limits; python/references/react-generated-client.md § Do this"
---

# Generated React mutation arguments are not Partial<...> as documented

**What happened.** `react-generated-client.md` says "A mutation's argument type is `Partial<Method>Request`" and "`partialRequest` is optional and partial — every field has a default". In practice `flight.release({ seatNumber })` fails `tsc` with `Argument of type '{ seatNumber: string; }' is not assignable to parameter of type '{ seatNumber: string; holdToken: string; quiet: boolean; }'`: every field is required. Adding a field to a request model therefore breaks every existing call site in the SPA.

**Expected.** Either the generated types should be partial (the runtime clearly applies defaults) or the reference should say they aren't.

**Repro.** Call a generated mutation with a subset of the request fields and run `tsc`.

**Where in the skills.** `python/references/react-generated-client.md`.

**Checked at 1.6.0.** `python/references/react-generated-client.md` lines 42-68 still say mutation arguments are `Partial<Method>Request`.
