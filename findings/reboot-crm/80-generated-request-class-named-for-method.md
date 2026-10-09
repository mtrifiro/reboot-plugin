---
id: reboot-crm-80
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P4.11"
reboot_version: 1.6.0
severity: green
target: plugin
names:
  - python/references/api-methods.md
  - python/references/patterns-common-gotchas.md
tags: [negative-space, error-text]
cluster: "4.1"
still_applies: no
status: Obsolete
resolved_by: ""
---

# A method's generated request class is named for the method, not the request model, and no reference says so

**What happened.** Declared `seed_backdated_history=Transaction(request=SeedBackdatedLeadHistoryRequest, ...)` on `Lead` and wrote the servicer signature as `request: Lead.SeedBackdatedLeadHistoryRequest`. The generated class is `Lead.SeedBackdatedHistoryRequest`, from the method name. `mypy` reports it undefined; the dev loop gives `AttributeError: type object 'Lead' has no attribute ...` with a correct "Did you mean". Hit twice in one afternoon. The `mcp-ui` skill's gotcha 19 said it for MCP apps; the `python` skill did not.

**Expected.** `api-methods.md` ("The Servicer Signature Each Declaration Obliges") to say in one line that the classes are `<Type>.<MethodPascalCase>Request` / `...Response` whatever the declared model is called.

**Repro.** Any method whose `request=` model is not named `<MethodPascalCase>Request`; write the servicer against the model's name; run `mypy`.

**Where in the skills.** `python/references/api-methods.md`.

**Checked at 1.6.0.** `python/references/api-methods.md` lines ~96-101 now state `<Type>.<Entry>Request` where `<Entry>` is the PascalCase form of the entry (method) name. Whether it says explicitly 'whatever the declared model is called' was not confirmed.
