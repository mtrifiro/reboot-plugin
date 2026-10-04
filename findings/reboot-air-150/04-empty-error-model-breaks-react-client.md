---
id: reboot-air-150-04
project: reboot-air-150
source: "reboot-air/reboot-findings.md §4"
reboot_version: 1.5.0
severity: unrated
target: framework
names:
  - python/references/api-errors.md
  - python/references/react-generated-client.md
tags: [negative-space, frontend, error-text]
cluster: "4.1"
still_applies: yes
status: Resolved
resolved_by: "python/references/react-generated-client.md § Errors you will see"
---

# An error Model with no fields crashes the generated React client at import

**What happened.** The app wrote `class CartEmpty(Model): pass`, listed in `errors=[CartEmpty, ...]` on `User.checkout`. `rbt generate` and the backend were fine and every backend test passed. `web/src/api/air/v1/air_rbt_types.ts` emitted `export const CartEmptySchema = z.object({});` with no `type: z.literal("CartEmpty")` discriminator, unlike every error model with fields. The React client builds `z.discriminatedUnion("type", [CartEmptySchema, ...])` at module top level, which throws `Invalid discriminated union option at index "0"`. Because it throws during module evaluation, the SPA renders a blank page with no console error in headless Chromium and no failed network request; it took a manual `import()` from devtools to see the stack. Workaround: give every error model at least one field (`reason: str = Field(tag=1, default="")`).

**Expected.** The codegen should emit the `type` literal for empty models too (or `rbt generate` should reject a field-less error model with a clear message).

**Repro.** Declare `class CartEmpty(Model): pass` and list it in `errors=[...]` on a method; run `rbt generate`; load the SPA.

**Where in the skills.** `python/references/api-errors.md` (error model guidance).

**Checked at 1.6.0.** No skill warns against field-less error models (grep for `empty`/`no fields` under `skills/` found nothing relevant).
