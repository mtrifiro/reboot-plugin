---
id: returns-desk-03
project: returns-desk
source: "v 1.4.1 Reboot/Archive/returns-desk/docs/reboot-learnings.md §4"
reboot_version: 1.4.0
severity: unrated
target: plugin
names:
  - python/references/api-errors.md
tags: [pattern]
cluster: ""
still_applies: yes
status: Open
resolved_by: ""
---

# A rejection counter cannot live inside the transaction that rejects; the loser records it after the abort

**What happened.** Corollary of item 2: incrementing `rejected_commits` inside the aborting transaction is rolled back with the abort. The workflow that catches the typed error records the prevention instead (`record_event(outcome="PREVENTED")` on the case, `note_rejected_reservation` on inventory).

**Expected.** A sentence in `api-errors.md` ("rejections are recorded by the loser, after the abort"), since every invariant-board-style UI needs it.

**Repro.** Not recorded.

**Where in the skills.** `python/references/api-errors.md`.

**Checked at 1.6.0.** `api-errors.md` § Do this and `patterns-error-handling.md` § Never say a raised `<Method>Aborted` rolls back every change the method made; neither draws the corollary that a count of rejections must be written by the catcher after the abort.
