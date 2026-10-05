---
id: reboot-crm-69
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P3.30"
reboot_version: 1.6.0
severity: yellow
target: bdd
names:
  - python/references/testing-features.md
tags: [testing, error-text]
cluster: "4.1"
still_applies: unknown
status: Resolved
resolved_by: "python/references/testing-features.md § Limits"
---

# eventually has aborts on an actor that does not exist yet

**What happened.** A scenario asks for a logo and a workflow creates the `Logo` actor a moment later. The step `Then as "alice", `get` on the `Logo` for "acme.dev" eventually has ... within 10 seconds` failed at once with `StateNotConstructed`: the step opens a reactive read (`reboot/bdd/steps.py:1103`) and the read aborts rather than waiting for the actor. Workaround: a custom step that reads in a loop and treats `StateNotConstructed` as not yet.

**Expected.** "Eventually" to cover the actor coming into being, since a workflow creating it is the ordinary way it happens.

**Repro.** Not recorded.

**Where in the skills.** `python/references/testing-features.md` (`eventually has`).

**Checked at 1.6.0.** Not found documented in `python/references/testing-features.md` by grep; not read in full.
