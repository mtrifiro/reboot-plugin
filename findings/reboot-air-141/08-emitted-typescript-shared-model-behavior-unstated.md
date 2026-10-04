---
id: reboot-air-141-08
project: reboot-air-141
source: "reboot-air/REBOOT_FINDINGS.md §8"
reboot_version: 1.4.1
severity: green
target: plugin
names:
  - python/references/react-generated-client.md
tags: [negative-space, frontend]
cluster: "4.1"
still_applies: yes
status: Open
resolved_by: ""
---

# Emitted TypeScript shared-model behavior unstated

**What happened.** Downstream half of finding §1. The author still could not tell whether `FleetResponse.planes` comes back as the same `PlaneDetails` type that `Plane.details` returns or a structural clone. A bounded grep of the generated `fleet_rbt_types.ts` showed codegen inlines the schema at each use site rather than referencing a shared one. TypeScript structural typing makes this harmless in practice, but only because shapes match. The only way to resolve it was to look at the generated file, which the skill says not to do.

**Expected.** One line in the "Naming Rules" section: shared models are emitted structurally at each use site, and the exported `z.infer` type for a shared model is safe to annotate components with.

**Repro.** Not recorded.

**Where in the skills.** `python/references/react-generated-client.md`.

**Checked at 1.6.0.** No statement found in `python/references/react-generated-client.md` (grep for shared model / reuse / inline returned nothing relevant).
