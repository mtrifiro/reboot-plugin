---
id: reboot-crm-68
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P3.29"
reboot_version: 1.6.0
severity: yellow
target: plugin
names:
  - python/references/servicer-constructor.md
  - python/references/rpc-constructor-calls.md
tags: [contradiction, error-text, negative-space]
cluster: "4.1"
still_applies: yes
status: Open
resolved_by: ""
---

# A constructor called from a workflow on an actor that exists raises StateAlreadyConstructed

**What happened.** `servicer-constructor.md` says "A constructor method may also be invokable on an existing actor; branch on `context.constructor`". A workflow asking for many companies' logos called the factory writer `Logo.want(context, host, ...)` for each; for a logo asked for before, the call aborted `StateAlreadyConstructed` and the workflow retried forever. `rpc-constructor-calls.md` says `Service.create` is idempotent from the `initialize` hook, and the app had found the same for `Team.create` from a transaction; nothing says the constructor itself is not. Workaround: a factory `create` that only sets the id's fields, tried first with `StateAlreadyConstructed` caught, then an ordinary writer.

**Expected.** The reference saying a constructor is once-only outside `initialize`, or a get-or-create call.

**Repro.** Not recorded.

**Where in the skills.** `python/references/servicer-constructor.md` and `python/references/rpc-constructor-calls.md`.

**Checked at 1.6.0.** `servicer-constructor.md` line ~70 still says a constructor may be invokable on an existing actor; `rpc-constructor-calls.md` line ~63 says safe on every start from initialize only.
