---
id: theater-chain-01
project: theater-chain
source: "theater-chain/reboot-findings.md §1"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/scheduling-recurring.md
  - python/references/servicer-workflow.md
  - python/references/servicer-writer.md
tags: [negative-space, pattern, index-gap]
cluster: "E"
still_applies: yes
status: Open
resolved_by: ""
---

# No clock or RNG may be persisted from a Writer or Transaction

**What happened.** `WriterContext` / `TransactionContext` expose no `now`. Writer and transaction bodies re-execute under transient retries and dev-mode effect validation (log: `INFO ... Re-running method Showing.Create to validate effects`), so a value from `time.time()` or `uuid4()` differs between runs and any state derived from it diverges. This looks ordinary but is wrong: `seat.hold_expires_at_ms = int(time.time() * 1000) + 120_000; seat.hold_id = str(uuid4())`. Three ways out, in order of preference: (1) push it into the request (the caller supplies `now_ms`, `hold_id`, `order_id`, `confirmation_code`, fixed across replays; the "client can lie" objection is answered in §2); (2) derive it from something already persistent (e.g. the `OrderedMap` id `f"orders:{user_id}"` allocated once into a real `orders_index_id` field); (3) capture it in a `Workflow` via `at_least_once`, at the cost of a workflow round-trip. The exception: `when=` on `ref.schedule(...)` may use the wall clock because scheduling timing is not replay-validated. It was the single biggest design constraint of the app; any app with expiring anything hits it in the first hour.

**Expected.** Per the source, a short dedicated reference `patterns-time-and-randomness.md`, linked from the "Before the servicer" reading list, with exactly the three escape routes and the `schedule(when=...)` exception. Currently the rule is a parenthetical in `scheduling-recurring.md` and a paragraph deep in `servicer-workflow.md`.

**Repro.** Not recorded.

**Where in the skills.** `python/references/scheduling-recurring.md`, `python/references/servicer-workflow.md`; suggested new `patterns-time-and-randomness.md`.

**Checked at 1.6.0.** Still scattered. The rule appears as a parenthetical at `python/references/scheduling-recurring.md:195-203` and in `python/references/servicer-workflow.md:243,663-718`, and `python/references/servicer-writer.md:30` mentions re-execution, but there is no dedicated time/randomness reference (none in `python/references/`) and no push-it-into-the-request route.
