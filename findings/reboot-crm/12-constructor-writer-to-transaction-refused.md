---
id: reboot-crm-12
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P1.6"
reboot_version: 1.6.0
severity: red
target: plugin
names:
  - python/references/api-schema-evolution.md
  - python/references/servicer-constructor.md
  - python/references/state-actor-decomposition.md
tags: [contradiction, negative-space, error-text]
cluster: "4.1"
still_applies: yes
status: Resolved
resolved_by: "python/references/api-schema-evolution.md § Errors you will see; python/references/state-actor-decomposition.md § Never"
---

# A constructor cannot change from Writer to Transaction, though the table says the kind change is compatible

**What happened.** `Pipeline.create` was a `Writer(factory=True)`. It needed to construct an `OrderedMap` at creation (a transaction on another actor, which a writer cannot call), so it became `Transaction(mode=Exclusive(), factory=True)`, the shape `Leads.create` already has. The dev loop refused to boot on the existing pipeline: "Reboot options for method `create` of servicer type `crm.v1.crm.Pipeline` updated from... writer { constructor { } } to... transaction { ... }". `api-schema-evolution.md` lists "Change a method between `Writer` and `Transaction`" as compatible "only when the other options on the method (e.g. `factory=True`) stay the same"; they did stay the same, but a `Transaction` carries a `mode`, and that or the constructor flag is enough to refuse it. Workaround: the writer stays a writer and the map is constructed by its first `insert`; `address()` catches `OrderedMap.SearchAborted` on the search before the first insert.

**Expected.** Either the change is allowed for constructors, or the table's row says it is not. Source fix list: (1) allow it; (2) correct the row to "except on a constructor"; (3) add the design rule to `servicer-constructor.md` and `state-actor-decomposition.md`: declare a factory as `Transaction(factory=True)` from the start if it might ever need to construct another actor or touch a second state (recommended first, since a `Writer` factory cannot be promoted later).

**Repro.** Change an existing `Writer(factory=True)` constructor to `Transaction(mode=Exclusive(), factory=True)` against persisted state.

**Where in the skills.** `python/references/api-schema-evolution.md` (row ~line 50, text ~lines 72-73), `servicer-constructor.md`, `state-actor-decomposition.md`.

**Checked at 1.6.0.** `api-schema-evolution.md` line 50 still lists `Writer`/`Transaction` as `yes` and lines 72-73 say it is legal when `factory=True` is unchanged, with no constructor exception; neither `servicer-constructor.md` nor `state-actor-decomposition.md` carries the design rule.

**Resolution (2026-10-10).** A row in `api-schema-evolution.md` § Errors you will see for the `writer { constructor { } } to... transaction` refusal, with the lazy-construction workaround and the rule to declare new factories as `Transaction(mode=Exclusive(), factory=True)`; `scripts/api_lint.py` notes a `Writer(factory=True)`.
