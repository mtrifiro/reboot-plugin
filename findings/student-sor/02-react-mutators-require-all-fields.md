---
id: student-sor-02
project: student-sor
source: "student-sor/reboot-findings.md §2"
reboot_version: 1.5.0
severity: unrated
target: plugin
names:
  - python/references/react-generated-client.md
tags: [contradiction, frontend, scaffold]
cluster: "4.2"
duplicate_of: reboot-air-141-16
still_applies: yes
status: Resolved
resolved_by: "python/references/react-generated-client.md § Limits; python/references/react-generated-client.md § Do this"
---

# Generated React mutators require every request field; the reference says they are partial

**What happened.** `tsc` rejects `inst.addTerm({ code, name, status })` because `startDate`, `endDate`, `asActor` and `asActorLabel` are missing; `app.beginReview({})` is rejected for the same reason. Twenty call sites failed type-checking. Reader hooks (`useListStudents({ cursor, limit })`) are fine. Workaround: a `NO_ACTOR` constant spread into every mutation call (`web/src/ui.tsx`) plus explicit zero values. Same as reboot-air-11.

**Expected.** `react-generated-client.md`: "A mutation's argument type is `Partial<Method>Request`", and "`partialRequest` is optional and partial — every field has a default." Either the generated mutator types should be `Partial<...>` as documented, or the reference should say all fields are required.

**Repro.** Not recorded.

**Where in the skills.** `python/references/react-generated-client.md` (lines ~42-68).

**Checked at 1.6.0.** `python/references/react-generated-client.md` lines 42-68 still say mutation arguments are `Partial<Method>Request`.

**Resolution note.** `web-app/references/react-client.md` makes no claim that requests are partial (grep, 2026-10-04), so the fix in `react-generated-client.md` closes the contradiction.
