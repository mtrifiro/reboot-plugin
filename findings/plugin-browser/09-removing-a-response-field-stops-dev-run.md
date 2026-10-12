---
id: plugin-browser-09
project: plugin-browser
source: "plugin-browser/FINDINGS.md § Framework, item 1"
reboot_version: 1.6.0
severity: yellow
target: framework
names:
  - python/references/api-schema-evolution.md
  - python/references/errors.md
tags: [negative-space, error-text]
cluster: ""
duplicate_of: student-sor-16
still_applies: no
status: Resolved
resolved_by: "python/references/api-schema-evolution.md § Limits"
---
# Removing a field from a method's response is refused like a state change, and the running app goes down

**What happened.** Replacing `tested` and `next_steps` on `NextPlan`, a model used only as a reader's response and never stored, stopped the running `rbt dev run`: `Field \`tested\` was removed from Pydantic model \`plugin_browser.v1.plugin_browser.CatalogNextPlanResponse\`. Removing fields is a backwards-incompatible change. To continue, restore the field or use \`expunge\` ...`, then `waiting for modification, or hit \`x\` to expunge`. The app served nothing until the fields came back. The test harness, which starts fresh, passed throughout. (2026-10-12, the Next page.)

**Expected.** The skills to say that every model in the API, a response included, follows the schema-evolution rules: add fields, never remove or rename one, and retire one by leaving it empty.

**Repro.** With the app running, remove a field from a Reader's response model and save.

**Where in the skills.** `python/references/api-schema-evolution.md` speaks of state; `errors.md` has no row for "was removed from Pydantic model".

**Checked at import (2026-10-12).** Already documented before this build: `api-schema-evolution.md` § Check the change against the table lists "Delete a field (state, request or response model)" as refused, § Limits says a response-model field is rejected though it strands no data, and `errors.md` has a `was removed from Pydantic model` row (all since 2026-10-04). The build didn't read them before changing the response; the framework's side (refusing a change that strands no data) is student-sor-16.
