---
id: client-portal-02
project: client-portal
source: "client-portal/reboot-findings.md §2"
reboot_version: 1.6.0
severity: unrated
target: plugin
names:
  - python/references/api-pydantic.md
  - python/references/api-methods.md
  - upgrade/migrations/1.6.0/transaction-mode.md
tags: [cost, negative-space, pattern]
cluster: "D"
still_applies: no
status: Obsolete
resolved_by: ""
---

# Transaction(mode=Exclusive()) on a method that does not write its own state

**What happened.** Cost: 216 deadlocks, 125 aborted tasks, zero documents published. `Portal.index_document` reads `self.state.documents_index_id` and writes a different actor (the documents `OrderedMap`). It was declared `Exclusive()`, which takes the portal's lock for the whole transaction, so every note indexed held the portal against every other writer: `IndexDocumentAborted: TransactionShouldRetry { reason: PRESUMED_DEADLOCK }` and `Transaction ... waited longer than 250ms for state '...' of type 'portal.v1.Portal', which is held by the older transaction ...; aborting so that the older transaction proceeds.` `api-pydantic.md:196` says `Shared()` is "the choice for a transaction that mostly reads its own state while writing others, such as the root of a tree of states." Bonus finding: changing a transaction's `mode` is not rejected by the schema gate (verified empirically by booting after the change; not in the compatibility table either way).

**Expected.** Pick the mode from what the body touches: writes its own state is `Exclusive()`; reads its own state and writes others is `Shared()`.

**Repro.** Declare `Exclusive()` on a transaction that only reads its own state and writes another actor; run it concurrently for many documents.

**Where in the skills.** `python/references/api-pydantic.md` (~line 191-196) and `python/references/api-methods.md`.

**Checked at 1.6.0.** `api-pydantic.md` (lines ~191-196), `api-methods.md` (lines ~27-28) and `upgrade/migrations/1.6.0/transaction-mode.md` now give exactly this rule (body assigns own state means exclusive, only calls others means shared), and 1.6.0 `rbt generate` refuses a transaction with no declared mode. Not checked: the claim that a `mode` change passes the schema gate.
