---
id: reboot-crm-10
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P1.4"
reboot_version: 1.6.0
severity: red
target: plugin
names:
  - python/references/api-schema-evolution.md
tags: [negative-space, error-text, contradiction]
cluster: "4.1"
still_applies: yes
status: Resolved
resolved_by: "python/references/api-schema-evolution.md § Do this"
---

# Editing a method's description= is a backwards-incompatible change, and nothing says so

**What happened.** Two method descriptions had "colour" changed to "color" and nothing else changed. `rbt dev run` refused to boot: "Updated state or method definitions are not backwards compatible ... - Reboot options for method `roster` of servicer type `crm.v1.crm.Team` updated from... reader { } description: ... to..." and sat at "waiting for modification, or hit `x` to expunge"; the only way to keep data was to restore the old spelling. It bit because the dev loop's watcher restarts on generated-code changes under `backend/api/`, so an intermediate API had been booted and persisted without anyone starting it deliberately. A reviewer's note in the source: the following entry (reboot-crm-11) is the same rule hit a day earlier on a different method.

**Expected.** A description is documentation (shown on the dashboard and in generated clients). `api-schema-evolution.md` lists compatible changes (`mcp=` option changes are fine) but says nothing about descriptions, and its own migration example edits one. Source fix list: (1) exclude `description` from the comparison (recommended); (2) list it in the table and make the error say "descriptions are part of the frozen schema"; (3) skill, today: the reference gains a row and a warning, and the example at lines ~123-131 that edits a `description=` currently teaches a boot refusal. Same finding as student-sor-17 and client-portal-01.

**Repro.** Reword a method's `description=` after the app has persisted state; restart `rbt dev run`.

**Where in the skills.** `python/references/api-schema-evolution.md` compatibility table and migration example.

**Upstream.** Reboot intends to push an upstream fix that lets a method's description change after it is created (noted 2026-10-10). When it ships, drop the rule from the skills and the method-description check from `hooks/schema-guard/schema.ts`.

**Checked at 1.6.0.** `api-schema-evolution.md` has no row for descriptions, and the example at lines ~123-131 still changes `description=` strings with no warning.
