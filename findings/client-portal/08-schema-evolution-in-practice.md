---
id: client-portal-08
project: client-portal
source: "client-portal/reboot-findings.md §8"
reboot_version: 1.6.0
severity: unrated
target: plugin
names:
  - python/references/api-schema-evolution.md
tags: [negative-space]
cluster: "4.1"
still_applies: unknown
status: Resolved
resolved_by: "python/references/api-schema-evolution.md § Do this"
---

# Schema evolution in practice (what reloads accept and reject)

**What happened.** Verified across roughly a dozen reloads: adding a field with a default and a new tag (17-23) accepted; adding a method (`rename`, `members`) accepted; adding a request/response model accepted; changing `Transaction` `mode=` accepted; rewording an existing `description=` rejected (client-portal-01); deleting a field never attempted (docs are unambiguous). Because fields cannot be deleted, `sync_notes_fetched` and `folders` remain in the API after their features were dropped; their descriptions now say they are unused and why.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** `python/references/api-schema-evolution.md` compatibility table.

**Checked at 1.6.0.** Not fully compared; `api-schema-evolution.md` has no row for `mode=` changes or `description=` rewording (grep).
