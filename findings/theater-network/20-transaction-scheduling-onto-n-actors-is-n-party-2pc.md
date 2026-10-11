---
id: theater-network-20
project: theater-network
source: "theater-network/docs/reboot-findings.md §20"
reboot_version: 1.4.0
severity: unrated
target: plugin
names:
  - python/references/servicer-transaction.md
  - python/references/servicer-workflow.md
  - python/references/scheduling-basic.md
tags: [cost, negative-space, pattern]
cluster: "D"
duplicate_of: reboot-air-141-19
still_applies: yes
status: Resolved
resolved_by: "python/references/servicer-transaction.md § Never; python/references/patterns-load-and-benchmarking.md § Never; python/references/scheduling-basic.md § Never"
---

# A transaction scheduling onto N actors is an N-party 2PC; fan out in workflows

**What happened.** Occurrence 4 of the `database.cc:1374` assert came with a minimal recipe. Making room-reset clear every affected customer's cart as a transaction (capture holders, loop, `schedule()` a `Cart.clear` on each) enlisted every foreign actor as a two-phase-commit participant: one commit across the showing plus N carts, prepared simultaneously while customers' own single-cart transactions raced the same carts. The prepares collided and the database worker died within minutes of the feature shipping. Safe shape: the writer captures the holder list into the workflow's request (an additive schema field) and the WORKFLOW clears each cart with sequential plain writer calls (the fan-out items 14 and 16 proved safe at 20-concurrent for room builds).

**Expected.** Rule from the source: a transaction's participant set is its blast radius; if the work is N independent writes it belongs in a workflow no matter how convenient `schedule()` looks.

**Repro.** Transaction loop scheduling `Cart.clear` on N carts while customers transact on the same carts.

**Where in the skills.** `servicer-transaction.md`, `servicer-workflow.md`.

**Checked at 1.6.0.** `servicer-transaction.md` does not state that scheduling on a foreign actor enlists it in 2PC or recommend workflow fan-out for N independent writes.
