---
id: returns-desk-07
project: returns-desk
source: "v 1.4.1 Reboot/Archive/returns-desk/docs/reboot-learnings.md §8"
reboot_version: 1.4.0
severity: unrated
target: plugin
names:
  - python/references/servicer-transaction.md
tags: [cost, pattern, error-text]
cluster: ""
still_applies: yes
status: Open
resolved_by: ""
---

# Barrier-released transactions on one actor spiral into 30 s lock timeouts; keep aggregators out of the participant set

**What happened.** 20 attempt workflows held at a coordinator barrier, then released to commit against a single `ServiceCase` actor: every transaction after the first few fails with `aborted with 'Unavailable': Timed out waiting 30.0s to acquire exclusive lock; retry the transaction` and retries after backoff; convergence takes minutes at N=20 (the test's 120 s wait expired). Same family as theater-network's bunched transactions, with a precise trigger: a barrier that de-staggers commits is the worst case for per-actor lock acquisition. N=2 shows no measurable convoy. The author's fix: the 20-way test drops the barrier (natural serialization through the case's event-writer calls spreads the commits); the visible 2-way demo keeps it. Addendum: the convoy generalizes to any hot actor a transaction touches. Adding a `DemoRun.register_refund` call inside `commit_refund` serialized every losing case's refund commit on the single run actor, and 19 concurrent commits re-created the spiral with no barrier.

**Expected.** A rule of thumb in `servicer-transaction.md`: a transaction's participant set is its lock set; keep aggregators, registries and dashboards out of it, and let the workflow write to them after commit with a `per_workflow` scope.

**Repro.** 20 workflows released together from a barrier, each committing a transaction on the same actor.

**Where in the skills.** `python/references/servicer-transaction.md`.

**Checked at 1.6.0.** `servicer-transaction.md` § Limits documents the 30 s lock deadline and the `Unavailable` abort, § Errors you will see has the timeout string, and § Scales as says a transaction on a hot actor stalls every user writer on it (showtime-42). Nothing covers barrier-released herds or says to keep aggregators, registries and dashboards out of a transaction's participants. Compare theater-network-18 (same family, but there the failure is the `database.cc` worker assert).
