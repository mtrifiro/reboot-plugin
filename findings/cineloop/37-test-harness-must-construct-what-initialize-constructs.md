---
id: cineloop-37
project: cineloop
source: "cineloop/reboot-findings.md §27 (Part 4)"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/testing-harness.md
  - python/references/testing-project-setup.md
tags: [testing, seeding, error-text]
cluster: "C"
still_applies: yes
status: Resolved
resolved_by: "python/references/testing-harness.md § Do this"
---

# A test harness has to construct what initialize constructs

**What happened.** Recording each sale into the box-office ledger inside the checkout transaction broke four previously passing tests with `Admin.RecordSaleAborted: StateNotConstructed { requires_constructor: true }`. The small harness seeds one showing and nothing else, while production's `initialize` creates the box office on every boot. Same failure class as item 33 from the other direction (there the fix was to tolerate a missing actor, here to construct it). Tolerate a missing actor when what you wanted from it was decorative (a city on a receipt); construct it in the harness when the application guarantees it exists (a ledger the checkout invariant depends on); wrapping the second in a `try` would have deleted a guarantee and a test of it.

**Expected.** Add to `testing-harness.md` 'Seed what `initialize` seeds': a harness that registers real servicers but skips the real `initialize` is not running the shipped application; every singleton `initialize` constructs (chain, ledger, settings actor) must be constructed by the harness too, either by passing the production `initialize=` to `rbt.up(...)` or mirroring its constructor calls in a test-local one.

**Repro.** Cross-actor call from checkout into an actor `initialize` creates, under a harness that skips it.

**Where in the skills.** `python/references/testing-harness.md`.

**Checked at 1.6.0.** `python/references/testing-harness.md` line 107 documents the `initialize=<async fn>` option, but there is no statement that the harness must construct what `initialize` constructs, nor the `requires_constructor: true` error text.
