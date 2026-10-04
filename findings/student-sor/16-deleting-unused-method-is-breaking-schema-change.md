---
id: student-sor-16
project: student-sor
source: "student-sor/reboot-findings.md §10"
reboot_version: 1.5.0
severity: unrated
target: framework
names:
  - python/references/api-schema-evolution.md
tags: [negative-space, error-text]
cluster: "4.1"
still_applies: yes
status: Open
resolved_by: ""
---

# Deleting an unused method is a backwards-incompatible schema change

**What happened.** Moving the record indexes out of the Institution removed six of its methods and three fields from a response model. `rbt dev run` then refused to restart: "Updated state or method definitions are not backwards compatible. ... - Field `student_count` was removed from Pydantic model `sor.v1.sor.InstitutionSummaryResponse`. - Method `list_students` was deleted from servicer type `sor.v1.sor.Institution` ... Backwards incompatibility encountered ... waiting for modification, or hit `x` to expunge". `--on-backwards-incompatibility` offers only `ask`, `expunge` and `fail`; there is no "proceed, I know". Removing a method, or a field from a response (not state) model, cannot break stored data, so a refactor that only shrinks an API forces compatibility stubs or a wipe. The author chose the wipe because the demo seed is deterministic; a real deployment could not. The check also fires for a changed `description=` string on a method (see student-sor-17).

**Expected.** A `proceed` option, or treating deleted methods and response-model fields as compatible.

**Repro.** Not recorded.

**Where in the skills.** `python/references/api-schema-evolution.md`.

**Checked at 1.6.0.** `python/references/api-schema-evolution.md` (lines ~165-185) still lists only revert or expunge as options.
