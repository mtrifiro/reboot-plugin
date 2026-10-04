---
id: reboot-crm-26
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P1.16"
reboot_version: 1.6.0
severity: red
target: plugin
names:
  - python/references/api-pydantic.md
tags: [negative-space, error-text, scaffold]
cluster: "4.1"
still_applies: yes
status: Open
resolved_by: ""
---

# A model shared between two API packages generates Python that does not import it, and rbt generate reports success

**What happened.** Splitting one twelve-type `crm.v1` into six packages, nineteen models are needed by more than one package (generic errors such as `EmptyNameError` used by all six; the audit trail `HistoryEntry`/`HistoryRequest`/`HistoryResponse`; research results; provenance). Found, in order: (1) a package containing only models and no `API(...)` block generates nothing and the model appears nowhere, with no error or warning (give the package a state type and it generates); (2) `api-pydantic.md`'s "free-floating decls" example is about a Type not wired into `API(...)` and does not say a package needs a Type for its Models to be emitted; (3) with a state type, a second package referencing `common.v1.common.SpikeError` generates, the proto records the defining package, and the generated Python refers to it by dotted path but never imports it: `NameError: name 'common' is not defined` at `backend/api/probe/v1/probe_rbt.py:2582` in `SayAborted`. `rbt generate` exits 0 on output that cannot be imported. Workaround (measured 2026-09-25 on 1.6.0): each package owns a copy of each shared model, from one base; put shared field definitions in a plain module under `api/` with no `API(...)` block (it generates nothing) and have every package declare its own empty-body subclass. Measured with a throwaway two-package probe: generation succeeds, inherited fields keep their tags, both types record and read back at runtime, and TypeScript generation is correct. Limits: the copies are distinct types, so anything crossing a package is converted by value. Done 2026-09-25 as seven packages with 35 bases in `api/shared.py` plus seven per-package models that nest a shared one; six call sites needed a by-value conversion (`servicers/common.py`, `as_copy`), which mypy does not see through generated constructors. The rename (`crm.v1.Lead` to `leads.v1.Lead`) is an expunge and the data came back through `scripts/restore.py --migration package_split`.

**Expected.** Either the generated module imports the package it references, or `rbt generate` refuses and says which model crosses which boundary. Source fix list: (1) emit the import (recommended); (2) fail generation when a referenced model's package cannot be resolved; (3) say a package needs a `Type` in `api-pydantic.md` next to the free-floating-decls example, and say where shared models belong. Until then the split is possible only with the per-package-copy workaround, which costs a class per shared model per package and a conversion at every crossing.

**Repro.** Two packages under `api/`: `common/v1/common.py` declares a `Model` and any `Type`; `probe/v1/probe.py` imports that model and names it in `errors=[...]`; `rbt generate` succeeds; `import probe.v1.probe_rbt` raises `NameError`.

**Where in the skills.** `python/references/api-pydantic.md` (free-floating decls example, ~line 31).

**Checked at 1.6.0.** `api-pydantic.md` has no mention of multi-package APIs, shared models or that a package needs a Type (grep for `package` found only the free-floating example).
