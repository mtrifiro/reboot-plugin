---
id: plugin-browser-02
project: plugin-browser
source: "plugin-browser/FINDINGS.md § reboot.bdd, item 2"
reboot_version: 1.6.0
severity: green
target: bdd
names:
  - python/references/testing-features.md
tags: [testing, error-text]
cluster: ""
still_applies: yes
status: Resolved
resolved_by: "python/references/testing-features.md § Errors you will see"
---
# Arguments after the actor get a bare "Step definition is not found", no "Almost" hint

**What happened.** ``When "alice" does an `explain` on `CodeNote` of "note-x" with `code="ChatGPT"` and …`` failed with `StepDefinitionNotFoundError`. The step wants the arguments first: ``does an `explain` with `code="ChatGPT"` and … on `CodeNote` of "note-x"``.

**Expected.** An "Almost: …" message, as for other near-misses, or the order stated in the reference; it is shown only by example (the `sign_up` scenario).

**Repro.** Put a `with` clause list after ``on `<Type>` of "<id>"`` in a `does a` step.

**Where in the skills.** `python/references/testing-features.md` (state the order), or an "Almost" step in `reboot/bdd/steps.py`.

**Resolution (2026-10-10).** Rows in `testing-features.md` § Errors you will see: a backtick inside a quoted value; `with` clauses after the actor; a recall inside a JSON5 literal.
