---
id: agentic-demo-08
project: agentic-demo
source: "v 1.4.1 Reboot/Archive/agentic-demo/docs/reboot-learnings.md §9"
reboot_version: 1.4.0
severity: unrated
target: plugin
names:
  - python/references/servicer-reader.md
tags: [negative-space, pattern]
cluster: ""
duplicate_of: returns-desk-08
still_applies: yes
status: Open
resolved_by: ""
---

# An aggregating reader on actor X saw other actors as of X's last write

**What happened.** `DemoRun.invariants` is a `Reader` that fans out `.get(context)` calls to every order, case, inventory, refund and attempt in the run. Polled over one-shot HTTP, it returned byte-identical responses forever: the values were the world as of the `DemoRun` actor's own last write (seed time), not the current state of the actors it read; `min_observed_quantity` still showed the pre-reservation value minutes after the reservation committed. The author's reading: reads issued from a `ReaderContext` are snapshot-consistent with the host actor's version, so a read-mostly aggregator actor serves a frozen world. Fix: give the aggregator a reason to advance. Each attempt workflow now writes `note_attempt_settled` to the `DemoRun` when it reaches a terminal state, which records completion and moves the snapshot; the next poll showed live values.

**Expected.** `servicer-reader.md` documents that an aggregating reader on actor X sees other actors as of X's last write, and says to design aggregators so the interesting events also touch X.

**Repro.** Not recorded beyond the description: poll a fan-out reader hosted on a read-mostly actor over one-shot HTTP after the actors it reads change.

**Where in the skills.** `python/references/servicer-reader.md`.

**Checked at 1.6.0.** grep for snapshot, consistent and last write in `servicer-reader.md`, `patterns-cross-actor-reads.md` and `rpc-forall.md` finds nothing on this. The cause is the author's inference ("apparently"), not confirmed from source; compare showtime-27, which verified that reactive subscriptions do propagate through fan-out readers. agentic-demo's learnings file repeats returns-desk's text for this section (it is the same file with §11 added); see returns-desk-08.
