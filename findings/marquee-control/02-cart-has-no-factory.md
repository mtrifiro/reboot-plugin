---
id: marquee-control-02
project: marquee-control
source: "v 1.4.1 Reboot/Archive/marquee-control/docs/reboot-learnings.md §2026-08-17 build session, bullet 2"
reboot_version: 1.4.1
severity: unrated
target: positive
names:
  - python/references/patterns-idempotency.md
  - python/references/servicer-constructor.md
tags: [pattern]
cluster: ""
still_applies: no
status: Resolved
resolved_by: "python/references/patterns-idempotency.md § First-write setup in a type with no factory"
---

# A per-visitor Cart has no factory method, so the first write constructs it

**What happened.** Following theater-network's convention, `Cart` has no factory: a factory classmethod aborts `StateAlreadyConstructed` on the browser's second visit; with no factory, the first ref-call write constructs implicitly.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** `patterns-idempotency.md`, `servicer-constructor.md`.

**Checked at 1.6.0.** `patterns-idempotency.md` § First-write setup in a type with no factory says a factory-less type is constructed by its first writer call; `servicer-constructor.md` notes a second constructor call aborts `StateAlreadyConstructed`.
