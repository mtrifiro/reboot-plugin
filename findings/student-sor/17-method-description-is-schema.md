---
id: student-sor-17
project: student-sor
source: "student-sor/reboot-findings.md §11"
reboot_version: 1.5.0
severity: unrated
target: plugin
names:
  - python/references/api-schema-evolution.md
  - python/references/api-methods.md
tags: [negative-space, error-text]
cluster: "4.1"
duplicate_of: reboot-crm-10
still_applies: yes
status: Resolved
resolved_by: "python/references/api-schema-evolution.md § Do this"
---

# A method's description= is treated as schema

**What happened.** Changing only the `description` string of a method in the API (no change to request, response, errors or kind) makes `rbt dev run` refuse to start with "Updated state or method definitions are not backwards compatible", listing "Reboot options for method `enroll` ... updated from ... to ..." with the two description texts. Documentation on a method is therefore frozen once the app has state. Field descriptions and `Type(...)` descriptions did not trigger the check; confirmed at scale on 2026-09-07: 495 field descriptions added in one edit and the app restarted and served its existing state. Only the method's `description=` is schema. Seen on Reboot 1.5.0 on 2026-09-07. Workaround: keep a method's rules in the servicer method's docstring and leave the API text alone.

**Expected.** Not recorded (the author notes this is the opposite of what one wants from documentation).

**Repro.** Not recorded.

**Where in the skills.** `python/references/api-schema-evolution.md`, `python/references/api-methods.md`.

**Checked at 1.6.0.** `python/references/api-schema-evolution.md` does not say method `description=` is schema (it uses `description=` only in an additive-playbook example, lines ~123-131); the upgrade migration `upgrade/migrations/1.5.0/method-description-out-of-mcp-options.md` is related but is about MCP options.
