---
id: meridian-circuit-03
project: meridian-circuit
source: "v 1.4.1 Reboot/meridian-circuit/docs/2026.08.18 reboot-learnings porting supabase app.md §3"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/react-generated-client.md
  - python/references/patterns-react-state.md
tags: [error-text, frontend, negative-space]
cluster: ""
still_applies: yes
status: Resolved
resolved_by: "python/references/react-generated-client.md § Errors you will see"
---

# A wire-level idempotency key must be a UUID; a readable one fails as an opaque Unknown

**What happened.** Passing a readable key from the browser, `cart.checkout(request, { idempotencyKey: `lab-double-${Date.now()}` })`, fails at the server with `ValueError: badly formed hexadecimal UUID string`, surfaced to the client as an opaque `rbt.v1alpha1.Unknown`. Use `crypto.randomUUID()`. Backend-side `idempotently(alias=...)` takes a readable string; only the wire-level key must be a UUID.

**Expected.** Not recorded.

**Repro.** Call a generated mutator with a non-UUID `idempotencyKey`.

**Where in the skills.** `python/references/react-generated-client.md` (the `idempotencyKey?: string` option) and `patterns-react-state.md`.

**Checked at 1.6.0.** `react-generated-client.md` types the option as `idempotencyKey?: string` with no format; `patterns-react-state.md` mints it with `newId()` but never says it must be a UUID. Grep for `badly formed`/`uuid string` across `skills/` found nothing.

**Resolution (2026-10-10).** Rows in `react-generated-client.md` § Errors you will see: the UUID idempotency key; the second reader's hook throwing (1.4.0); int64 as `number`; a subscription on an unconstructed actor tearing the channel; the six-connection ceiling. The `#`-in-id trap already had its row; the `_rbt_web.ts` import failure is proto-era (1.4.0) and not carried.
