---
id: cineloop-21
project: cineloop
source: "cineloop/reboot-findings.md Part 2 §H"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/lifecycle-initialize-hook.md
tags: [seeding, error-text]
cluster: "C"
still_applies: unknown
status: Open
resolved_by: ""
---

# lifecycle-initialize-hook.md: say when aliases are needed before it bites (seeding loops)

**What happened.** The reference documents `.idempotently("alias")` but frames it around calling the same method twice. Seeding a catalog is a loop: 12 `Theater.create` calls (fine, distinct actors) interleaved with 12 `chain.register_theater` calls (not fine, same actor). What matters is per-actor, and the wording 'calling that same method on the same actor again' is accurate but easy to skim past when the code looks like one uniform loop.

**Expected.** Add 'Seeding loops are the common case': a loop creating N actors needs no aliases; a loop registering each into a shared index calls the same method on the same actor N times and each needs a distinct alias (`await chain.idempotently(f"reg-{theater.id}").register_theater(context, theater_id=theater.id)`).

**Repro.** Not recorded.

**Where in the skills.** `python/references/lifecycle-initialize-hook.md`; proposal task C (`lifecycle-seeding.md`).

**Checked at 1.6.0.** `python/references/lifecycle-initialize-hook.md` lines 12-17 and section at line 78 now state the same-method-same-actor rule and the error text, but still no seeding-loop framing or loop example. Partly addressed; judged unknown.
