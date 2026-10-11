---
id: crm-kit-07
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §2"
reboot_version: 1.6.0
severity: unrated
target: plugin
names:
  - python/references/api-schema-evolution.md
tags: [negative-space, error-text]
cluster: "4.1"
duplicate_of: reboot-crm-10
still_applies: no
status: Resolved
resolved_by: "python/references/api-schema-evolution.md § Do this"
---

# A method's description= is frozen schema once the app has booted with state

**What happened.** "colour" to "color" in a method `description=` made the dev loop refuse to boot ("Updated state or method definitions are not backwards compatible ... description: ...") until the exact text came back or the data was expunged. Field descriptions and new fields, methods and `errors=` are free. `--watch` persists half-written APIs itself, so "first boot" comes early. The description is also the MCP tool description; if one goes stale, leave it and correct it in a comment beside it.

**Expected.** Write every method `description=` in final form before the app first boots with state; never edit it after.

**Repro.** Not recorded.

**Where in the skills.** `api-schema-evolution.md` (named in §11: its table omits method descriptions, and its own `deposit` example edits a shipped one).

**Checked at 1.6.0.** `python/references/api-schema-evolution.md` § Do this covers it per the canonical item reboot-crm-10.
