---
id: reboot-bluesky-10
project: reboot-bluesky
source: "REBOOT_FINDINGS.md §10"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/state-collections.md
  - python/references/stdlib-ordered-map.md
tags: [version-drift]
cluster: "A"
still_applies: unknown
status: Open
resolved_by: ""
---

# uuid7 is a doc-recommended but unmanaged dependency

**What happened.** The references recommend UUIDv7 keys (`from uuid7 import create as uuid7`) but the `uuid7` package is a third-party dependency the app must discover and pin itself.

**Expected.** Re-export a uuid7 helper from `reboot` (or vendor one) so the canonical pattern works out of the box.

**Repro.** Not recorded.

**Where in the skills.** `state-collections.md`, `stdlib-ordered-map.md`.

**Checked at 1.6.0.** python/references/state-collections.md:188 and stdlib-ordered-map.md:120 still import `uuid7`; I did not verify whether `uuid7` is declared in the project-setup pyproject template.
