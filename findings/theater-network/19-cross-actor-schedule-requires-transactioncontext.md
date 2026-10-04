---
id: theater-network-19
project: theater-network
source: "theater-network/docs/reboot-findings.md §19"
reboot_version: 1.4.0
severity: unrated
target: plugin
names:
  - python/references/scheduling-basic.md
  - python/references/servicer-writer.md
tags: [negative-space, error-text]
cluster: "4.1"
duplicate_of: reboot-crm-14
still_applies: yes
status: Open
resolved_by: ""
---

# Cross-actor schedule() requires a TransactionContext

**What happened.** A Writer can schedule ONLY itself. The generated overloads for scheduling another actor's method accept `TransactionContext` alone. `scheduling-basic.md`'s 'Schedule Other Actors' section does not say this, and the mypy error from a `WriterContext` is an opaque union-attr/overload mismatch. This is why `Seat.expire` and `Cart.expire_hold` are declared `Transaction` despite doing no cross-actor calls. (Writer to Transaction is a schema-compatible change, so converting is safe.) Each foreign actor a transaction schedules onto is enlisted in its two-phase commit (item 20).

**Expected.** Not recorded.

**Repro.** Schedule another actor's method from a `WriterContext`; observe the opaque mypy overload error.

**Where in the skills.** `python/references/scheduling-basic.md` 'Schedule Other Actors' section.

**Checked at 1.6.0.** `python/references/scheduling-basic.md` lines 80-88 show `Account.ref(other_id).schedule(...)` on any ref with no mention of the `TransactionContext` requirement; `servicer-writer.md:84-98` says a writer schedules on its own actor only.
