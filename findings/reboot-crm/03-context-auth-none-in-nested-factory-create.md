---
id: reboot-crm-03
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P0.3"
reboot_version: 1.6.0
severity: yellow
target: plugin
names:
  - python/references/rpc-constructor-calls.md
  - python/references/servicer-constructor.md
tags: [auth, negative-space]
cluster: "4.1"
duplicate_of: cineloop-29
still_applies: yes
status: Resolved
resolved_by: "python/references/rpc-constructor-calls.md § Never; python/references/servicer-constructor.md § Never"
---

# context.auth is None inside a factory create reached from another actor's transaction

**What happened.** `Pipeline.add_account` (a transaction) reads `context.auth.user_id` to make the adder the owner, then calls `Account.create(context, ...)`. Inside that constructor `context.auth` is `None`, so an account's first `StageChange`, written there, cannot say who added it, while every later move, written in a transaction the teammate calls directly, can. Workaround: pass what the caller knows as a request field. The source marks this as the same defect as reboot-crm-02 seen first in a constructor.

**Expected.** Either the caller's identity carries into the nested constructor, or the `servicer-*.md` references say it does not. Source fix: same as reboot-crm-02; the constructor-specific half belongs in `rpc-constructor-calls.md` and `servicer-constructor.md` (a nested `create` runs app-internal, so anything it wants to stamp, such as owner or first history entry, must arrive as a request field). File as one bug with reboot-crm-02 but keep both repros.

**Repro.** Transaction reads `context.auth.user_id`, then calls a factory `create` on another actor; inspect `context.auth` inside the constructor.

**Where in the skills.** `python/references/rpc-constructor-calls.md`, `python/references/servicer-constructor.md`.

**Checked at 1.6.0.** Neither `rpc-constructor-calls.md` nor `servicer-constructor.md` mentions that a nested `create` runs app-internal (grep for `app_internal`/`nested` found nothing).
