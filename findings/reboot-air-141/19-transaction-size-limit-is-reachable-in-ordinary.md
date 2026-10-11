---
id: reboot-air-141-19
project: reboot-air-141
source: "reboot-air/REBOOT_FINDINGS.md §20"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/servicer-transaction.md
  - python/references/lifecycle-initialize-hook.md
tags: [negative-space, cost, seeding]
cluster: "C"
still_applies: yes
status: Resolved
resolved_by: "python/references/servicer-transaction.md § Limits"
---

# Transaction size limit is reachable in ordinary seeding and undocumented

**What happened.** Seeding the flight schedule creates one actor per flight inside a `Transaction`, batched with `asyncio.gather`, the shape `servicer-transaction.md` recommends. At 138 flights it worked. At 360 the app hung and filled the log with repeated lock waits (`await self._wait(mode=Lock.Mode.EXCLUSIVE, deadline=deadline)` / `await asyncio.wait_for(waiter.future, timeout=timeout)`) and never came up. Nothing says a transaction has a practical size ceiling or that touching one `OrderedMap` root from hundreds of inserts in a single transaction pushes it over. The fix that worked, not in any reference: split work into transactions of roughly the proven size and give each call its own idempotency alias, because `lifecycle-initialize-hook.md` auto-generates one key per (actor, method) and a second bare call to the same method on the same actor is an error, e.g. `await airline.idempotently(f"Publish schedule for {service_date}").seed_schedule(context, start_date=service_date, days=1)` in a per-day loop. The failure is a hang, and the log points at an internal lock rather than transaction size.

**Expected.** Say something concrete in `servicer-transaction.md`: a transaction holds locks on every actor it touches for its whole duration; hundreds of constructor calls plus a shared stdlib index in one transaction can exceed the lock deadline; remedy is to split into several transactions, with a pointer to the `.idempotently(alias)` rule. Even a rough order of magnitude ("tens, not hundreds") would help.

**Repro.** Not recorded.

**Where in the skills.** `python/references/servicer-transaction.md`.

**Checked at 1.6.0.** Still absent. `python/references/servicer-transaction.md` has no transaction-size or lock-duration guidance (grep for size / hundreds / tens found nothing; only line 20 on lock modes). The `.idempotently` alias rule is documented in `python/references/lifecycle-initialize-hook.md:78-109`, but not linked to size.
