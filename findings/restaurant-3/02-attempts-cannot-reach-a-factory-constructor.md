---
id: restaurant-3-02
project: restaurant-3
source: "restaurant-3/FINDINGS.md § reboot.bdd, item 1"
reboot_version: 1.6.0
severity: yellow
target: bdd
names:
  - python/references/testing-features.md
tags: [negative-space, testing]
cluster: ""
still_applies: yes
status: Open
resolved_by: ""
---
# The built-in `attempts` step cannot reach a factory constructor

**What happened.** `World.call` resolves the method on `Type.ref(id)`, where a `factory=True` constructor is not defined, so a scenario that must assert a constructor's declared error (an occupied table on `Check.open`) has no built-in step. The design made `open` a plain transaction on a caller-minted id with an "already opened" guard instead.

**Expected.** `"hana" attempts an `open` ... on `Check` of "check-1"` to call the factory and record its abort, as `creates` does for the happy path.

**Repro.** Declare `open=Transaction(factory=True, ...)`, write an `attempts an `open`` step.

**Where in the skills.** `python/references/testing-features.md` ("Attempts, aborts, tasks") does not say constructors are out of reach of `attempts`.
