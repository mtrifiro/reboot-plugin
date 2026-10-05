---
id: reboot-air-150-10
project: reboot-air-150
source: "reboot-air/reboot-findings.md §10"
reboot_version: 1.5.0
severity: unrated
target: plugin
names:
  - python/references/scheduling-basic.md
  - python/references/servicer-writer.md
tags: [contradiction, negative-space, cost]
cluster: "4.1"
duplicate_of: reboot-crm-14
still_applies: yes
status: Resolved
resolved_by: "python/references/scheduling-basic.md § Do this; python/references/servicer-writer.md § Never"
---

# A writer cannot schedule work on another actor (only a transaction can); the reference implies otherwise

**What happened.** `scheduling-basic.md`, "Schedule Other Actors, Not Just `self`", shows `await Account.ref(other_id).schedule(when=...).interest(context)` with no context type stated. From a `WriterContext` mypy rejects it: the generated `schedule()` overloads for another actor's ref take only `TransactionContext`. `servicer-writer.md` says a writer can "schedule work on itself", so the two references read as a contradiction. Workaround: schedule a method on `self` that then reaches the other actor. Subtlety: if that method is a Transaction, it takes the actor's write lock while it runs (~400 ms), so a second click on the same flight queues behind it (hold latency 58 ms to 500 ms back-to-back); making it a Workflow avoids the lock (80-105 ms back-to-back).

**Expected.** The scheduling reference should say plainly: from a Writer, `self.ref().schedule()` only; from a Transaction, any ref.

**Repro.** Call `Account.ref(other_id).schedule(...)` from a Writer; run `mypy`.

**Where in the skills.** `python/references/scheduling-basic.md` ("Schedule Other Actors, Not Just `self`") and `python/references/servicer-writer.md`.

**Checked at 1.6.0.** `python/references/scheduling-basic.md` lines ~80-88 still say `ref.schedule(...)` works on any ref with no context-type caveat.
