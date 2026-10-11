---
id: reboot-crm-52
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P3.16"
reboot_version: 1.6.0
severity: yellow
target: bdd
names: []
tags: [testing, error-text]
cluster: "4.4"
still_applies: unknown
status: Resolved
resolved_by: "python/references/testing-features.md § Errors you will see"
---

# reboot.bdd: a Given/When eventually has is refused with an Almost that hides the fix

**What happened.** `Given as "alice", `get` ... eventually has `poggio.status="ready"` within 20 seconds` fails with "Almost: a Given or When 'has' saves what it reads now; 'eventually has' asserts, under a Then". The rule is fine; the message stops one sentence short.

**Expected.** Extend the message with "move this step under `Then` (a later `Given` may follow it)", since that is the fix. Same class as reboot-crm-13 (the runtime knows the answer and declines to say it).

**Repro.** Write an `eventually has` step under a Given or When.

**Where in the skills.** Not applicable to a skill unless an error-index row is added.

**Checked at 1.6.0.** `python/references/testing-features.md` mentions `eventually has` (line ~249) but not this error text (grep for `Almost`).
