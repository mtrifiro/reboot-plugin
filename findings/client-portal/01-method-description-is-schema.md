---
id: client-portal-01
project: client-portal
source: "client-portal/reboot-findings.md §1"
reboot_version: 1.6.0
severity: unrated
target: plugin
names:
  - python/references/api-schema-evolution.md
  - python/references/api-methods.md
tags: [negative-space, error-text]
cluster: "4.1"
duplicate_of: reboot-crm-10
still_applies: yes
status: Open
resolved_by: ""
---

# Editing a method's description is a schema change

**What happened.** Cost: the app refused to start. `api-schema-evolution.md` explains that fields, methods and state types are compared against the schema the persisted state was written with, but not that the comparison covers a method's whole options block, prose included. Boot failed with "Updated state or method definitions are not backwards compatible. - Reboot options for method `tick` of servicer type `portal.v1.portal.Portal` updated from... description: ... to... description: ...". Two reworded sentences, no behaviour change, and the application would not boot. The only ways out are to restore the stored wording or `rbt dev expunge`, which discards every actor. Not caught sooner because hot reloads all session were additive (new fields, new methods), which pass; the rejection only appeared on a full restart, hours after the edit. The author left accurate wording in comments beside both methods (`api/portal/v1/portal.py`, `tick` and `request_sync`).

**Expected.** Treat `description=` on an existing method as immutable once state exists: get the wording right before the first run that persists anything; after that, bank rewordings for the next expunge.

**Repro.** Reword a method's `description=` after state exists, then fully restart `rbt dev run`.

**Where in the skills.** `python/references/api-schema-evolution.md`.

**Checked at 1.6.0.** `python/references/api-schema-evolution.md` does not say method `description=` is part of the compared schema (it uses `description=` only in an example, lines ~123-131).
