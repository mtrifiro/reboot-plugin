---
id: theater-network-05
project: theater-network
source: "theater-network/docs/reboot-findings.md §5"
reboot_version: 1.4.0
severity: unrated
target: plugin
names:
  - python/references/rpc-constructor-calls.md
  - python/references/servicer-constructor.md
tags: [negative-space]
cluster: "4.1"
still_applies: unknown
status: Resolved
resolved_by: "python/references/servicer-constructor.md § Limits"
---

# Constructors compose only so deep

**What happened.** `Transaction -> Writer-factory` is the proven nesting (a transaction that creates an actor via its writer factory). Deeper compositions, transaction factories calling transaction factories that construct stdlib actors, were part of the original hang tangle.

**Expected.** Keep creation shapes shallow and boring (the source's guidance).

**Repro.** Not recorded beyond the description above.

**Where in the skills.** Constructor reference Limits section.

**Checked at 1.6.0.** No nesting-depth guidance found in `python/references/rpc-constructor-calls.md` or `servicer-constructor.md`. Whether the hang still occurs on 1.6.0 was not tested.
