---
id: meridian-circuit-04
project: meridian-circuit
source: "v 1.4.1 Reboot/meridian-circuit/docs/2026.08.18 reboot-learnings porting supabase app.md §4"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/patterns-idempotency.md
  - python/references/servicer-workflow-calls.md
tags: [error-text, testing]
cluster: ""
still_applies: no
status: Resolved
resolved_by: "python/references/servicer-workflow-calls.md § Limits"
---

# An idempotency key is bound to its request bytes; reusing it with a different payload is refused

**What happened.** Reusing one key with a different payload is refused outright: `ValueError: Idempotency key for 'circuit.v1.CartMethods.Checkout' of state 'cart-…' is being reused _unsafely_; you can not reuse an idempotency key with a different request`. It caught a genuine bug in the app's own test, which sent `at_epoch_s=time.time()` on each of two 'duplicate' submits, so they were two different requests. A real retry resends byte-identical bytes; the protection will not let you paper over a non-deterministic field.

**Expected.** Not recorded.

**Repro.** Two submits under one idempotency key whose requests differ in a timestamp field.

**Where in the skills.** `python/references/patterns-idempotency.md`, `python/references/servicer-workflow-calls.md`.

**Checked at 1.6.0.** `servicer-workflow-calls.md` § Limits: 'Reusing an alias with a different request is refused ... requests under one alias must be replay-stable too'; the exact error text is in its § Errors you will see and in `errors.md`. Stated for workflow aliases; the client-key case follows the same rule but is not spelled out.
